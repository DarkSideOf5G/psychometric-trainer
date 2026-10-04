"""Compute reversible viewports; original images and the question bank stay unchanged.
Retain all PDF text/diagram geometry and all raster ink except verified repeated
page-edge decorations. Ambiguous images keep their original viewport.
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
 protected=[];decorations=[];clips=[]
 for d in paths:
  level=d['level'];clips=[c for c in clips if c[0]<level]
  if d['type']=='clip':clips.append((level,pdf.Rect(d['scissor'])));continue
  if d['type']=='group':continue
  r=pdf.Rect(d['rect']);pad=max(.7,(d.get('width') or 0)/2);r=pdf.Rect(r.x0-pad,r.y0-pad,r.x1+pad,r.y1+pad)
  for _,clip in clips:r &= clip
  if r.is_empty:continue
  if d['type']=='f' and d.get('fill') and signature(d) in eligible:decorations.append(r)
  else:protected.append(r)
 for block in page.get_text('dict')['blocks']:
  if block['type']==1:protected.append(pdf.Rect(block['bbox']))
  else:
   for line in block['lines']:
    for span in line['spans']:protected.append(pdf.Rect(span['bbox']))
 return protected,decorations

def viewport(asset,bbox,protected,decorations):
 b=pdf.Rect(bbox)
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
  low=min(low,int(w*.2));high=max(high,int(w*.8));low=max(0,low);high=min(w,high)
  # Tiny reductions add rounding complexity without a visible benefit.
  if w/(high-low)<1.025:low=0;high=w
  assert high>low and not ink[:,:low].any() and not ink[:,high:].any(),asset
  for r in touched:
   assert low <= (r.x0-b.x0)/b.width*w+.01 and high >= (r.x1-b.x0)/b.width*w-.01,asset
  return {'size':[w,h],'box':[low,0,high,h]},high-low<w

def main():
 questions=json.loads((BANK/'public-questions.json').read_text());by_exam=collections.defaultdict(list)
 for q in questions:by_exam[q['id'][:10]].append(q)
 result={};gains=[];question_assets=set();page_count=0
 for exam,qs in by_exam.items():
  batch=json.loads((SITE/f'data/exams/{exam}.json').read_text());regions={}
  for q in qs:
   for r in q['regions']:regions[r['asset']]=r;question_assets.add(r['asset'])
  for c in batch['contexts'].values():
   for source,image in zip(c['regions'],c.get('images',[])):regions[image['asset']]=source
  pages=collections.defaultdict(list)
  for asset,r in regions.items():pages[r['page']].append((asset,r))
  with pdf.open(ROOT/qs[0]['source']) as doc:
   for number,items in pages.items():
    protected,decorations=geometry(doc[number-1]);page_count+=1
    for asset,r in items:
     meta,trimmed=viewport(asset,r['bbox'],protected,decorations);result[asset]=meta
     if trimmed:gains.append(meta['size'][0]/(meta['box'][2]-meta['box'][0])-1)
  print(f'{exam}: checked {len(regions)} image viewports',flush=True)
 (SITE/'data/image-crops.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
 report={'images_verified':len(result),'question_images_verified':len(question_assets),'source_pages_checked':page_count,'images_trimmed':len(gains),'median_trim_gain_percent':round(statistics.median(gains)*100,1) if gains else 0,'maximum_trim_gain_percent':round(max(gains)*100,1) if gains else 0,'original_images_modified':False,'all_text_diagram_geometry_retained':True,'all_non_decoration_pixels_retained':True}
 (APP/'reports/crop-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
