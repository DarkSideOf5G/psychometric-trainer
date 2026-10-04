#!/usr/bin/env python3
"""Package only verified student content into a GitHub Pages static site."""
import collections,gzip,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];APP=ROOT/'training-app';BANK=ROOT/'question-bank';SITE=APP/'site'
def save(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def main():
 questions=json.loads((BANK/'public-questions.json').read_text());keys={k['question_id']:k for k in json.loads((BANK/'private-answer-keys.json').read_text())};allowed=set(json.loads((BANK/'public-assets-manifest.json').read_text())['assets']);manifest=json.loads((ROOT/'download-manifest.json').read_text());sources={s['file']:s for s in manifest['files'] if 'file' in s};exams=collections.defaultdict(lambda:{'questions':{},'contexts':{}});assets=set();catalog=[]
 SITE.mkdir(exist_ok=True)
 for f in (APP/'src').iterdir():
  if f.is_file():shutil.copyfile(f,SITE/f.name)
 dims={}
 for q in questions:
  exam=q['id'][:10];subject=q['section_id'].split('-')[-2];mode='math' if subject=='quantitative' else 'language';key=keys[q['id']];label=int(key['correct_choice_id'].rsplit('-c',1)[1]);salt=digest('psycho-training-v1:'+q['id']+':'+q['source_sha256'])[:24];check=digest(f"{q['id']}:{label}:{salt}")
  catalog.append({'id':q['id'],'exam':exam,'mode':mode,'subject':subject})
  # No native question text, correct IDs, or answer-key images are published.
  record={'id':q['id'],'subject':subject,'number':q['original_number'],'ordinal':int(q['section_id'].rsplit('-',1)[1]),'regions':q['regions'],'contexts':[c['id'] for c in q['contexts']],'choiceContext':q.get('choice_context_id'),'kind':q['question_type'],'salt':salt,'check':check,'sourceUrl':sources[q['source']]['url']}
  exams[exam]['questions'][q['id']]=record
  for r in q['regions']:assets.add(r['asset'])
  for c in q['contexts']:
   if c['kind']=='complete_section_fallback':
    for r in c['regions']:dims[(exam,r['page'])]=(r['bbox'][2],r['bbox'][3])
   for r in c['regions']:assets.add(r['asset'])
   exams[exam]['contexts'].setdefault(c['id'],{'id':c['id'],'kind':c['kind'],'regions':c['regions']})
 if not assets.issubset(allowed):raise ValueError('Non-public asset requested')
 for asset in sorted(assets):
  dst=SITE/asset;dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists() or dst.stat().st_size!=(BANK/asset).stat().st_size:shutil.copyfile(BANK/asset,dst)
 for exam,batch in exams.items():
  for c in batch['contexts'].values():
   if c['kind']=='complete_section_fallback':continue
   images=[]
   for j,r in enumerate(c['regions']):
    with Image.open(BANK/r['asset']) as original:
     w,h=dims[(exam,r['page'])];b=r['bbox'];box=(max(0,int(b[0]/w*original.width)),max(0,int(b[1]/h*original.height)),min(original.width,int(b[2]/w*original.width)),min(original.height,int(b[3]/h*original.height)));crop=original.crop(box)
     if crop.width<1 or crop.height<1:raise ValueError('Empty context '+c['id'])
     asset=f'context-assets/{exam}/{c["id"]}-{j}.webp';dst=SITE/asset;dst.parent.mkdir(parents=True,exist_ok=True);crop.save(dst,format='WEBP',lossless=True,method=4);images.append({'asset':asset,'page':r['page'],'height':b[3]-b[1]})
   c['images']=images
  save(SITE/f'data/exams/{exam}.json',batch)
 counts=dict(collections.Counter(q['subject'] for q in catalog));version=digest(json.dumps([(q['id'],keys[q['id']]['key_version']) for q in questions]))[:16];save(SITE/'data/catalog.json',{'version':version,'questions':catalog,'counts':counts});(SITE/'.nojekyll').touch();summary={'questions':len(catalog),'subjects':counts,'public_source_images':len(assets),'exam_shards':len(exams),'site_bytes':sum(p.stat().st_size for p in SITE.rglob('*') if p.is_file()),'answer_checks':'SHA-256 per choice; original answer-key files are not published','version':version};save(APP/'reports/build.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':
 main()
 subprocess.run([sys.executable,str(APP/'scripts/crop-metadata.py')],check=True)
