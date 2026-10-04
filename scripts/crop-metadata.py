"""Compute reversible viewports; original images and the question bank stay unchanged.
Retain all PDF text/diagram geometry and all raster ink except verified repeated
page-edge decorations, isolated printed question numbers, and repeated separators
below all content. Ambiguous objects remain protected.
Requires Pillow, numpy and PyMuPDF (build-time only).
"""
import collections,json,math,statistics
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import pymupdf as pdf
APP=Path(__file__).resolve().parents[1];ROOT=APP.parent;SITE=APP/'site';BANK=ROOT/'question-bank'
def signature(d):
 r=pdf.Rect(d['rect']);return (round(r.x0,1),round(r.x1,1),round(r.height,1),tuple(round(c,2) for c in d.get('fill',())))
def geometry(page):
 paths=page.get_drawings(extended=True);counts=collections.Counter(signature(d) for d in paths if d['type']=='f' and d.get('fill'))
 eligible=set()
 for d in paths:
  if d['type']!='f' or not d.get('fill'):continue
  r=pdf.Rect(d['rect']);color=d['fill']
  if r.width<35 and 10<r.height<70 and (r.x1<55 or r.x0>page.rect.width-55) and max(color)-min(color)<.035 and .2<min(color)<.9 and counts[signature(d)]>=3:eligible.add(signature(d))
 # Recognize decorations only if matching repeated colors/heights exist on both margins.
 left={(s[2],s[3]) for s in eligible if s[1]<55};right={(s[2],s[3]) for s in eligible if s[0]>page.rect.width-55}
 eligible={s for s in eligible if (s[2],s[3]) in left&right}
 protected=[];decorations=[];clips=[];separators=[]
 line_counts=collections.Counter((round(d["rect"].x0,1),round(d["rect"].x1,1)) for d in paths if d["type"]=="s" and d["rect"].height<.01 and d["rect"].width>page.rect.width*.7)
 for d in paths:
  level=d['level'];clips=[c for c in clips if c[0]<level]
  if d['type']=='clip':clips.append((level,pdf.Rect(d['scissor'])));continue
  if d['type']=='group':continue
  r=pdf.Rect(d['rect']);pad=max(.7,(d.get('width') or 0)/2);r=pdf.Rect(r.x0-pad,r.y0-pad,r.x1+pad,r.y1+pad)
  for _,clip in clips:r &= clip
  if r.is_empty:continue
  if d['type']=='f' and d.get('fill') and signature(d) in eligible:decorations.append(r)
  elif d['type']=='s' and d['rect'].height<.01 and d['rect'].width>page.rect.width*.7 and line_counts[(round(d['rect'].x0,1),round(d['rect'].x1,1))]>=2:separators.append(r)
  else:protected.append(r)
 for block in page.get_text('dict')['blocks']:
  if block['type']==1:protected.append(pdf.Rect(block['bbox']))
  else:
   for line in block['lines']:
    for span in line['spans']:
     if span['text'].strip():protected.append(pdf.Rect(span['bbox']))
 return protected,decorations,separators

def viewport(asset,bbox,protected,decorations,separators,number_rect=None,tight=True):
 b=pdf.Rect(bbox)
 protected=list(protected);decorations=list(decorations)
 if number_rect is not None:
  protected=[r for r in protected if r!=number_rect]
  decorations.append(number_rect)
 relevant=[r&b for r in protected if not (r&b).is_empty]
 for r in separators:
  clipped=r&b
  if clipped.is_empty:continue
  # Only discard a repeated page separator below every content object.
  if relevant and clipped.y0>max(t.y1 for t in relevant)+2:decorations.append(r)
  else:protected.append(r)
 with Image.open(SITE/asset) as image:
  w,h=image.size;gray=np.asarray(image.convert('L'));mask=Image.new('1',(w,h));draw=ImageDraw.Draw(mask)
  for r in decorations:
   r=r&b
   if not r.is_empty:draw.rectangle((max(0,math.floor((r.x0-b.x0)/b.width*w)-2),max(0,math.floor((r.y0-b.y0)/b.height*h)-2),min(w-1,math.ceil((r.x1-b.x0)/b.width*w)+2),min(h-1,math.ceil((r.y1-b.y0)/b.height*h)+2)),fill=1)
  ink=(gray<250)&~np.asarray(mask,dtype=bool);columns=np.flatnonzero(ink.any(axis=0))
  if not len(columns):return {'size':[w,h],'box':[0,0,w,h]},False
  low=max(0,int(columns[0])-10);high=min(w,int(columns[-1])+11)
  touched=[]
  for r in protected:
   r=r&b
   if r.is_empty:continue
   touched.append(r);low=min(low,max(0,math.floor((r.x0-b.x0-4)/b.width*w)));high=max(high,min(w,math.ceil((r.x1-b.x0+4)/b.width*w)))
  low=max(0,low);high=min(w,high)
  rows=np.flatnonzero(ink.any(axis=1));top=max(0,int(rows[0])-10);bottom=min(h,int(rows[-1])+11)
  for r in touched:
   top=min(top,max(0,math.floor((r.y0-b.y0-4)/b.height*h)));bottom=max(bottom,min(h,math.ceil((r.y1-b.y0+4)/b.height*h)))
  # Keep short shared headings at their previous conservative scale.
  if not tight:
   low=min(low,int(w*.2));high=max(high,int(w*.8));top=0;bottom=h
  # Tiny reductions add rounding complexity without a visible benefit.
  if w/(high-low)<1.025:low=0;high=w
  assert high>low and not ink[:,:low].any() and not ink[:,high:].any(),asset
  for r in touched:
   assert low <= (r.x0-b.x0)/b.width*w+.01 and high >= (r.x1-b.x0)/b.width*w-.01,asset
   assert top <= (r.y0-b.y0)/b.height*h+.01 and bottom >= (r.y1-b.y0)/b.height*h-.01,asset
  assert not ink[:top].any() and not ink[bottom:].any(),asset
  return {'size':[w,h],'box':[low,top,high,bottom]},high-low<w or bottom-top<h

def main():
 questions=json.loads((BANK/'public-questions.json').read_text());by_exam=collections.defaultdict(list)
 for q in questions:by_exam[q['id'][:10]].append(q)
 result={};gains=[];question_assets=set();page_count=0
 for exam,qs in by_exam.items():
  batch=json.loads((SITE/f'data/exams/{exam}.json').read_text());regions={}
  for q in qs:
   for r in q['regions']:regions[r['asset']]={**r,'number':q['original_number'] if r is q['regions'][0] else None};question_assets.add(r['asset'])
  for c in batch['contexts'].values():
   for source,image in zip(c['regions'],c.get('images',[])):regions[image['asset']]=source
  pages=collections.defaultdict(list)
  for asset,r in regions.items():pages[r['page']].append((asset,r))
  with pdf.open(ROOT/qs[0]['source']) as doc:
   for number,items in pages.items():
    page=doc[number-1];protected,decorations,separators=geometry(page);page_count+=1
    for asset,r in items:
     number_rect=None
     if r.get('number') is not None:
      b=pdf.Rect(r['bbox']);candidates=[]
      for block in page.get_text('dict')['blocks']:
       for line in block.get('lines',[]):
        for span in line['spans']:
         rect=pdf.Rect(span['bbox']);text=span['text'].strip()
         if text in (f".{r['number']}",f"{r['number']}.") and b.y0<=rect.y0<=b.y0+20 and rect.x0>page.rect.width*.8 and span['flags']&16:candidates.append(rect)
      if len(candidates)==1:
       candidate=candidates[0];padded=pdf.Rect(candidate.x0-3,candidate.y0-2,candidate.x1+3,candidate.y1+2)
       if not any(t!=candidate and not (t&padded).is_empty for t in protected):number_rect=candidate
     meta,trimmed=viewport(asset,r['bbox'],protected,decorations,separators,number_rect,asset in question_assets);result[asset]=meta
     if trimmed:gains.append(meta['size'][0]/(meta['box'][2]-meta['box'][0])-1)
  print(f'{exam}: checked {len(regions)} image viewports',flush=True)
 (SITE/'data/image-crops.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
 report={'images_verified':len(result),'question_images_verified':len(question_assets),'source_pages_checked':page_count,'images_trimmed':len(gains),'median_trim_gain_percent':round(statistics.median(gains)*100,1) if gains else 0,'maximum_trim_gain_percent':round(max(gains)*100,1) if gains else 0,'original_images_modified':False,'all_text_diagram_geometry_retained_except_identified_question_numbers':True,'all_content_pixels_retained':True}
 (APP/'reports/crop-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
