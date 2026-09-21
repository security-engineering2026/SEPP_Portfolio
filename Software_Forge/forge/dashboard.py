from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from .engine import ForgeEngine
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        e=ForgeEngine(Path.cwd()); body=json.dumps({"product":"Software Forge","status":"RUNNING","health":e.health()},indent=2).encode(); self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass
def serve(host="127.0.0.1",port=8765): ThreadingHTTPServer((host,port),Handler).serve_forever()
