from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(Path(__file__).resolve().parents[1]/'site'),**kwargs)
 def translate_path(self,path):return super().translate_path(path.removeprefix('/psychometric-trainer'))
ThreadingHTTPServer(('127.0.0.1',8788),Handler).serve_forever()
