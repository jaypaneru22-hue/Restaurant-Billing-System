"""High-performance multi-threaded HTTP server hosting the RestoPro REST API and Customer Web Portal."""
import os
import sys
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Optional

from api.rest_handler import rest_api_handler
from utils.logger import logger

STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Spawns an independent thread per connection for true multi-device concurrency."""
    daemon_threads = True
    allow_reuse_address = True


class RestoProHTTPRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for REST API endpoints and static mobile web portal files."""

    server_version = "RestoPro-API/2.0"

    def do_OPTIONS(self):
        self._dispatch_api()

    def do_GET(self):
        if self.path.startswith("/api/") or self.path == "/api":
            self._dispatch_api()
        else:
            self._serve_static_or_spa()

    def do_POST(self):
        if self.path.startswith("/api/") or self.path == "/api":
            self._dispatch_api()
        else:
            self.send_error(405, "Method Not Allowed")

    def do_PUT(self):
        if self.path.startswith("/api/") or self.path == "/api":
            self._dispatch_api()
        else:
            self.send_error(405, "Method Not Allowed")

    def do_DELETE(self):
        if self.path.startswith("/api/") or self.path == "/api":
            self._dispatch_api()
        else:
            self.send_error(405, "Method Not Allowed")

    def _dispatch_api(self):
        """Reads payload and passes request to RestAPIHandler."""
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""

        # Normalize headers to lowercase dictionary
        headers_dict = {k.lower(): v for k, v in self.headers.items()}

        status_code, response_headers, body = rest_api_handler.handle_request(
            method=self.command,
            path=self.path,
            headers=headers_dict,
            body_bytes=body_bytes,
            client_address=self.client_address
        )

        self.send_response(status_code)
        for h_name, h_val in response_headers.items():
            self.send_header(h_name, h_val)
        self.end_headers()

        if body:
            self.wfile.write(body)

    def _serve_static_or_spa(self):
        """Serves mobile web portal assets (HTML, CSS, JS, images) or falls back to portal.html."""
        clean_path = self.path.split("?")[0].strip("/")
        if not clean_path or clean_path in ("portal", "menu", "track", "cart", "login", "register"):
            target_file = STATIC_DIR / "portal.html"
        else:
            target_file = (STATIC_DIR / clean_path).resolve()
            # Prevent path traversal
            if not str(target_file).startswith(str(STATIC_DIR.resolve())):
                self.send_error(403, "Access Forbidden")
                return

        if not target_file.exists() or not target_file.is_file():
            # Fall back to portal.html for client-side routing
            target_file = STATIC_DIR / "portal.html"

        if not target_file.exists():
            self.send_error(404, "Portal Web Page Not Found")
            return

        mime_type, _ = mimetypes.guess_type(str(target_file))
        mime_type = mime_type or "application/octet-stream"
        if "text" in mime_type or "javascript" in mime_type or "json" in mime_type:
            mime_type += "; charset=utf-8"

        try:
            with open(target_file, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            logger.error(f"Error serving static file {target_file}: {e}")
            self.send_error(500, "Internal Server Error")

    def log_message(self, format, *args):
        """Silences verbose request logging except in debug mode."""
        pass


def run_http_server(host: str = "0.0.0.0", port: int = 8080) -> ThreadedHTTPServer:
    """Creates and starts the multi-threaded HTTP server instance."""
    server_address = (host, port)
    httpd = ThreadedHTTPServer(server_address, RestoProHTTPRequestHandler)
    logger.info(f"RestoPro Multi-User HTTP Server started at http://{host}:{port}/")
    return httpd
