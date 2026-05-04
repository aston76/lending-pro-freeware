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
import webview
import logger  # persistent error logger
from database import init_database, load_active_profile
from api import Api
from backup import backup_local

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
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", port), Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{port}/index.html?startup={int(time.time())}"
    except Exception as e:
        print(f"Server start failed on {port}: {e}")
        return os.path.join(web_dir, 'index.html')


def get_web_dir():
    """Get the path to the web directory, handling both dev and packaged modes."""
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'web')


def on_closing():
    """
    Called when the user closes the main window.
    Performs an auto-backup (non-blocking) before allowing the window to close.
    """
    try:
        backup_local()
    except Exception as e:
        logger.error("[Backup on close] Warning: %s", e, exc_info=True)


def main():
    logger.log_startup()
    load_active_profile()  # Restore last active profile
    init_database()
    logger.info("Database initialized successfully.")

    api = Api()
    web_dir = get_web_dir()
    
    # Start the local server
    app_url = start_local_server(web_dir, port=34001)

    window = webview.create_window(
        'PH-Lending Pro',
        url=app_url,
        js_api=api,
        width=1440,
        height=900,
        min_size=(900, 600),
        text_select=True,
        background_color='#0f172a'
    )

    # Pass window ref to api so it can trigger close from JS
    api._window = window

    webview.settings['ALLOW_FILE_URLS'] = True

    # Note: Using http_server=True causes local server pathing issues in macOS pywebview.
    # To fix camera access with file:// protocol, WKWebView policies must be adjusted.
    # Mac permissions are requested in Info.plist (already handled by create_app_launcher.py)
    
    webview.start(
        debug=('--debug' in sys.argv),
        private_mode=False
    )
    logger.log_shutdown()

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
