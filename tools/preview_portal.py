"""Preview the portal under the same project prefix used by GitHub Pages."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from functools import partial
from pathlib import Path
import argparse,json,os

ROOT=Path(__file__).resolve().parents[1];PREFIX='/relational-graph-stylometry'
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        if not path.startswith(PREFIX+'/'):return str(ROOT/'site'/'__unknown_route__')
        return super().translate_path(path[len(PREFIX):])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8875);args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(ROOT/'site')))
    state=ROOT/'.preview';state.mkdir(exist_ok=True)
    (state/'server.json').write_text(json.dumps({'pid':os.getpid(),'url':'http://127.0.0.1:'+str(args.port)+PREFIX+'/','root':str(ROOT/'site')})+'\n',encoding='utf-8')
    print('PREVIEW_URL=http://127.0.0.1:'+str(args.port)+PREFIX+'/',flush=True)
    server.serve_forever()
