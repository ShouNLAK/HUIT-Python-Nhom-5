import json
import socket
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Optional
from urllib.parse import parse_qs, urlparse


class MayChuWebhookNapTien:
    def __init__(self, quan_li, host: str = "0.0.0.0", cong: int = 5050, url_co_so_cong_khai: Optional[str] = None) -> None:
        self.quan_li = quan_li
        self.host = host
        self.cong = cong
        self.may_chu_http: Optional[ThreadingHTTPServer] = None
        self._luong: Optional[threading.Thread] = None
        self._khoa = threading.Lock()
        self.dang_chay = False
        self.url_co_so_cong_khai = url_co_so_cong_khai or self._xay_dung_url_cong_khai_mac_dinh()

    def _xay_dung_url_cong_khai_mac_dinh(self) -> str:
        ung_vien = self._phat_hien_ipv4()
        return f"http://{ung_vien}:{self.cong}"

    def _phat_hien_ipv4(self) -> str:
        try:
            kiem_tra = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            kiem_tra.connect(("8.8.8.8", 80))
            ip = kiem_tra.getsockname()[0]
            kiem_tra.close()
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass
        try:
            ten_may = socket.gethostname()
            ip = socket.gethostbyname(ten_may)
            phan = ip.split(".")
            if len(phan) == 4 and not ip.startswith("127."):
                return ip
        except Exception:
            pass
        return "127.0.0.1"

    def khoi_dong(self) -> bool:
        with self._khoa:
            if self.dang_chay:
                return True
            try:
                xu_ly = self._xay_dung_xu_ly()
                self.may_chu_http = ThreadingHTTPServer((self.host, self.cong), xu_ly)
                self.dang_chay = True
            except Exception:
                self.dang_chay = False
                self.may_chu_http = None
                raise
        self._luong = threading.Thread(target=self.may_chu_http.serve_forever, daemon=True)
        self._luong.start()
        return True

    def dung(self) -> None:
        with self._khoa:
            if not self.dang_chay:
                return
            if self.may_chu_http:
                try:
                    self.may_chu_http.shutdown()
                    self.may_chu_http.server_close()
                except Exception:
                    pass
            self.dang_chay = False
            self.may_chu_http = None

    def _xay_dung_xu_ly(self):
        may_chu = self

        class _XuLy(BaseHTTPRequestHandler):
            def do_GET(self):
                may_chu._xu_ly(self)

            def do_POST(self):
                may_chu._xu_ly(self)

            def log_message(self, format, *args):
                return

        return _XuLy

    def _xu_ly(self, xu_ly: BaseHTTPRequestHandler) -> None:
        phan_tich = urlparse(xu_ly.path)
        if phan_tich.path == "/health":
            self._gui_json(xu_ly, 200, {"status": "ok"})
            return
        if phan_tich.path != "/nap-tien":
            self._gui_json(xu_ly, 404, {"error": "Not found"})
            return
        tham_so = parse_qs(phan_tich.query)
        ma = tham_so.get("code", tham_so.get("request"))
        token = tham_so.get("token")
        if xu_ly.command == "POST":
            do_dai_noi_dung = int(xu_ly.headers.get("Content-Length", 0) or 0)
            if do_dai_noi_dung:
                try:
                    noi_dung = xu_ly.rfile.read(do_dai_noi_dung)
                    tai_trong = json.loads(noi_dung.decode("utf-8"))
                    ma = [tai_trong.get("code") or tai_trong.get("request")]
                    token = [tai_trong.get("token")]
                except Exception:
                    pass
        gia_tri_ma = ma[0] if ma else None
        gia_tri_token = token[0] if token else None
        if not gia_tri_ma or not gia_tri_token:
            self._gui_thong_bao(xu_ly, 400, "Thiếu tham số code/token")
            return
        thanh_cong, thong_bao = self.quan_li.xu_ly_webhook_nap_tien(gia_tri_ma, gia_tri_token)
        if thanh_cong:
            try:
                noi_dung = self.quan_li.phan_hoi_website(gia_tri_ma).encode('utf-8')
                xu_ly.send_response(200)
                xu_ly.send_header('Content-Type', 'text/html; charset=utf-8')
                xu_ly.send_header('Content-Length', str(len(noi_dung)))
                xu_ly.end_headers()
                xu_ly.wfile.write(noi_dung)
                return
            except Exception:
                pass
        ma_trang_thai = 200 if thanh_cong else 400
        self._gui_thong_bao(xu_ly, ma_trang_thai, thong_bao)

    def _gui_json(self, xu_ly: BaseHTTPRequestHandler, trang_thai: int, tai_trong):
        noi_dung = json.dumps(tai_trong).encode("utf-8")
        xu_ly.send_response(trang_thai)
        xu_ly.send_header("Content-Type", "application/json; charset=utf-8")
        xu_ly.send_header("Content-Length", str(len(noi_dung)))
        xu_ly.end_headers()
        xu_ly.wfile.write(noi_dung)

    def _gui_thong_bao(self, xu_ly: BaseHTTPRequestHandler, trang_thai: int, thong_bao: str):
        noi_dung = f"<html><body><h2>{thong_bao}</h2></body></html>".encode("utf-8")
        xu_ly.send_response(trang_thai)
        xu_ly.send_header("Content-Type", "text/html; charset=utf-8")
        xu_ly.send_header("Content-Length", str(len(noi_dung)))
        xu_ly.end_headers()
        xu_ly.wfile.write(noi_dung)
