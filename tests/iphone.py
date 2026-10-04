"""W3C Safari WebDriver test on an actual iOS simulator, not mobile emulation."""
import json,urllib.request,urllib.error,time,base64,pathlib,os
APP=pathlib.Path(__file__).resolve().parents[1];saved=json.load(open('/tmp/psycho-safari-session.json'))['value'];sid=saved['sessionId'];root='http://127.0.0.1:5150/session/'+sid;url=os.environ.get('APP_URL','http://127.0.0.1:8787/')
def call(path,data=None,method=None):
 req=urllib.request.Request(root+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'},method=method or ('POST' if data is not None else 'GET'))
 try:return json.load(urllib.request.urlopen(req,timeout=60))['value']
 except urllib.error.HTTPError as e:raise RuntimeError(e.read().decode())
def js(script):return call('/execute/sync',{'script':script,'args':[]})
def wait(script):
 deadline=time.time()+40
 while time.time()<deadline:
  if js(script):return
  time.sleep(.25)
 raise RuntimeError('Timed out: '+script)
def click(selector):
 el=call('/element',{'using':'css selector','value':selector});eid=el['element-6066-11e4-a52e-4f735466cecf'];call('/element/'+eid+'/click',{})
def ready():
 wait("return document.querySelector('#answers') && !document.querySelector('#answers').disabled")
 wait("return [...document.querySelectorAll('#questionBody > .picture-button img')].every(i=>i.complete && i.naturalWidth>0)")
 time.sleep(.4)
def identify():return js("return decodeURI(document.querySelector('#questionBody > .picture-button img').src).match(/(he-\\d{4}-\\d{2}-(?:quantitative|verbal|english)-\\d-q\\d+)-\\d.webp/)[1]")
keys={k['question_id']:int(k['correct_choice_id'].rsplit('-c',1)[1]) for k in json.loads((APP.parent/'question-bank/private-answer-keys.json').read_text())}
call('/url',{'url':url});ready();js("localStorage.removeItem('psycho-training:v1:'+new URL('./',location.href).pathname)");call('/refresh',{});ready();qid=identify();assert 'quantitative' in qid
assert js('return document.documentElement.scrollWidth <= innerWidth')
# Click the visible label instead of the deliberately visually hidden radio.
click(f'.answer-grid label:has(input[value="{keys[qid]}"])');click('#checkButton');wait("return !document.querySelector('#feedback').hidden");assert 'נכון!' in js("return document.querySelector('#feedback').textContent")
call('/refresh',{});ready();assert identify()!=qid
for button,subject in [('languageMode','verbal'),('englishMode','english')]:
 click('#'+button);ready();assert subject in identify()
qid=identify();wrong=keys[qid]%4+1;click(f'.answer-grid label:has(input[value="{wrong}"])');click('#checkButton');wait("return !document.querySelector('#feedback').hidden");assert 'נשארת' in js("return document.querySelector('#feedback').textContent")
click('#nextButton');ready();click('#questionBody > .picture-button');assert js("return document.querySelector('#zoomDialog').open")
js("document.querySelector('#zoomRange').value=200;document.querySelector('#zoomRange').dispatchEvent(new Event('input'))");assert js("return document.querySelector('#zoomImage').style.width==='200%'")
(APP/'reports/iphone-zoom.png').write_bytes(base64.b64decode(call('/screenshot')));click('#closeZoom');click('#settingsButton');assert js("return document.querySelector('#settingsDialog').open");click('#resetButton');click('#cancelReset');assert js("return document.querySelector('#resetConfirm').hidden");click('#closeSettings')
assert js("return document.documentElement.scrollWidth<=innerWidth")
(APP/'reports/iphone.png').write_bytes(base64.b64decode(call('/screenshot')))
report={'url':url,'passed':True,'device':saved['capabilities'],'checks':['touch answer selection','correct grading','saved retirement after reload','three subjects','incorrect grading','image zoom','settings/reset cancellation','no horizontal overflow']}
(APP/'reports'/('iphone-deployed.json' if 'github.io' in url else 'iphone-local.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
