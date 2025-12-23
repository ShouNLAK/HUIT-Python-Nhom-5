import base64
import hashlib
import io
import os
import re
import threading
from datetime import datetime, timedelta
from Class.user import NguoiDung
from Class.tour import TourDuLich
from Class.khach_hang import KhachHang
from Class.dat_tour import DatTour
from Class.nap_tien import YeuCauNapTien
from QuanLy.nap_tien_server import MayChuWebhookNapTien

try:
    import qrcode

    THU_VIEN_QR_SAN_SANG = True
except Exception:
    qrcode = None
    THU_VIEN_QR_SAN_SANG = False


class QuanLiDuLich:
    BAM_MA_TEN_DANG_NHAP_ROOT = "4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2"
    BAM_MA_MAT_KHAU_ROOT = "18885f27b5af9012df19e496460f9294d5ab76128824c6f993787004f6d9a7db"
    MA_TEN_DANG_NHAP_ROOT = "cm9vdC5zdXBlcnZpc29y"
    TEN_HIEN_THI_ROOT = "Root Operator"
    TEN_DANG_NHAP_ADMIN_MAC_DINH = "admin"
    MAT_KHAU_ADMIN_MAC_DINH = "Admin@123"
    TEN_ADMIN_MAC_DINH = "Quản trị viên"
    PHUT_HET_HAN_QR_MAC_DINH = 15
    HOST_WEBHOOK_MAC_DINH = "0.0.0.0"
    CONG_WEBHOOK_MAC_DINH = 5050
    def __init__(self):
        self.danh_sach_tour = []
        self.danh_sach_khach_hang = []
        self.danh_sach_dat_tour = []
        self.danh_sach_hdv = []
        self.danh_sach_nguoi_dung = []
        self.nguoi_dung_hien_tai = None
        self.danh_sach_nap_tien = []
        self._khoa_nap_tien = threading.Lock()
        self._may_chu_nap_tien = None
        self._xu_ly_tu_dong_luu = None
        self._url_qr_co_so = None

    def set_auto_save(self, handler):
        self._xu_ly_tu_dong_luu = handler

    def _trigger_auto_save(self):
        if callable(self._xu_ly_tu_dong_luu):
            try:
                self._xu_ly_tu_dong_luu()
            except Exception:
                pass

    def phan_tich_ngay(self, value):
        if not value:
            return None
        text = str(value).strip()
        if text.isdigit() and len(text) == 8:
            try:
                dd = int(text[:2])
                mm = int(text[2:4])
                yyyy = int(text[4:])
                return datetime(yyyy, mm, dd)
            except Exception:
                pass
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(text[:10], fmt)
            except Exception:
                continue
        return None

    def dinh_dang_ngay_ddmmyyyy(self, date_obj):
        if not date_obj:
            return ""
        return date_obj.strftime("%d/%m/%Y")

    def dien_giai_ngay(self, date_obj):
        if not date_obj:
            return ""
        thu_map = {
            0: "Thứ Hai",
            1: "Thứ Ba",
            2: "Thứ Tư",
            3: "Thứ Năm",
            4: "Thứ Sáu",
            5: "Thứ Bảy",
            6: "Chủ nhật",
        }
        thu = thu_map.get(date_obj.weekday(), "")
        return f"{thu}, ngày {date_obj.day:02d} tháng {date_obj.month:02d} năm {date_obj.year}"

    def kiem_tra_khung_ngay(self, ngay_di, ngay_ve):
        start = self.phan_tich_ngay(ngay_di) if ngay_di else None
        end = self.phan_tich_ngay(ngay_ve) if ngay_ve else None
        if ngay_di and not start:
            return False, None, None, "Ngày đi không đúng định dạng (DD/MM/YYYY)"
        if ngay_ve and not end:
            return False, None, None, "Ngày về không đúng định dạng (DD/MM/YYYY)"
        if start and end and end < start:
            return False, None, None, "Ngày về phải sau hoặc bằng ngày đi"
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        if start and start < today:
            return False, None, None, "Ngày đi phải từ hôm nay trở đi"
        return True, start, end, ""

    def kiem_tra_lich_trinh(self, lich_trinh, start_date, end_date):
        if not lich_trinh:
            return True, ""
        if not isinstance(lich_trinh, list):
            return False, "Lịch trình phải là danh sách các chặng"
        if not (start_date and end_date):
            return False, "Cần thiết lập Ngày đi và Ngày về trước khi thêm lịch trình"
        previous = None
        for idx, entry in enumerate(lich_trinh, start=1):
            if not isinstance(entry, dict):
                return False, f"Mục lịch trình #{idx} không hợp lệ"
            ngay = entry.get("ngay")
            diem = (entry.get("diaDiem") or entry.get('dia_diem', '') or "").strip()
            if not ngay:
                return False, f"Mục lịch trình #{idx} thiếu ngày"
            ngay_dt = self.phan_tich_ngay(ngay)
            if not ngay_dt:
                return False, f"Ngày ở mục #{idx} không đúng định dạng (DD/MM/YYYY)"
            if ngay_dt < start_date or ngay_dt > end_date:
                window = f"{self.dinh_dang_ngay_ddmmyyyy(start_date)} - {self.dinh_dang_ngay_ddmmyyyy(end_date)}"
                return False, f"Ngày {ngay} phải nằm trong khoảng {window}"
            if previous and ngay_dt < previous:
                return False, "Các mốc lịch trình phải được sắp xếp theo thứ tự thời gian"
            if not diem:
                return False, f"Mục lịch trình #{idx} thiếu địa điểm"
            previous = ngay_dt
        return True, ""

    def trang_thai_tour(self, tour, today=None):
        today = today or datetime.today().date()
        start = self.phan_tich_ngay(getattr(tour, "ngay_di", None))
        end = self.phan_tich_ngay(getattr(tour, "ngay_ve", None))
        if not start:
            return "chua_len_lich"
        if end is None:
            end = start
        start_d = start.date()
        end_d = end.date()
        if end_d < today:
            return "da_hoan_thanh"
        if start_d > today:
            return "da_len_lich"
        if start_d <= today <= end_d:
            return "dang_dien_ra"
        return "chua_len_lich"

    def dien_giai_trang_thai_tour(self, tour, today=None):
        ma = self.trang_thai_tour(tour, today)
        mapping = {
            "da_len_lich": "Đã lên lịch",
            "dang_dien_ra": "Đang diễn ra",
            "da_hoan_thanh": "Đã hoàn thành",
            "chua_len_lich": "Chưa lên lịch"
        }
        return mapping.get(ma, "Chưa lên lịch")

    def hop_le_so_dien_thoai_vn(self, phone):
        if not phone:
            return False
        phone = phone.strip()
        dau_so_hop_le = [
            "032","033","034","035","036","037","038","039",
            "052","056","058","059",
            "070","076","077","078","079",
            "081","082","083","084","085","086","087","088","089",
            "090","091","092","093","094","095","096","097","098","099"
        ]
        if len(phone) != 10:
            return False
        return phone[:3] in dau_so_hop_le and phone.isdigit()

    def _ten_lien_ket_du_kien(self, vai_tro, ma):
        if vai_tro == "user":
            kh = self.tim_khach_hang(ma)
            if kh and kh.ten_khach_hang:
                return kh.ten_khach_hang.strip()
        elif vai_tro == "hdv":
            hdv = self.tim_hdv(ma)
            if hdv and hdv.get("ten_hdv"):
                return hdv.get("ten_hdv").strip()
        return None

    def _dong_bo_ten_nguoi_dung_day_du(self, ma, vai_tro, ten_moi):
        if not ten_moi:
            return
        nguoi_dung = self.tim_nguoi_dung_theo_ma(ma, [vai_tro])
        if nguoi_dung:
            nguoi_dung.ten_day_du = ten_moi.strip()

    def dong_bo_ten_tu_khach(self, ma_khach_hang):
        ten = self._ten_lien_ket_du_kien("user", ma_khach_hang)
        if ten:
            self._dong_bo_ten_nguoi_dung_day_du(ma_khach_hang, "user", ten)

    def dong_bo_ten_tu_hdv(self, ma_hdv):
        ten = self._ten_lien_ket_du_kien("hdv", ma_hdv)
        if ten:
            self._dong_bo_ten_nguoi_dung_day_du(ma_hdv, "hdv", ten)

    def _lam_sach_ten_dang_nhap_goc(self, goc, mac_dinh="user"):
        da_lam_sach = re.sub(r"[^a-z0-9]+", "", (goc or "").lower())
        return da_lam_sach or mac_dinh

    def _tao_ten_dang_nhap_duy_nhat(self, goc):
        co_so = self._lam_sach_ten_dang_nhap_goc(goc)
        ung_vien = co_so
        dem = 1
        while self.tim_nguoi_dung(ung_vien):
            ung_vien = f"{co_so}{dem}"
            dem += 1
        return ung_vien

    def _thoi_gian_utc_hien_tai_iso(self):
        return datetime.utcnow().replace(microsecond=0).isoformat()

    def _tao_ma_yeu_cau(self):
        nguyen_thuy = base64.urlsafe_b64encode(os.urandom(12)).decode("ascii")
        return nguyen_thuy.rstrip("=")

    def _dam_bao_webhook_chay(self):
        if self._may_chu_nap_tien and self._may_chu_nap_tien.running:
            return True
        return self.khoi_dong_may_chu_webhook()

    def _xay_dung_url_qr(self, id_yeu_cau, ma):
        url_co_so = (
            (self._may_chu_nap_tien.public_base_url if self._may_chu_nap_tien else None)
            or self._url_qr_co_so
            or os.environ.get("NAP_TIEN_PUBLIC_URL")
            or f"http://127.0.0.1:{self.CONG_WEBHOOK_MAC_DINH}"
        )
        self._url_qr_co_so = url_co_so
        return f"{url_co_so.rstrip('/')}/nap-tien?code={id_yeu_cau}&token={ma}"

    def _tao_anh_qr(self, noi_dung, id_yeu_cau):
        if not THU_VIEN_QR_SAN_SANG or not qrcode:
            return None, "Thiếu thư viện qrcode. Chạy: pip install qrcode[pil]"
        try:
            qr = qrcode.QRCode(box_size=10, border=2)
            qr.add_data(noi_dung)
            qr.make(fit=True)
            anh = qr.make_image(fill_color="black", back_color="white")
            bo_dem = io.BytesIO()
            anh.save(bo_dem, format="PNG")
            ma_hoa = base64.b64encode(bo_dem.getvalue()).decode("ascii")
            du_lieu_uri = f"data:image/png;base64,{ma_hoa}"
            return du_lieu_uri, ""
        except Exception as exc:
            return None, f"Không thể tạo QR: {exc}"

    def _tao_ma_nap_tien(self):
        tien_to = datetime.utcnow().strftime("NT%Y%m%d%H%M%S")
        ton_tai = {req.ma_giao_dich for req in getattr(self, "danh_sach_nap_tien", [])}
        chi_so = 1
        ung_vien = f"{tien_to}{chi_so:03d}"
        while ung_vien in ton_tai:
            chi_so += 1
            ung_vien = f"{tien_to}{chi_so:03d}"
        return ung_vien

    def tim_yeu_cau_nap_tien(self, ma_giao_dich):
        for yeu_cau in getattr(self, "danh_sach_nap_tien", []):
            if yeu_cau.ma_giao_dich == ma_giao_dich:
                return yeu_cau
        return None

    def lay_nap_tien_theo_khach(self, ma_khach_hang):
        return [yeu_cau for yeu_cau in getattr(self, "danh_sach_nap_tien", []) if yeu_cau.ma_khach_hang == ma_khach_hang]

    def _loai_bo_yeu_cau_het_han(self):
        da_thay_doi = False
        for yeu_cau in getattr(self, "danh_sach_nap_tien", []):
            if yeu_cau.trang_thai == YeuCauNapTien.TRANG_THAI_CHO and yeu_cau.da_het_han():
                yeu_cau.danh_dau_het_han()
                da_thay_doi = True
        if da_thay_doi:
            self._trigger_auto_save()

    def khoi_dong_webhook_server(self, host=None, cong=None, url_co_so_cong_khai=None):
        host = host or self.HOST_WEBHOOK_MAC_DINH
        cong = cong or self.CONG_WEBHOOK_MAC_DINH
        if self._may_chu_nap_tien and self._may_chu_nap_tien.dang_chay:
            return True
        try:
            self._may_chu_nap_tien = MayChuWebhookNapTien(self, host=host, cong=cong, url_co_so_cong_khai=url_co_so_cong_khai)
            self._may_chu_nap_tien.khoi_dong()
            self._url_qr_co_so = self._may_chu_nap_tien.url_co_so_cong_khai
            print(f"Máy chủ webhook nạp tiền đang lắng nghe tại {self._url_qr_co_so}")
            return True
        except Exception as exc:
            print(f"Không thể khởi động webhook nạp tiền: {exc}")
            self._may_chu_nap_tien = None
            return False

    def dung_webhook_nap_tien(self):
        if self._may_chu_nap_tien:
            self._may_chu_nap_tien.dung()
            self._may_chu_nap_tien = None

    def tao_yeu_cau_nap_tien(self, ma_khach_hang, so_tien, phut_het_han=None):
        self._loai_bo_yeu_cau_het_han()
        if not self.nguoi_dung_hien_tai:
            return False, "Bạn phải đăng nhập"
        if self.nguoi_dung_hien_tai.vai_tro == "user" and str(self.nguoi_dung_hien_tai.ma_khach_hang) != str(ma_khach_hang):
            return False, "Bạn chỉ có thể nạp tiền cho tài khoản của mình"
        try:
            so_tien = float(so_tien)
        except Exception:
            return False, "Số tiền không hợp lệ"
        if so_tien <= 0:
            return False, "Số tiền phải lớn hơn 0"
        kh = self.tim_khach_hang(ma_khach_hang)
        if not kh:
            return False, "Không tìm thấy khách hàng"
        phut_het_han = phut_het_han or self.PHUT_HET_HAN_QR_MAC_DINH
        if not self._dam_bao_webhook_chay():
            return False, "Không thể khởi động webhook nạp tiền"
        id_yeu_cau = self._tao_ma_nap_tien()
        ma = self._tao_ma_yeu_cau()
        url_qr = self._xay_dung_url_qr(id_yeu_cau, ma)
        du_lieu_uri_qr, loi = self._tao_anh_qr(url_qr, id_yeu_cau)
        if not du_lieu_uri_qr:
            return False, loi
        thoi_gian_het_han = (datetime.utcnow() + timedelta(minutes=phut_het_han)).replace(microsecond=0).isoformat()
        yeu_cau = YeuCauNapTien(
            ma_giao_dich=id_yeu_cau,
            so_tien=so_tien,
            noi_dung=url_qr,
            trang_thai=YeuCauNapTien.TRANG_THAI_CHO,
            thoi_gian_het_han=thoi_gian_het_han,
            du_lieu_qr=du_lieu_uri_qr,
        )
        with self._khoa_nap_tien:
            self.danh_sach_nap_tien.append(yeu_cau)
        self._trigger_auto_save()
        return True, {
            "ma_giao_dich": id_yeu_cau,
            "du_lieu_uri_qr": du_lieu_uri_qr,
            "url_qr": url_qr,
            "thoi_gian_het_han": thoi_gian_het_han,
            "so_tien": so_tien,
        }

    def lay_thong_tin_nap_tien(self, ma_giao_dich):
        yeu_cau = self.tim_yeu_cau_nap_tien(ma_giao_dich)
        if not yeu_cau:
            return None
        return {
            "ma_giao_dich": yeu_cau.ma_giao_dich,
            "ma_khach_hang": yeu_cau.ma_khach_hang,
            "so_tien": yeu_cau.so_tien,
            "trang_thai": yeu_cau.trang_thai,
            "thoi_gian_het_han": yeu_cau.thoi_gian_het_han,
            "du_lieu_qr": yeu_cau.du_lieu_qr,
            "url_qr": yeu_cau.noi_dung_qr,
        }

    def xu_ly_webhook_nap_tien(self, id_yeu_cau, ma):
        self._loai_bo_yeu_cau_het_han()
        with self._khoa_nap_tien:
            yeu_cau = self.tim_yeu_cau_nap_tien(id_yeu_cau)
            if not yeu_cau:
                return False, "Không tìm thấy giao dịch"
            if yeu_cau.trang_thai == YeuCauNapTien.TRANG_THAI_XAC_NHAN:
                return True, "Giao dịch đã được xác nhận trước đó"
            if yeu_cau.da_het_han():
                yeu_cau.danh_dau_het_han()
                self._trigger_auto_save()
                return False, "Mã QR đã hết hạn"
            if ma != yeu_cau.token:
                return False, "Token không hợp lệ"
            kh = self.tim_khach_hang(yeu_cau.ma_khach_hang)
            if not kh:
                return False, "Không tìm thấy khách hàng"
            kh.so_du += yeu_cau.so_tien
            yeu_cau.danh_dau_xac_nhan()
            yeu_cau.thong_tin_bo_sung["xac_nhan_tai"] = self._thoi_gian_utc_hien_tai_iso()
            self._trigger_auto_save()
            return True, self.phan_hoi_website(yeu_cau)

    def phan_hoi_website(self, yeu_cau_hoac_id):
        yeu_cau = yeu_cau_hoac_id
        if isinstance(yeu_cau_hoac_id, (str, int)):
            try:
                yeu_cau = self.tim_yeu_cau_nap_tien(str(yeu_cau_hoac_id))
            except Exception:
                yeu_cau = None
        if not yeu_cau:
            html = '<!doctype html><html><body><h2>Không tìm thấy giao dịch</h2></body></html>'
            return html
        so_tien = getattr(yeu_cau, 'so_tien', 0)
        ma_giao_dich = getattr(yeu_cau, 'ma_giao_dich', '')
        ma_khach_hang = getattr(yeu_cau, 'ma_khach_hang', '')
        xac_nhan_tai = yeu_cau.thong_tin_bo_sung.get('xac_nhan_tai', '') if hasattr(yeu_cau, 'thong_tin_bo_sung') else ''
        kh = self.tim_khach_hang(ma_khach_hang)
        ten = kh.ten_khach_hang if kh else (str(ma_khach_hang) or 'Khách hàng')
        html = f'''<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thanh toán thành công</title>
<style>
body{{font-family:Segoe UI,Roboto,Arial,sans-serif;background:#f4f7fb;margin:0;padding:0;display:flex;align-items:center;justify-content:center;height:100vh}}
.card{{background:#fff;border-radius:12px;padding:28px;box-shadow:0 8px 30px rgba(20,30,50,0.08);max-width:720px;width:90%}}
.check{{width:96px;height:96px;border-radius:50%;background:#e6fbf3;display:flex;align-items:center;justify-content:center;margin:0 auto}}
.check svg{{width:56px;height:56px;stroke:#12a454;stroke-width:6;stroke-linecap:round;stroke-linejoin:round;fill:none}}
.title{{font-size:20px;font-weight:700;color:#123}}
.meta{{color:#556; margin-top:8px}}
.details{{margin-top:18px;padding:12px;background:#fbfdff;border-radius:8px;border:1px solid #eef3ff}}
.label{{font-weight:600;color:#334;display:block}}
.value{{color:#0b1640;margin-top:6px}}
@keyframes pop{{0%{{transform:scale(.8);opacity:0}}60%{{transform:scale(1.06);opacity:1}}100%{{transform:scale(1);opacity:1}}}}
.check{{animation:pop .6s ease}}
</style>
</head>
<body>
<div class="card">
<div class="check">
<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
</div>
<h1 class="title" style="text-align:center;margin-top:12px">Thanh toán thành công</h1>
<p class="meta" style="text-align:center">Giao dịch đã được xác nhận tự động trên hệ thống</p>
<div class="details">
<span class="label">Mã giao dịch</span>
<div class="value">{ma_giao_dich}</div>
<span class="label">Tên khách</span>
<div class="value">{ten}</div>
<span class="label">Số tiền</span>
<div class="value">{int(so_tien):,} VND</div>
<span class="label">Thời gian xác nhận</span>
<div class="value">{xac_nhan_tai}</div>
</div>
</div>
</body>
</html>'''
        return html

    def ensure_user_for_khach(self, kh: KhachHang, default_password="123"):
        if not kh or not kh.ma_khach_hang:
            return None
        code = str(kh.ma_khach_hang).strip()
        existing = self.tim_nguoi_dung_theo_ma(code, ["user"])
        if existing:
            existing.ten_hien_thi = kh.ten_khach_hang
            return existing.ten_dang_nhap
        username = self._tao_ten_dang_nhap_duy_nhat(code)
        self.danh_sach_nguoi_dung.append(NguoiDung(username, default_password, "user", code, kh.ten_khach_hang))
        return username

    def ensure_user_for_hdv(self, hdv, default_password="123"):
        if not hdv:
            return None
        ma = None
        ten = None
        if isinstance(hdv, dict):
            ma = str(hdv.get("maHDV") or "").strip()
            ten = (hdv.get("tenHDV") or "").strip() or None
        if not ma:
            return None
        existing = self.tim_nguoi_dung_theo_ma(ma, ["hdv"])
        if existing:
            existing.ten_hien_thi = ten or existing.ten_hien_thi
            return existing.ten_dang_nhap
        username = self._tao_ten_dang_nhap_duy_nhat(ma)
        self.danh_sach_nguoi_dung.append(NguoiDung(username, default_password, "hdv", ma, ten or username))
        return username

    def dong_bo_tai_khoan_lien_ket(self):
        for kh in self.danh_sach_khach_hang:
            self.ensure_user_for_khach(kh)
        for hdv in getattr(self, "danh_sach_hdv", []) or []:
            self.ensure_user_for_hdv(hdv)
        def is_valid(u):
            if u.vai_tro == "admin" or u.vai_tro == "root":
                return True
            if u.vai_tro == "user":
                return self.tim_khach_hang(u.ma_khach_hang) is not None
            if u.vai_tro == "hdv":
                return self.tim_hdv(u.ma_khach_hang) is not None
            return False
        self.danh_sach_nguoi_dung = [u for u in self.danh_sach_nguoi_dung if is_valid(u)]

    def _hash_value(self, value):
        if value is None:
            return ""
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _giai_ma_ma(self, ma):
        try:
            return base64.b64decode(ma.encode("utf-8")).decode("utf-8")
        except Exception:
            return ""

    def _ten_dang_nhap_root(self):
        ten = self._giai_ma_ma(self.MA_TEN_DANG_NHAP_ROOT)
        return ten or "root"

    def _xay_dung_nguoi_dung_root(self):
        return NguoiDung(self._ten_dang_nhap_root(), "", "root", None, self.TEN_HIEN_THI_ROOT)

    def _kiem_tra_ten_dang_nhap(self, ten_dang_nhap):
        if not ten_dang_nhap:
            return False
        return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{4,31}", ten_dang_nhap))

    def _kiem_tra_mat_khau(self, mat_khau, cho_phep_mac_dinh=False):
        if cho_phep_mac_dinh and mat_khau == "123":
            return True
        if not mat_khau or len(mat_khau) < 4 or len(mat_khau) > 64:
            return False
        return not re.search(r"\s", mat_khau)

    def _kiem_tra_ten_day_du(self, ten_day_du):
        if not ten_day_du:
            return False
        da_cat = ten_day_du.strip()
        if len(da_cat) < 3 or len(da_cat) > 80:
            return False
        return True

    def tim_nguoi_dung(self, ten_dang_nhap):
        return next((u for u in self.danh_sach_nguoi_dung if u.ten_dang_nhap == ten_dang_nhap), None)

    def tim_nguoi_dung_theo_ma(self, ma_khach_hang, vai_tro_cho_phep=None):
        if ma_khach_hang is None:
            return None
        target = str(ma_khach_hang)
        for u in self.danh_sach_nguoi_dung:
            if str(u.ma_khach_hang) == target and (not vai_tro_cho_phep or u.vai_tro in vai_tro_cho_phep):
                return u
        return None

    def dem_so_admin(self):
        return sum(1 for u in self.danh_sach_nguoi_dung if u.vai_tro == "admin")

    def dat_lai_mat_khau(self, ten_dang_nhap, mat_khau_moi):
        nguoi_dung = self.tim_nguoi_dung(ten_dang_nhap)
        if not nguoi_dung:
            return False, "Không tìm thấy tài khoản"
        if not self._kiem_tra_mat_khau(mat_khau_moi, cho_phep_mac_dinh=True):
            return False, "Mật khẩu không hợp lệ"
        nguoi_dung.mat_khau = mat_khau_moi
        return True, "Đã đặt lại mật khẩu"

    def ensure_default_accounts(self):
        if not any(u.vai_tro == "admin" for u in self.danh_sach_nguoi_dung):
            admin = NguoiDung(
                self.TEN_DANG_NHAP_ADMIN_MAC_DINH,
                self.MAT_KHAU_ADMIN_MAC_DINH,
                "admin",
                None,
                self.TEN_ADMIN_MAC_DINH,
            )
            if not self.tim_nguoi_dung(admin.ten_dang_nhap):
                self.danh_sach_nguoi_dung.append(admin)

    def tao_ma_khach_tu_dong(self):
        existing = []
        for k in self.danh_sach_khach_hang:
            if k.ma_khach_hang and k.ma_khach_hang.upper().startswith("KH"):
                tail = k.ma_khach_hang.upper().replace("KH", "", 1)
                if tail.isdigit():
                    existing.append(int(tail))
        next_id = (max(existing) + 1) if existing else 1
        return f"KH{str(next_id).zfill(3)}"

    def dang_ky_nguoi_dung(self, ten_dang_nhap, mat_khau, vai_tro="user", ma_khach_hang=None, ten_day_du=None):
        ten_dang_nhap = (ten_dang_nhap or "").strip()
        mat_khau = mat_khau or ""
        vai_tro = (vai_tro or "user").lower()
        if not self._kiem_tra_ten_dang_nhap(ten_dang_nhap):
            return False, "Tên đăng nhập phải dài tối thiểu 5 ký tự và không chứa khoảng trắng"
        if self.tim_nguoi_dung(ten_dang_nhap):
            return False, "Tên đăng nhập đã tồn tại"
        if vai_tro not in ["admin", "user", "hdv"]:
            return False, "Vai trò không hợp lệ"
        ma_lien_ket = ma_khach_hang
        if vai_tro in ("user", "hdv"):
            if not ma_lien_ket:
                return False, "Thiếu mã liên kết"
            if vai_tro == "user" and self.tim_khach_hang(ma_lien_ket) is None:
                return False, "Mã khách hàng không tồn tại"
            if vai_tro == "hdv" and self.tim_hdv(ma_lien_ket) is None:
                return False, "Mã HDV không tồn tại"
            if self.tim_nguoi_dung_theo_ma(ma_lien_ket, [vai_tro]):
                return False, "Mã liên kết đã có tài khoản"
        else:
            ma_lien_ket = None
        if not self._kiem_tra_mat_khau(mat_khau):
            return False, "Mật khẩu phải từ 4 đến 64 ký tự và không có khoảng trắng"
        ten_day_du_cung_cap = (ten_day_du or "").strip()
        if vai_tro in ("user", "hdv"):
            ten_du_kien = self._ten_lien_ket_du_kien(vai_tro, ma_lien_ket)
            if not ten_du_kien or not self._kiem_tra_ten_day_du(ten_du_kien):
                return False, "Tên hiển thị của thông tin liên kết không hợp lệ"
            if ten_day_du_cung_cap and ten_day_du_cung_cap != ten_du_kien:
                return False, "Họ tên tài khoản phải trùng với tên đã đăng ký"
            ten_hien_thi = ten_du_kien
        else:
            ten_hien_thi = ten_day_du_cung_cap or ten_dang_nhap
            if not self._kiem_tra_ten_day_du(ten_hien_thi):
                return False, "Họ tên hiển thị không hợp lệ"
        self.danh_sach_nguoi_dung.append(NguoiDung(ten_dang_nhap, mat_khau, vai_tro, ma_lien_ket, ten_hien_thi))
        return True, "Tạo tài khoản thành công"

    def dang_nhap(self, ten_dang_nhap, mat_khau):
        ten_dang_nhap_nhap = (ten_dang_nhap or "").strip()
        mat_khau_nhap = mat_khau or ""
        if self._hash_value(ten_dang_nhap_nhap) == self.BAM_MA_TEN_DANG_NHAP_ROOT and self._hash_value(mat_khau_nhap) == self.BAM_MA_MAT_KHAU_ROOT:
            self.nguoi_dung_hien_tai = self._xay_dung_nguoi_dung_root()
            print("Đăng nhập thành công (vai trò: root)")
            return True
        for u in self.danh_sach_nguoi_dung:
            if u.ten_dang_nhap == ten_dang_nhap_nhap and u.mat_khau == mat_khau_nhap:
                self.nguoi_dung_hien_tai = u
                print(f"Đăng nhập thành công (vai trò: {u.vai_tro})")
                return True
        print("Sai tài khoản hoặc mật khẩu")
        return False

    def them_khach_hang(self, kh: KhachHang, allow_public=False, auto_link_account=True):
        if not allow_public and (not self.nguoi_dung_hien_tai or self.nguoi_dung_hien_tai.vai_tro != "admin"):
            print("Bạn không có quyền thực hiện!")
            return False
        ma = (kh.ma_khach_hang or "").strip().upper()
        ten = (kh.ten_khach_hang or "").strip()
        if not re.fullmatch(r"KH\d{3,}", ma):
            print("Mã khách hàng phải theo định dạng KH###")
            return False
        if not self._kiem_tra_ten_day_du(ten):
            print("Tên khách không hợp lệ")
            return False
        if self.tim_khach_hang(ma) is not None:
            print("Mã khách hàng đã tồn tại!")
            return False
        phone = (kh.so_dien_thoai or "").strip()
        if not self.hop_le_so_dien_thoai_vn(phone):
            print("Số điện thoại không hợp lệ!")
            return False
        if any(existing.so_dien_thoai == phone for existing in self.danh_sach_khach_hang):
            print("Số điện thoại đã tồn tại")
            return False
        email = (kh.email or "").strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            print("Email không hợp lệ!")
            return False
        if any(existing.email.lower() == email for existing in self.danh_sach_khach_hang if existing.email):
            print("Email đã được sử dụng")
            return False
        if kh.so_du < 0:
            print("Số dư không hợp lệ")
            return False
        kh.ma_khach_hang = ma
        kh.ten_khach_hang = ten
        kh.so_dien_thoai = phone
        kh.email = email
        self.danh_sach_khach_hang.append(kh)
        self.dong_bo_ten_tu_khach(kh.ma_khach_hang)
        if auto_link_account:
            self.ensure_user_for_khach(kh)
        print("Thêm khách hàng thành công")
        return True

    def hien_thi_danh_sach_khach_hang(self):
        if not self.nguoi_dung_hien_tai:
            print("Bạn phải đăng nhập!")
            return []
        if self.nguoi_dung_hien_tai.vai_tro == "admin":
            return self.danh_sach_khach_hang
        return [kh for kh in self.danh_sach_khach_hang if kh.ma_khach_hang == self.nguoi_dung_hien_tai.ma_khach_hang]

    def tim_hdv(self, ma_hdv: str):
        if not hasattr(self, "danh_sach_hdv"):
            self.danh_sach_hdv = []
        for hdv in self.danh_sach_hdv:
            if str(hdv.get("ma_hdv")) == str(ma_hdv):
                return hdv
        return None

    def tim_khach_hang(self, ma_khach_hang: str):
        for kh in self.danh_sach_khach_hang:
            if kh.ma_khach_hang == ma_khach_hang:
                return kh
        return None

    def lay_ten_hien_thi(self, user: NguoiDung):
        if not user:
            return ""
        if user.vai_tro == "root":
            return self.TEN_HIEN_THI_ROOT
        if user.vai_tro == "user" and user.ma_khach_hang:
            kh = self.tim_khach_hang(user.ma_khach_hang)
            return kh.ten_khach_hang if kh else user.ten_hien_thi
        if user.vai_tro == "hdv" and user.ma_khach_hang:
            hdv = self.tim_hdv(user.ma_khach_hang)
            return hdv.get("tenHDV") if hdv else user.ten_hien_thi
        return user.ten_hien_thi

    def lay_danh_sach_admin(self):
        return [u for u in self.danh_sach_nguoi_dung if u.vai_tro == "admin"]

    def cap_nhat_admin(self, ten_dang_nhap, ten_hien_thi=None, mat_khau=None):
        admin = self.tim_nguoi_dung(ten_dang_nhap)
        if not admin or admin.vai_tro != "admin":
            return False, "Không tìm thấy tài khoản admin"
        if ten_hien_thi is not None:
            if not self._kiem_tra_ten_day_du(ten_hien_thi):
                return False, "Họ tên không hợp lệ"
            admin.ten_hien_thi = ten_hien_thi.strip()
        if mat_khau is not None:
            if not self._kiem_tra_mat_khau(mat_khau):
                return False, "Mật khẩu không hợp lệ"
            admin.mat_khau = mat_khau
        return True, "Đã cập nhật"

    def xoa_admin(self, ten_dang_nhap):
        admin = self.tim_nguoi_dung(ten_dang_nhap)
        if not admin or admin.vai_tro != "admin":
            return False, "Không tìm thấy tài khoản admin"
        if self.dem_so_admin() <= 1:
            return False, "Cần ít nhất một tài khoản admin"
        self.danh_sach_nguoi_dung = [u for u in self.danh_sach_nguoi_dung if u.ten_dang_nhap != ten_dang_nhap]
        return True, "Đã xóa admin"

    def dat_lai_mat_khau_theo_ma(self, ma, vai_tro, mat_khau_mac_dinh="123"):
        nguoi_dung = self.tim_nguoi_dung_theo_ma(ma, [vai_tro])
        if not nguoi_dung:
            return False, "Không tìm thấy tài khoản"
        if not self._kiem_tra_mat_khau(mat_khau_mac_dinh, cho_phep_mac_dinh=True):
            return False, "Mật khẩu mặc định không hợp lệ"
        nguoi_dung.mat_khau = mat_khau_mac_dinh
        return True, "Đã đặt lại mật khẩu"

    def cap_nhat_khach_hang(self, ma_khach_hang=None, ten_khach_hang=None, so_dien_thoai=None, email=None, so_du=None):
        if not self.nguoi_dung_hien_tai or self.nguoi_dung_hien_tai.vai_tro != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        kh = self.tim_khach_hang(ma_khach_hang)
        if kh is None:
            print("Khách hàng không tồn tại!")
            return False
        if ten_khach_hang is not None:
            if not ten_khach_hang.strip():
                print("Tên khách không hợp lệ")
                return False
            kh.ten_khach_hang = ten_khach_hang.strip()
            self.ensure_user_for_khach(kh)
        if so_dien_thoai is not None:
            if not self.hop_le_so_dien_thoai_vn(so_dien_thoai):
                print("Số điện thoại không hợp lệ!")
                return False
            if any(other.so_dien_thoai == so_dien_thoai and other.ma_khach_hang != kh.ma_khach_hang for other in self.danh_sach_khach_hang):
                print("Số điện thoại đã được sử dụng")
                return False
            kh.so_dien_thoai = so_dien_thoai
        if email is not None:
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                print("Email không hợp lệ!")
                return False
            if any((other.email or "").lower() == email.lower() and other.ma_khach_hang != kh.ma_khach_hang for other in self.danh_sach_khach_hang):
                print("Email đã được sử dụng")
                return False
            kh.email = email
        if so_du is not None:
            if so_du < 0:
                print("Số dư không hợp lệ!")
                return False
            kh.so_du = so_du
        print("Cập nhật thành công")
        return True

    def xoa_khach_hang(self, ma_khach_hang):
        if not self.nguoi_dung_hien_tai or self.nguoi_dung_hien_tai.vai_tro != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        kh = self.tim_khach_hang(ma_khach_hang)
        if kh is None:
            print("Khách hàng không tồn tại")
            return False
        for dt in self.danh_sach_dat_tour:
            if dt.ma_khach_hang == ma_khach_hang and dt.trang_thai == "da_thanh_toan":
                print("Không thể xóa! Khách hàng còn đơn đã thanh toán!")
                return False
        self.danh_sach_khach_hang = [k for k in self.danh_sach_khach_hang if k.ma_khach_hang != ma_khach_hang]
        self.danh_sach_nguoi_dung = [u for u in self.danh_sach_nguoi_dung if not (u.ma_khach_hang == ma_khach_hang and u.vai_tro == "user")]
        print("Xóa khách hàng thành công")
        return True

    def them_tour(self, tour: TourDuLich):
        if not self.nguoi_dung_hien_tai or self.nguoi_dung_hien_tai.vai_tro != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        if not tour.ma_tour:
            print("Mã tour trống")
            return False
        if self.tim_tour(tour.ma_tour):
            print("Mã tour đã tồn tại!")
            return False
        if tour.gia_tour <= 0:
            print("Giá tour không hợp lệ")
            return False
        if tour.so_cho < 1:
            print("Số chỗ phải >= 1")
            return False
        ngay_di = getattr(tour, "ngay_di", None)
        ngay_ve = getattr(tour, "ngay_ve", None)
        ok, start, end, msg = self.kiem_tra_khung_ngay(ngay_di, ngay_ve)
        if not ok:
            print(msg)
            return False
        ok, msg = self.kiem_tra_lich_trinh(getattr(tour, "lich_trinh", []), start, end)
        if not ok:
            print(msg)
            return False
        self.danh_sach_tour.append(tour)
        print("Thêm tour thành công")
        return True

    def hien_thi_danh_sach_tour(self):
        return self.danh_sach_tour

    def tim_tour(self, ma_tour: str):
        for t in self.danh_sach_tour:
            if t.ma_tour == ma_tour:
                return t
        return None

    def cap_nhat_tour(self, ma_tour=None, ten_tour=None, gia_tour=None, so_cho=None, lich_trinh=None, huong_dan_vien=None, ngay_di=None, ngay_ve=None):
        if not self.nguoi_dung_hien_tai or self.nguoi_dung_hien_tai.vai_tro != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        t = self.tim_tour(ma_tour)
        if t is None:
            print("Tour không tồn tại!")
            return False
        trang_thai = self.trang_thai_tour(t)
        if trang_thai in ("dang_dien_ra", "da_hoan_thanh"):
            print("Không thể cập nhật tour đang diễn ra hoặc đã hoàn thành")
            return False
        new_ngay_di = ngay_di if ngay_di is not None else getattr(t, "ngay_di", None)
        new_ngay_ve = ngay_ve if ngay_ve is not None else getattr(t, "ngay_ve", None)
        schedule = lich_trinh if lich_trinh is not None else t.lich_trinh
        ok, start, end, msg = self.kiem_tra_khung_ngay(new_ngay_di, new_ngay_ve)
        if not ok:
            print(msg)
            return False
        ok, msg = self.kiem_tra_lich_trinh(schedule, start, end)
        if not ok:
            print(msg)
            return False
        if ten_tour is not None:
            t.ten_tour = ten_tour
        if gia_tour is not None:
            if gia_tour <= 0:
                print("Giá không hợp lệ")
                return False
            t.gia_tour = gia_tour
        if so_cho is not None:
            if so_cho < 1:
                print("Số chỗ phải >=1")
                return False
            t.so_cho = so_cho
        t.lich_trinh = schedule
        t.ngay_di = new_ngay_di
        t.ngay_ve = new_ngay_ve
        if huong_dan_vien is not None:
            t.huong_dan_vien = huong_dan_vien
        print("Cập nhật tour thành công")
        return True

    def xoa_tour(self, ma_tour):
        if not self.nguoi_dung_hien_tai or self.nguoi_dung_hien_tai.vai_tro != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        t = self.tim_tour(ma_tour)
        if t is None:
            print("Tour không tồn tại")
            return False
        for dt in self.danh_sach_dat_tour:
            if dt.ma_tour == ma_tour and dt.trang_thai == "da_thanh_toan":
                print("Không thể xóa! Tour đã có người đặt và thanh toán!")
                return False
        self.danh_sach_tour = [tour for tour in self.danh_sach_tour if tour.ma_tour != ma_tour]
        print("Xóa tour thành công")
        return True

    def dat_tour_moi(self, dat: DatTour):
        if self.nguoi_dung_hien_tai and self.nguoi_dung_hien_tai.vai_tro == "user":
            dat.ma_khach_hang = self.nguoi_dung_hien_tai.ma_khach_hang

        kh = self.tim_khach_hang(dat.ma_khach_hang)
        tour = self.tim_tour(dat.ma_tour)

        if any(d.ma_dat_tour == dat.ma_dat_tour for d in self.danh_sach_dat_tour):
            raise ValueError("Mã đặt tour đã tồn tại")
        if not kh:
            raise ValueError("Khách hàng không tồn tại")
        if not tour:
            raise ValueError("Tour không tồn tại")

        ngay_dat = self.phan_tich_ngay(dat.ngay)
        if not ngay_dat:
            raise ValueError("Ngày đặt không đúng định dạng (DD/MM/YYYY)")
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        if ngay_dat.date() < today.date():
            raise ValueError("Không thể đặt tour trong quá khứ")

        if dat.so_nguoi <= 0:
            raise ValueError("Số người phải >= 1")
        if dat.so_nguoi > tour.so_cho:
            raise ValueError("Không đủ chỗ")

        trang_thai = self.trang_thai_tour(tour, today.date())
        if trang_thai == "da_hoan_thanh":
            raise ValueError("Tour đã kết thúc, không thể đặt")
        if tour.ngay_di and ngay_dat.date() < tour.ngay_di:
            raise ValueError("Ngày đặt phải từ ngày đi trở về sau")
        if tour.ngay_ve and ngay_dat.date() > tour.ngay_ve:
            raise ValueError("Ngày đặt phải trước hoặc trong ngày về")

        dat.tong_tien = dat.so_nguoi * tour.gia_tour
        if kh.so_du < dat.tong_tien:
            raise ValueError("Không đủ số dư")

        kh.so_du -= dat.tong_tien
        tour.so_cho -= dat.so_nguoi
        dat.trang_thai = "da_thanh_toan"
        self.danh_sach_dat_tour.append(dat)
        return True

    def hien_thi_danh_sach_dat_tour(self):
        if not self.nguoi_dung_hien_tai:
            print("Bạn phải đăng nhập!")
            return []
        if self.nguoi_dung_hien_tai.vai_tro == "admin":
            return self.danh_sach_dat_tour
        return [d for d in self.danh_sach_dat_tour if d.ma_khach_hang == self.nguoi_dung_hien_tai.ma_khach_hang]

    def tim_dat_tour_theo_ma(self, ma_dat):
        d = next((x for x in self.danh_sach_dat_tour if x.ma_dat_tour == ma_dat), None)
        if not d:
            return None
        if self.nguoi_dung_hien_tai and self.nguoi_dung_hien_tai.vai_tro == "user" and d.ma_khach_hang != self.nguoi_dung_hien_tai.ma_khach_hang:
            print("Bạn không thể xem đơn của người khác!")
            return None
        return d

    def tim_dat_tour_theo_khach(self, ma_khach_hang):
        if not self.nguoi_dung_hien_tai:
            print("Bạn phải đăng nhập!")
            return []
        if self.nguoi_dung_hien_tai.vai_tro == "admin":
            return [d for d in self.danh_sach_dat_tour if d.ma_khach_hang == ma_khach_hang]
        if ma_khach_hang != self.nguoi_dung_hien_tai.ma_khach_hang:
            print("Bạn không thể xem đơn của người khác!")
            return []
        return [d for d in self.danh_sach_dat_tour if d.ma_khach_hang == ma_khach_hang]

    def cap_nhat_dat_tour(self, ma_dat, ma_tour=None, so_nguoi=None):
        if not self.nguoi_dung_hien_tai or self.nguoi_dung_hien_tai.vai_tro != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        d = self.tim_dat_tour_theo_ma(ma_dat)
        if not d:
            print("Không tìm thấy đơn")
            return False
        if d.trang_thai != "da_thanh_toan":
            print("Chỉ cập nhật đơn đã thanh toán")
            return False
        if (ma_tour is None or ma_tour == d.ma_tour) and (so_nguoi is None or so_nguoi == d.so_nguoi):
            print("Không có dữ liệu cần cập nhật")
            return True
        kh = self.tim_khach_hang(d.ma_khach_hang)
        tourCu = self.tim_tour(d.ma_tour)
        tourMoi = self.tim_tour(ma_tour) if ma_tour else tourCu
        if self.trang_thai_tour(tourCu) in ("dang_dien_ra", "da_hoan_thanh"):
            print("Không thể cập nhật đơn khi tour đang diễn ra hoặc đã hoàn thành")
            return False
        if not tourMoi:
            print("Tour mới không tồn tại")
            return False
        if self.trang_thai_tour(tourMoi) in ("dang_dien_ra", "da_hoan_thanh"):
            print("Tour mới đang diễn ra hoặc đã hoàn thành, không thể chuyển")
            return False
        so_nguoi_moi = so_nguoi if so_nguoi is not None else d.so_nguoi
        if so_nguoi_moi <= 0:
            print("Số người phải >= 1")
            return False
        if tourMoi.ma_tour == tourCu.ma_tour:
            soChoKhaDung = tourCu.so_cho + d.so_nguoi
        else:
            soChoKhaDung = tourMoi.so_cho
        if so_nguoi_moi > soChoKhaDung:
            print("Không đủ chỗ")
            return False
        tongTienMoi = so_nguoi_moi * tourMoi.gia_tour
        if tongTienMoi > (kh.so_du + d.tong_tien):
            print("Không đủ số dư")
            return False
        if self.trang_thai_tour(tourMoi) == "da_hoan_thanh":
            print("Tour mới đã hoàn thành, không thể chuyển")
            return False
        tourCu.so_cho += d.so_nguoi
        kh.so_du += d.tong_tien
        tourMoi.so_cho -= so_nguoi_moi
        kh.so_du -= tongTienMoi
        d.ma_tour = tourMoi.ma_tour
        d.so_nguoi = so_nguoi_moi
        d.tong_tien = tongTienMoi
        print("Cập nhật thành công")
        return True

    def huy_dat_tour(self, ma_dat):
        d = self.tim_dat_tour_theo_ma(ma_dat)
        if not d:
            print("Không tìm thấy đơn đặt tour")
            return False
        if self.nguoi_dung_hien_tai and self.nguoi_dung_hien_tai.vai_tro == "user":
            if d.ma_khach_hang != self.nguoi_dung_hien_tai.ma_khach_hang:
                print("Bạn không thể hủy đơn của người khác!")
                return False
        if d.trang_thai == "huy":
            print("Đơn đã bị hủy trước đó")
            return False
        kh = self.tim_khach_hang(d.ma_khach_hang)
        tour = self.tim_tour(d.ma_tour)
        if not kh or not tour:
            print("Lỗi dữ liệu: khách hàng hoặc tour không tồn tại")
            return False
        if self.trang_thai_tour(tour) == "dang_dien_ra":
            print("Không thể hủy đơn khi tour đang diễn ra")
            return False
        if self.trang_thai_tour(tour) == "da_hoan_thanh":
            print("Không thể hủy đơn khi tour đã hoàn thành")
            return False
        if d.trang_thai == "chua_thanh_toan":
            d.trang_thai = "huy"
            print("Hủy đơn chưa thanh toán (không hoàn tiền / không trả slot)")
            return True
        kh.so_du += d.tong_tien
        tour.so_cho += d.so_nguoi
        d.trang_thai = "huy"
        print("Hủy đơn đã thanh toán (đã hoàn tiền + trả slot)")
        return True

    def dang_xuat(self):
        self.nguoi_dung_hien_tai = None
        print("Đã đăng xuất")
