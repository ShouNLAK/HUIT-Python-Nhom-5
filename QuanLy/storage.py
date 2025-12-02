import json
from pathlib import Path
from Class.tour import Tour
from Class.khach_hang import KhachHang
from Class.dat_tour import DatTour
from Class.user import User

BASE_DIR = Path(__file__).parents[1]
DATA_DIR = BASE_DIR / "Data"

TOUR_FILE = DATA_DIR.joinpath("tours.json")
KH_FILE = DATA_DIR.joinpath("khachhang.json")
DAT_FILE = DATA_DIR.joinpath("dattour.json")
HDV_FILE = DATA_DIR.joinpath("hdv.json")
USERS_FILE = DATA_DIR.joinpath("users.json")


def tour_to_dict(tour: Tour):
    return {
        "maTour": tour.maTour,
        "tenTour": tour.tenTour,
        "gia": tour.gia,
        "soCho": tour.soCho,
        "lichTrinh": tour.lichTrinh,
        "huongDanVien": tour.huongDanVien,
        "ngayDi": getattr(tour, "ngayDi", None),
        "ngayVe": getattr(tour, "ngayVe", None),
    }


def dict_to_tour(data):
    return Tour(
        data.get("maTour"),
        data.get("tenTour"),
        data.get("gia", 0),
        data.get("soCho", 0),
        data.get("lichTrinh", []),
        data.get("huongDanVien", ""),
        data.get("ngayDi"),
        data.get("ngayVe"),
    )


def kh_to_dict(kh: KhachHang):
    return {
        "maKH": kh.maKH,
        "tenKH": kh.tenKH,
        "soDT": kh.soDT,
        "email": kh.email,
        "soDu": kh.soDu,
    }


def dict_to_kh(data):
    return KhachHang(
        data.get("maKH"),
        data.get("tenKH"),
        data.get("soDT", ""),
        data.get("email", ""),
        data.get("soDu", 0),
    )


def dat_to_dict(dat: DatTour):
    return {
        "maDat": dat.maDat,
        "maKH": dat.maKH,
        "maTour": dat.maTour,
        "soNguoi": dat.soNguoi,
        "ngayDat": dat.ngayDat,
        "trangThai": dat.trangThai,
        "tongTien": dat.tongTien,
    }


def dict_to_dat(data):
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
    tours = tai_danh_sach(TOUR_FILE, dict_to_tour)
    khs = tai_danh_sach(KH_FILE, dict_to_kh)
    dats = tai_danh_sach(DAT_FILE, dict_to_dat)
    hdvs = tai_danh_sach(HDV_FILE, lambda item: item)
    users = tai_danh_sach(
        USERS_FILE,
        lambda data: User(
            data.get("username"),
            data.get("password"),
            data.get("role", "user"),
            data.get("maKH"),
            data.get("fullName"),
        ),
    )
    return tours, khs, dats, hdvs, users


def luu_tat_ca(ql):
    tours = [tour_to_dict(t) for t in ql.danhSachTour]
    khs = [kh_to_dict(k) for k in ql.danhSachKhachHang]
    dats = [dat_to_dict(d) for d in ql.danhSachDatTour]
    try:
        luu_danh_sach(TOUR_FILE, tours)
        luu_danh_sach(KH_FILE, khs)
        luu_danh_sach(DAT_FILE, dats)
        if hasattr(ql, "danhSachHDV"):
            luu_danh_sach(HDV_FILE, ql.danhSachHDV)
        def serialize_user(u):
            data = {
                "username": u.username,
                "password": u.password,
                "role": u.role,
                "maKH": u.maKH,
            }
            if u.role == "admin":
                data["fullName"] = u.fullName
            return data

        users = [serialize_user(u) for u in ql.users]
        luu_danh_sach(USERS_FILE, users)
        return True
    except Exception:
        return False
