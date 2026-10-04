"""W3C Safari WebDriver test on an actual iOS simulator, not mobile emulation."""
import json,urllib.request,urllib.error,time,base64,pathlib,os,queue,threading,subprocess
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
commands=queue.Queue();tapped=threading.Event();scripts=queue.Queue();results=queue.Queue()
class Bridge(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path=="/script":
   try:body={"script":scripts.get(timeout=.3)}
   except queue.Empty:body={}
  elif self.path=="/next":
   try:body=commands.get(timeout=.5)
   except queue.Empty:body={}
  else:tapped.set();body={}
  data=json.dumps(body).encode();self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(data)
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers["Content-Length"])));results.put(body.get("value"));self.send_response(200);self.end_headers()
 def log_message(self,*args):pass
if os.environ.get("NATIVE_TAPS"):
 threading.Thread(target=ThreadingHTTPServer(("127.0.0.1",5151),Bridge).serve_forever,daemon=True).start()
APP=pathlib.Path(__file__).resolve().parents[1]
url=os.environ.get('APP_URL','http://127.0.0.1:8787/')
if os.environ.get('NATIVE_TAPS'):
 udid=os.environ.get('SIMULATOR_UDID','3BBC1F5A-396B-4234-A4FF-445CAB30E516')
 devices=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','--json']))['devices']
 runtime,device=next((runtime,d) for runtime,items in devices.items() for d in items if d['udid']==udid)
 saved={'capabilities':{'deviceName':device['name'],'platformVersion':runtime.rsplit('iOS-',1)[1].replace('-','.'),'platformName':'iOS','browserName':'WKWebView (native XCTest host)','deviceUDID':udid}}
 root=''
else:
 saved=json.load(open('/tmp/psycho-safari-session.json'))['value'];root='http://127.0.0.1:5150/session/'+saved['sessionId']

def call(path,data=None,method=None):
 if os.environ.get('NATIVE_TAPS'):
  if path=='/execute/sync':code='(function(){'+data['script']+'})()'
  elif path=='/url':code='location.href='+json.dumps(data['url'])
  elif path=='/refresh':code='location.reload()'
  elif path=='/screenshot':code='__screenshot__'
  else:raise RuntimeError('Unsupported native command '+path)
  scripts.put(code);return results.get(timeout=120)
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
 if os.environ.get('NATIVE_TAPS'):
  js("document.querySelector("+json.dumps(selector)+").scrollIntoView({block:'center',behavior:'instant'})")
  time.sleep(.5)
  rect=js("const r=document.querySelector("+json.dumps(selector)+").getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}")
  tapped.clear();commands.put(rect)
  if not tapped.wait(30):raise RuntimeError('Native touch driver did not respond')
  time.sleep(.25)
 else:
  el=call('/element',{'using':'css selector','value':selector});eid=el['element-6066-11e4-a52e-4f735466cecf'];call('/element/'+eid+'/click',{})
def ready():
 wait("return document.querySelector('#answers') && !document.querySelector('#answers').disabled")
 wait("return [...document.querySelectorAll('#questionBody > .picture-button img')].every(i=>i.complete && i.naturalWidth>0)")
 time.sleep(.4)
def identify():return js("return decodeURI(document.querySelector('#questionBody > .picture-button img').src).match(/(he-\\d{4}-\\d{2}-(?:quantitative|verbal|english)-\\d-q\\d+)-\\d.webp/)[1]")
keys={k['question_id']:int(k['correct_choice_id'].rsplit('-c',1)[1]) for k in json.loads((APP.parent/'question-bank/private-answer-keys.json').read_text())}
call('/url',{'url':url});ready();assert js('return location.href').startswith(url), 'Wrong site loaded';js("localStorage.removeItem('psycho-training:v1:'+new URL('./',location.href).pathname)");js('window.__testBeforeRefresh=true');call('/refresh',{});wait('return !window.__testBeforeRefresh');ready();qid=identify();assert 'quantitative' in qid
assert js('return document.documentElement.scrollWidth <= innerWidth')
# Enlarge and pan the question without zooming/overflowing the surrounding page.
click('#questionBody > .image-controls [data-zoom="in"]');click('#questionBody > .image-controls [data-zoom="in"]')
assert js("return document.querySelector('#questionBody > .image-controls output').textContent==='150%'")
assert js("return document.documentElement.scrollWidth<=innerWidth")
if os.environ.get('NATIVE_TAPS'):
 js("document.querySelector('#questionBody > .picture-button .picture-scroll').scrollIntoView({block:'center',behavior:'instant'})")
 time.sleep(.5)
 before=js("return document.querySelector('#questionBody > .picture-button .picture-scroll').scrollLeft")
 gesture=js("const r=document.querySelector('#questionBody > .picture-button .picture-scroll').getBoundingClientRect();const y=(Math.max(r.top,20)+Math.min(r.bottom,innerHeight-20))/2;return {x:r.left+r.width*.25,y,endX:r.left+r.width*.75,endY:y}")
 tapped.clear();commands.put(gesture);assert tapped.wait(30);time.sleep(.5)
 after=js("return document.querySelector('#questionBody > .picture-button .picture-scroll').scrollLeft")
 assert before>after, (before,after)
 assert js("return !document.querySelector('#zoomDialog').open")
click('#questionBody > .image-controls [data-zoom="fit"]')
assert js("return document.querySelector('#questionBody > .image-controls output').textContent==='100%'")
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
report={'url':url,'passed':True,'device':({**saved['capabilities'],'browserName':'WKWebView (native XCTest host)'} if os.environ.get('NATIVE_TAPS') else saved['capabilities']),'checks':['inline zoom and fit','native horizontal image pan','touch answer selection','correct grading','saved retirement after reload','three subjects','incorrect grading','image zoom','settings/reset cancellation','no horizontal overflow'],'touch_driver':'XCTest' if os.environ.get('NATIVE_TAPS') else 'WebDriver'}
(APP/'reports'/('iphone-deployed.json' if 'github.io' in url else 'iphone-local.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if os.environ.get("NATIVE_TAPS"):commands.put({"stop":True});time.sleep(1)
