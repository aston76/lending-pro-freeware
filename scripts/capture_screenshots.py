#!/usr/bin/env python3
"""
Serves the Lending Pro web frontend with an injected pywebview bridge
so browser automation can capture pixel-perfect screenshots with real
demo data, without launching the native pywebview window.

Usage:
    PH_LENDING_DEMO_ONLY=1 python3 scripts/capture_screenshots.py
Then connect Playwright to http://127.0.0.1:34099/index.html
"""

import http.server
import json
import os
import socketserver
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = str(ROOT / "web")

os.environ.setdefault("PH_LENDING_DEMO_ONLY", "1")
sys.path.insert(0, str(ROOT))

from api import Api  # noqa: E402
import demo_generator  # noqa: E402


def _init_api():
    api = Api()
    import database
    database.set_demo_mode(True)
    database.init_database()
    conn = database.get_connection()
    count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    conn.close()
    if count == 0:
        demo_generator.generate_demo_data()
        demo_generator._enhance_with_v14_features()
    api._is_demo = True
    return api


API = _init_api()

POLYFILL = b"""
<script>
(function() {
  window.pywebview = {
    api: new Proxy({}, {
      get: function(_target, method) {
        return function() {
          var args = Array.prototype.slice.call(arguments);
          return fetch('/__api__', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ method: method, args: args })
          }).then(function(r) { return r.json(); });
        };
      }
    })
  };
  window.addEventListener('load', function() {
    setTimeout(function() {
      window.dispatchEvent(new Event('pywebviewready'));
    }, 60);
  });
})();
</script>
"""


class CaptureHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, *_args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html") or self.path.startswith("/index.html?"):
            html_path = os.path.join(WEB_DIR, "index.html")
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            html = html.replace("<head>", "<head>" + POLYFILL.decode(), 1)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/__api__":
            self.send_error(404)
            return
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            method_name = data.get("method", "")
            args = data.get("args", [])

            if method_name.startswith("_"):
                raise ValueError("Private methods are not exposed.")

            fn = getattr(API, method_name, None)
            if fn is None or not callable(fn):
                raise ValueError("Unknown API method: " + method_name)

            result = fn(*args)
            payload = json.dumps(result, default=str, ensure_ascii=False)
        except Exception as exc:
            traceback.print_exc()
            payload = json.dumps(
                {"success": False, "error": str(exc)},
                ensure_ascii=False,
            )

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(payload.encode("utf-8"))


def _count(table):
    import database
    conn = database.get_connection()
    n = conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
    conn.close()
    return n


def main():
    port = 34099
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), CaptureHandler)
    print("Capture server ready: http://127.0.0.1:" + str(port) + "/index.html")
    print("Demo clients:", _count("clients"), "Loans:", _count("loans"))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
