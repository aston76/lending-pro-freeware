"""
PH-Lending Pro — Application Entry Point
Launches the pywebview desktop window with the API backend.
On close: auto-backup then clean shutdown.
"""

import os
import sys
import threading
import socketserver
import http.server
import time
from pathlib import Path
import webview
import logger  # persistent error logger
from app_config import APP_NAME
from api import Api

# Force UTF-8 on Windows console to avoid charmap/encoding errors (e.g. Peso symbol ₱)
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

def start_local_server(web_dir, port=34001):
    """Starts a local HTTP server serving the web directory. No-cache headers force WKWebView to reload fresh files."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=web_dir, **kwargs)

        def log_message(self, format, *args):
            pass  # Suppress logs

        def end_headers(self):
            # Force no-cache so WKWebView always loads fresh CSS/JS
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            super().end_headers()

    socketserver.TCPServer.allow_reuse_address = True
    last_error = None
    for candidate_port in (port, 0):
        try:
            httpd = socketserver.TCPServer(("127.0.0.1", candidate_port), Handler)
            actual_port = int(httpd.server_address[1])
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            url = f"http://127.0.0.1:{actual_port}/index.html?startup={int(time.time())}"
            return url, httpd
        except OSError as e:
            last_error = e
    logger.warning("Local web server unavailable; using file fallback: %s", last_error)
    return Path(web_dir, "index.html").resolve().as_uri(), None


def get_web_dir():
    """Get the path to the web directory, handling both dev and packaged modes."""
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'web')


def main():
    logger.log_startup()
    api = Api()
    logger.info("Database initialized successfully.")
    web_dir = get_web_dir()

    app_url, server = start_local_server(web_dir, port=34001)
    api._server = server

    window = webview.create_window(
        APP_NAME,
        url=app_url,
        js_api=api,
        width=1440,
        height=900,
        min_size=(900, 600),
        text_select=True,
        background_color='#101419'
    )

    # Pass window ref to api so it can trigger close from JS
    api._window = window

    def handle_native_close(*_):
        api.shutdown_services(force_backup=True)

    window.events.closing += handle_native_close

    webview.settings['ALLOW_FILE_URLS'] = True

    # Note: Using http_server=True causes local server pathing issues in macOS pywebview.
    # To fix camera access with file:// protocol, WKWebView policies must be adjusted.
    # Mac permissions are requested in Info.plist (already handled by create_app_launcher.py)
    
    webview.start(
        debug=('--debug' in sys.argv),
        private_mode=False
    )
    api.shutdown_services(force_backup=False)
    logger.log_shutdown()

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
