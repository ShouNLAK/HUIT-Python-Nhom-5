
import json
import sys
from pathlib import Path
from Class.tour import TourDuLich
from Class.khach_hang import KhachHang
from Class.dat_tour import DatTour


def _resolve_data_dir() -> Path:
    """Tìm đường dẫn Data phù hợp trong mọi chế độ chạy."""
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "Data")
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).parent / "Data")
    candidates.append(Path(__file__).resolve().parents[1] / "Data")
    for path in candidates:
        if path.exists():
            return path
    return candidates[-1]


DATA_DIR = _resolve_data_dir()

TOUR_FILE = DATA_DIR.joinpath("tours.json")
KH_FILE = DATA_DIR.joinpath("khachhang.json")
DAT_FILE = DATA_DIR.joinpath("dattour.json")
HDV_FILE = DATA_DIR.joinpath("hdv.json")
USERS_FILE = DATA_DIR.joinpath("users.json")


def tour_thanh_dict(tour: TourDuLich):
    def _norm_date(d):
        if not d:
            return None
        if isinstance(d, str):
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    return __import__('datetime').datetime.strptime(d, fmt).strftime('%d-%m-%Y')
                except Exception:
                    continue
            return d
        try:
            return d.strftime('%d-%m-%Y')
        except Exception:
            return str(d)
    return {
        "maTour": tour.ma_tour,
        "tenTour": tour.ten_tour,
        "gia": tour.gia_tour,
        "soCho": tour.so_cho,
        "lichTrinh": tour.lich_trinh,
        "huongDanVien": tour.huong_dan_vien,
        "ngayDi": _norm_date(getattr(tour, "ngay_di", None)),
        "ngayVe": _norm_date(getattr(tour, "ngay_ve", None)),
    }


def dict_thanh_tour(data):
    return TourDuLich(
        data.get("maTour"),
        data.get("tenTour"),
        data.get("gia", 0),
        data.get("soCho", 0),
        data.get("lichTrinh", []),
        data.get("huongDanVien", ""),
        data.get("ngayDi"),
        data.get("ngayVe"),
    )


def khach_hang_thanh_dict(kh: KhachHang):
    return {
        "maKH": kh.ma_khach_hang,
        "tenKH": kh.ten_khach_hang,
        "soDT": kh.so_dien_thoai,
        "email": kh.email,
        "soDu": kh.so_du,
    }


def dict_thanh_khach_hang(data):
    return KhachHang(
        data.get("maKH"),
        data.get("tenKH"),
        data.get("soDT", ""),
        data.get("email", ""),
        data.get("soDu", 0),
    )


def dat_thanh_dict(dat: DatTour):
    return {
        "maDat": dat.ma_dat_tour,
        "maKH": dat.ma_khach_hang,
        "maTour": dat.ma_tour,
        "soNguoi": dat.so_nguoi,
        "ngayDat": dat.ngay_dat,
        "trangThai": dat.trang_thai,
        "tongTien": dat.tong_tien,
    }


def dict_thanh_dat(data):
    return DatTour(
        data.get("maDat"),
        data.get("maKH"),
        data.get("maTour"),
        data.get("soNguoi", 1),
        data.get("ngayDat", ""),
        data.get("trangThai", "chua_thanh_toan"),
        data.get("tongTien", 0),
    )


def tai_danh_sach(file_path: Path, converter):
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            return [converter(item) for item in data]
    except Exception:
        return []


def luu_danh_sach(file_path: Path, data):
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def tai_tat_ca():
    tours = tai_danh_sach(TOUR_FILE, dict_thanh_tour)
    khs = tai_danh_sach(KH_FILE, dict_thanh_khach_hang)
    dats = tai_danh_sach(DAT_FILE, dict_thanh_dat)
    hdvs = tai_danh_sach(HDV_FILE, lambda item: item)
    def _dict_thanh_nguoi(data):
        from Class.user import NguoiDung

        return NguoiDung(
            data.get("tenDangNhap") or data.get("username"),
            data.get("matKhau") or data.get("password"),
            data.get("vaiTro") or data.get("role", "user"),
            data.get("maKH"),
            data.get("tenHienThi") or data.get("fullName"),
        )

    users = tai_danh_sach(USERS_FILE, _dict_thanh_nguoi)
    return tours, khs, dats, hdvs, users


def luu_tat_ca(ql):
    tours = [tour_thanh_dict(t) for t in ql.danh_sach_tour]
    khs = [khach_hang_thanh_dict(k) for k in ql.danh_sach_khach_hang]
    dats = [dat_thanh_dict(d) for d in ql.danh_sach_dat_tour]
    try:
        luu_danh_sach(TOUR_FILE, tours)
        luu_danh_sach(KH_FILE, khs)
        luu_danh_sach(DAT_FILE, dats)
        if hasattr(ql, "danh_sach_hdv"):
            luu_danh_sach(HDV_FILE, ql.danh_sach_hdv)
        def serialize_user(u):
            data = {
                "tenDangNhap": u.ten_dang_nhap,
                "matKhau": u.mat_khau,
                "vaiTro": u.vai_tro,
                "maKH": u.ma_khach_hang,
            }
            if u.vai_tro == "admin":
                data["tenHienThi"] = u.ten_hien_thi
            return data

        users = [serialize_user(u) for u in ql.danh_sach_nguoi_dung]
        luu_danh_sach(USERS_FILE, users)
        return True
    except Exception:
        return False
