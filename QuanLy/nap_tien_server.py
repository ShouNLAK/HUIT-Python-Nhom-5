import json
import socket
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Optional
from urllib.parse import parse_qs, urlparse


class NapTienWebhookServer:
    """HTTP server nhận tín hiệu khi mã QR được quét."""

    def __init__(self, manager, host: str = "0.0.0.0", port: int = 5050, public_base_url: Optional[str] = None) -> None:
        self.manager = manager
        self.host = host
        self.port = port
        self.httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.running = False
        self.public_base_url = public_base_url or self._build_default_public_url()

    def _build_default_public_url(self) -> str:
        candidate = self._detect_ipv4()
        return f"http://{candidate}:{self.port}"

    def _detect_ipv4(self) -> str:
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            probe.connect(("8.8.8.8", 80))
            ip = probe.getsockname()[0]
            probe.close()
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            parts = ip.split(".")
            if len(parts) == 4 and not ip.startswith("127."):
                return ip
        except Exception:
            pass
        return "127.0.0.1"

    def start(self) -> bool:
        with self._lock:
            if self.running:
                return True
            try:
                handler = self._build_handler()
                self.httpd = ThreadingHTTPServer((self.host, self.port), handler)
                self.running = True
            except Exception:
                self.running = False
                self.httpd = None
                raise
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        with self._lock:
            if not self.running:
                return
            if self.httpd:
                try:
                    self.httpd.shutdown()
                    self.httpd.server_close()
                except Exception:
                    pass
            self.running = False
            self.httpd = None

    def _build_handler(self):
        server = self

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # type: ignore[override]
                server._handle(self)

            def do_POST(self):  # type: ignore[override]
                server._handle(self)

            def log_message(self, format, *args):  # noqa: A003
                return

        return _Handler

    def _handle(self, handler: BaseHTTPRequestHandler) -> None:
        parsed = urlparse(handler.path)
        if parsed.path == "/health":
            self._send_json(handler, 200, {"status": "ok"})
            return
        if parsed.path != "/nap-tien":
            self._send_json(handler, 404, {"error": "Not found"})
            return
        params = parse_qs(parsed.query)
        code = params.get("code", params.get("request"))
        token = params.get("token")
        if handler.command == "POST":
            content_length = int(handler.headers.get("Content-Length", 0) or 0)
            if content_length:
                try:
                    body = handler.rfile.read(content_length)
                    payload = json.loads(body.decode("utf-8"))
                    code = [payload.get("code") or payload.get("request")]
                    token = [payload.get("token")]
                except Exception:
                    pass
        code_val = code[0] if code else None
        token_val = token[0] if token else None
        if not code_val or not token_val:
            self._send_message(handler, 400, "Thiếu tham số code/token")
            return
        success, message = self.manager.XuLyWebhookNapTien(code_val, token_val)
        status_code = 200 if success else 400
        self._send_message(handler, status_code, message)

    def _send_json(self, handler: BaseHTTPRequestHandler, status: int, payload):
        body = json.dumps(payload).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    def _send_message(self, handler: BaseHTTPRequestHandler, status: int, message: str):
        body = f"<html><body><h2>{message}</h2></body></html>".encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
