import base64
import hashlib
import re
from datetime import datetime
from Class.user import User
from Class.tour import Tour
from Class.khach_hang import KhachHang
from Class.dat_tour import DatTour


class QuanLiDuLich:
    ROOT_USERNAME_HASH = "4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2"
    ROOT_PASSWORD_HASH = "18885f27b5af9012df19e496460f9294d5ab76128824c6f993787004f6d9a7db"
    ROOT_USERNAME_TOKEN = "cm9vdC5zdXBlcnZpc29y"
    ROOT_DISPLAY_NAME = "Root Operator"
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "Admin@123"
    DEFAULT_ADMIN_NAME = "Quản trị viên"
    def __init__(self):
        self.danhSachTour = []
        self.danhSachKhachHang = []
        self.danhSachDatTour = []
        self.danhSachHDV = []
        self.users = []
        self.currentUser = None

    def _parse_date(self, value):
        if not value:
            return None
        try:
            return datetime.strptime(str(value).strip(), "%Y-%m-%d")
        except Exception:
            return None

    def _validate_date_window(self, ngayDi, ngayVe):
        start = self._parse_date(ngayDi) if ngayDi else None
        end = self._parse_date(ngayVe) if ngayVe else None
        if ngayDi and not start:
            return False, None, None, "Ngày đi không đúng định dạng (YYYY-MM-DD)"
        if ngayVe and not end:
            return False, None, None, "Ngày về không đúng định dạng (YYYY-MM-DD)"
        if start and end and end < start:
            return False, None, None, "Ngày về phải sau hoặc bằng ngày đi"
        return True, start, end, ""

    def _validate_lich_trinh(self, lichTrinh, start_date, end_date):
        if not lichTrinh:
            return True, ""
        if not isinstance(lichTrinh, list):
            return False, "Lịch trình phải là danh sách các chặng"
        if not (start_date and end_date):
            return False, "Cần thiết lập Ngày đi và Ngày về trước khi thêm lịch trình"
        previous = None
        for idx, entry in enumerate(lichTrinh, start=1):
            if not isinstance(entry, dict):
                return False, f"Mục lịch trình #{idx} không hợp lệ"
            ngay = entry.get("ngay")
            diem = (entry.get("diaDiem") or "").strip()
            if not ngay:
                return False, f"Mục lịch trình #{idx} thiếu ngày"
            ngay_dt = self._parse_date(ngay)
            if not ngay_dt:
                return False, f"Ngày ở mục #{idx} không đúng định dạng (YYYY-MM-DD)"
            if ngay_dt < start_date or ngay_dt > end_date:
                window = f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}"
                return False, f"Ngày {ngay} phải nằm trong khoảng {window}"
            if previous and ngay_dt < previous:
                return False, "Các mốc lịch trình phải được sắp xếp theo thứ tự thời gian"
            if not diem:
                return False, f"Mục lịch trình #{idx} thiếu địa điểm"
            previous = ngay_dt
        return True, ""

    def _expected_link_name(self, role, ma):
        if role == "user":
            kh = self.TimKhacHang(ma)
            if kh and kh.tenKH:
                return kh.tenKH.strip()
        elif role == "hdv":
            hdv = self.TimHDV(ma)
            if hdv and hdv.get("tenHDV"):
                return hdv.get("tenHDV").strip()
        return None

    def _sync_user_fullname(self, ma, role, new_name):
        if not new_name:
            return
        user = self.TimUserTheoMa(ma, [role])
        if user:
            user.fullName = new_name.strip()

    def DongBoTenTuKhach(self, maKH):
        ten = self._expected_link_name("user", maKH)
        if ten:
            self._sync_user_fullname(maKH, "user", ten)

    def DongBoTenTuHDV(self, maHDV):
        ten = self._expected_link_name("hdv", maHDV)
        if ten:
            self._sync_user_fullname(maHDV, "hdv", ten)

    def _sanitize_username_seed(self, seed, fallback="user"):
        cleaned = re.sub(r"[^a-z0-9]+", "", (seed or "").lower())
        return cleaned or fallback

    def _generate_unique_username(self, seed):
        base = self._sanitize_username_seed(seed)
        candidate = base
        counter = 1
        while self.TimUser(candidate):
            candidate = f"{base}{counter}"
            counter += 1
        return candidate

    def ensure_user_for_khach(self, kh: KhachHang, default_password="123"):
        if not kh or not kh.maKH:
            return None
        code = str(kh.maKH).strip()
        existing = self.TimUserTheoMa(code, ["user"])
        if existing:
            existing.fullName = kh.tenKH
            return existing.username
        username = self._generate_unique_username(code)
        self.users.append(User(username, default_password, "user", code, kh.tenKH))
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
        existing = self.TimUserTheoMa(ma, ["hdv"])
        if existing:
            existing.fullName = ten or existing.fullName
            return existing.username
        username = self._generate_unique_username(ma)
        self.users.append(User(username, default_password, "hdv", ma, ten or username))
        return username

    def dong_bo_tai_khoan_lien_ket(self):
        for kh in self.danhSachKhachHang:
            self.ensure_user_for_khach(kh)
        for hdv in getattr(self, "danhSachHDV", []) or []:
            self.ensure_user_for_hdv(hdv)
        def is_valid(u):
            if u.role == "admin" or u.role == "root":
                return True
            if u.role == "user":
                return self.TimKhacHang(u.maKH) is not None
            if u.role == "hdv":
                return self.TimHDV(u.maKH) is not None
            return False
        self.users = [u for u in self.users if is_valid(u)]

    def _hash_value(self, value):
        if value is None:
            return ""
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _decode_token(self, token):
        try:
            return base64.b64decode(token.encode("utf-8")).decode("utf-8")
        except Exception:
            return ""

    def _root_username(self):
        name = self._decode_token(self.ROOT_USERNAME_TOKEN)
        return name or "root"

    def _build_root_user(self):
        return User(self._root_username(), "", "root", None, self.ROOT_DISPLAY_NAME)

    def _validate_username(self, username):
        if not username:
            return False
        return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{4,31}", username))

    def _validate_password(self, password, allow_default=False):
        if allow_default and password == "123":
            return True
        if not password or len(password) < 4 or len(password) > 64:
            return False
        return not re.search(r"\s", password)

    def _validate_fullname(self, fullname):
        if not fullname:
            return False
        stripped = fullname.strip()
        if len(stripped) < 3 or len(stripped) > 80:
            return False
        return True

    def TimUser(self, username):
        return next((u for u in self.users if u.username == username), None)

    def TimUserTheoMa(self, ma, allowed_roles=None):
        if ma is None:
            return None
        target = str(ma)
        for u in self.users:
            if str(u.maKH) == target and (not allowed_roles or u.role in allowed_roles):
                return u
        return None

    def DemSoAdmin(self):
        return sum(1 for u in self.users if u.role == "admin")

    def ResetMatKhau(self, username, new_password):
        user = self.TimUser(username)
        if not user:
            return False, "Không tìm thấy tài khoản"
        if not self._validate_password(new_password, allow_default=True):
            return False, "Mật khẩu không hợp lệ"
        user.password = new_password
        return True, "Đã đặt lại mật khẩu"

    def ensure_default_accounts(self):
        if not any(u.role == "admin" for u in self.users):
            admin = User(
                self.DEFAULT_ADMIN_USERNAME,
                self.DEFAULT_ADMIN_PASSWORD,
                "admin",
                None,
                self.DEFAULT_ADMIN_NAME,
            )
            if not self.TimUser(admin.username):
                self.users.append(admin)

    def tao_ma_khach_tu_dong(self):
        existing = []
        for k in self.danhSachKhachHang:
            if k.maKH and k.maKH.upper().startswith("KH"):
                tail = k.maKH.upper().replace("KH", "", 1)
                if tail.isdigit():
                    existing.append(int(tail))
        next_id = (max(existing) + 1) if existing else 1
        return f"KH{str(next_id).zfill(3)}"

    def DangKyUser(self, username, password, role="user", maKH=None, fullName=None):
        username = (username or "").strip()
        password = password or ""
        role = (role or "user").lower()
        if not self._validate_username(username):
            return False, "Tên đăng nhập phải dài tối thiểu 5 ký tự và không chứa khoảng trắng"
        if self.TimUser(username):
            return False, "Tên đăng nhập đã tồn tại"
        if role not in ["admin", "user", "hdv"]:
            return False, "Vai trò không hợp lệ"
        link_code = maKH
        if role in ("user", "hdv"):
            if not link_code:
                return False, "Thiếu mã liên kết"
            if role == "user" and self.TimKhacHang(link_code) is None:
                return False, "Mã khách hàng không tồn tại"
            if role == "hdv" and self.TimHDV(link_code) is None:
                return False, "Mã HDV không tồn tại"
            if self.TimUserTheoMa(link_code, [role]):
                return False, "Mã liên kết đã có tài khoản"
        else:
            link_code = None
        if not self._validate_password(password):
            return False, "Mật khẩu phải từ 4 đến 64 ký tự và không có khoảng trắng"
        provided_fullname = (fullName or "").strip()
        if role in ("user", "hdv"):
            expected_name = self._expected_link_name(role, link_code)
            if not expected_name or not self._validate_fullname(expected_name):
                return False, "Tên hiển thị của thông tin liên kết không hợp lệ"
            if provided_fullname and provided_fullname != expected_name:
                return False, "Họ tên tài khoản phải trùng với tên đã đăng ký"
            display_name = expected_name
        else:
            display_name = provided_fullname or username
            if not self._validate_fullname(display_name):
                return False, "Họ tên hiển thị không hợp lệ"
        self.users.append(User(username, password, role, link_code, display_name))
        return True, "Tạo tài khoản thành công"

    def Login(self, username, password):
        user_input = (username or "").strip()
        pwd_input = password or ""
        if self._hash_value(user_input) == self.ROOT_USERNAME_HASH and self._hash_value(pwd_input) == self.ROOT_PASSWORD_HASH:
            self.currentUser = self._build_root_user()
            print("Đăng nhập thành công (vai trò: root)")
            return True
        for u in self.users:
            if u.username == user_input and u.password == pwd_input:
                self.currentUser = u
                print(f"Đăng nhập thành công (vai trò: {u.role})")
                return True
        print("Sai tài khoản hoặc mật khẩu")
        return False

    def ThemKhachHang(self, kh: KhachHang, allow_public=False, auto_link_account=True):
        if not allow_public and (not self.currentUser or self.currentUser.role != "admin"):
            print("Bạn không có quyền thực hiện!")
            return False
        ma = (kh.maKH or "").strip().upper()
        ten = (kh.tenKH or "").strip()
        if not re.fullmatch(r"KH\d{3,}", ma):
            print("Mã khách hàng phải theo định dạng KH###")
            return False
        if not self._validate_fullname(ten):
            print("Tên khách không hợp lệ")
            return False
        if self.TimKhacHang(ma) is not None:
            print("Mã khách hàng đã tồn tại!")
            return False
        phone = (kh.soDT or "").strip()
        if not phone.isdigit() or len(phone) != 10:
            print("Số điện thoại không hợp lệ!")
            return False
        if any(existing.soDT == phone for existing in self.danhSachKhachHang):
            print("Số điện thoại đã tồn tại")
            return False
        email = (kh.email or "").strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            print("Email không hợp lệ!")
            return False
        if any(existing.email.lower() == email for existing in self.danhSachKhachHang if existing.email):
            print("Email đã được sử dụng")
            return False
        if kh.soDu < 0:
            print("Số dư không hợp lệ")
            return False
        kh.maKH = ma
        kh.tenKH = ten
        kh.soDT = phone
        kh.email = email
        self.danhSachKhachHang.append(kh)
        self.DongBoTenTuKhach(kh.maKH)
        if auto_link_account:
            self.ensure_user_for_khach(kh)
        print("Thêm khách hàng thành công")
        return True

    def HienThiDanhSachKhachHang(self):
        if not self.currentUser:
            print("Bạn phải đăng nhập!")
            return []
        if self.currentUser.role == "admin":
            return self.danhSachKhachHang
        return [kh for kh in self.danhSachKhachHang if kh.maKH == self.currentUser.maKH]

    def TimHDV(self, maHDV: str):
        if not hasattr(self, "danhSachHDV"):
            self.danhSachHDV = []
        for hdv in self.danhSachHDV:
            if str(hdv.get("maHDV")) == str(maHDV):
                return hdv
        return None

    def TimKhacHang(self, maKH: str):
        for kh in self.danhSachKhachHang:
            if kh.maKH == maKH:
                return kh
        return None

    def LayTenHienThi(self, user: User):
        if not user:
            return ""
        if user.role == "root":
            return self.ROOT_DISPLAY_NAME
        if user.role == "user" and user.maKH:
            kh = self.TimKhacHang(user.maKH)
            return kh.tenKH if kh else user.fullName
        if user.role == "hdv" and user.maKH:
            hdv = self.TimHDV(user.maKH)
            return hdv.get("tenHDV") if hdv else user.fullName
        return user.fullName

    def LayDanhSachAdmin(self):
        return [u for u in self.users if u.role == "admin"]

    def CapNhatAdmin(self, username, fullName=None, password=None):
        admin = self.TimUser(username)
        if not admin or admin.role != "admin":
            return False, "Không tìm thấy tài khoản admin"
        if fullName is not None:
            if not self._validate_fullname(fullName):
                return False, "Họ tên không hợp lệ"
            admin.fullName = fullName.strip()
        if password is not None:
            if not self._validate_password(password):
                return False, "Mật khẩu không hợp lệ"
            admin.password = password
        return True, "Đã cập nhật"

    def XoaAdmin(self, username):
        admin = self.TimUser(username)
        if not admin or admin.role != "admin":
            return False, "Không tìm thấy tài khoản admin"
        if self.DemSoAdmin() <= 1:
            return False, "Cần ít nhất một tài khoản admin"
        self.users = [u for u in self.users if u.username != username]
        return True, "Đã xóa admin"

    def ResetMatKhauTheoMa(self, ma, role, default_password="123"):
        user = self.TimUserTheoMa(ma, [role])
        if not user:
            return False, "Không tìm thấy tài khoản"
        if not self._validate_password(default_password, allow_default=True):
            return False, "Mật khẩu mặc định không hợp lệ"
        user.password = default_password
        return True, "Đã đặt lại mật khẩu"

    def CapNhatKhachHang(self, maKH=None, tenKH=None, soDT=None, email=None, soDu=None):
        if not self.currentUser or self.currentUser.role != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        kh = self.TimKhacHang(maKH)
        if kh is None:
            print("Khách hàng không tồn tại!")
            return False
        if tenKH is not None:
            if not self._validate_fullname(tenKH):
                print("Tên khách không hợp lệ")
                return False
            kh.tenKH = tenKH.strip()
            self.DongBoTenTuKhach(kh.maKH)
            self.ensure_user_for_khach(kh)
        if soDT is not None:
            if not soDT.isdigit() or len(soDT) != 10:
                print("Số điện thoại không hợp lệ!")
                return False
            if any(other.soDT == soDT and other.maKH != kh.maKH for other in self.danhSachKhachHang):
                print("Số điện thoại đã được sử dụng")
                return False
            kh.soDT = soDT
        if email is not None:
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                print("Email không hợp lệ!")
                return False
            if any((other.email or "").lower() == email.lower() and other.maKH != kh.maKH for other in self.danhSachKhachHang):
                print("Email đã được sử dụng")
                return False
            kh.email = email
        if soDu is not None:
            if soDu < 0:
                print("Số dư không hợp lệ!")
                return False
            kh.soDu = soDu
        print("Cập nhật thành công")
        return True

    def XoaKhachHang(self, maKH):
        if not self.currentUser or self.currentUser.role != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        kh = self.TimKhacHang(maKH)
        if kh is None:
            print("Khách hàng không tồn tại")
            return False
        for dt in self.danhSachDatTour:
            if dt.maKH == maKH and dt.trangThai == "da_thanh_toan":
                print("Không thể xóa! Khách hàng còn đơn đã thanh toán!")
                return False
        self.danhSachKhachHang = [k for k in self.danhSachKhachHang if k.maKH != maKH]
        self.users = [u for u in self.users if not (u.maKH == maKH and u.role == "user")]
        print("Xóa khách hàng thành công")
        return True

    def ThemTour(self, tour: Tour):
        if not self.currentUser or self.currentUser.role != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        if not tour.maTour:
            print("Mã tour trống")
            return False
        if self.TimTour(tour.maTour):
            print("Mã tour đã tồn tại!")
            return False
        if tour.gia <= 0:
            print("Giá tour không hợp lệ")
            return False
        if tour.soCho < 1:
            print("Số chỗ phải >= 1")
            return False
        ngay_di = getattr(tour, "ngayDi", None)
        ngay_ve = getattr(tour, "ngayVe", None)
        ok, start, end, msg = self._validate_date_window(ngay_di, ngay_ve)
        if not ok:
            print(msg)
            return False
        ok, msg = self._validate_lich_trinh(getattr(tour, "lichTrinh", []), start, end)
        if not ok:
            print(msg)
            return False
        self.danhSachTour.append(tour)
        print("Thêm tour thành công")
        return True

    def HienThiDanhSachTour(self):
        return self.danhSachTour

    def TimTour(self, maTour: str):
        for t in self.danhSachTour:
            if t.maTour == maTour:
                return t
        return None

    def CapNhatTour(self, maTour=None, tenTour=None, gia=None, soCho=None, lichTrinh=None, huongDanVien=None, ngayDi=None, ngayVe=None):
        if not self.currentUser or self.currentUser.role != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        t = self.TimTour(maTour)
        if t is None:
            print("Tour không tồn tại!")
            return False
        new_ngay_di = ngayDi if ngayDi is not None else getattr(t, "ngayDi", None)
        new_ngay_ve = ngayVe if ngayVe is not None else getattr(t, "ngayVe", None)
        schedule = lichTrinh if lichTrinh is not None else t.lichTrinh
        ok, start, end, msg = self._validate_date_window(new_ngay_di, new_ngay_ve)
        if not ok:
            print(msg)
            return False
        ok, msg = self._validate_lich_trinh(schedule, start, end)
        if not ok:
            print(msg)
            return False
        if tenTour is not None:
            t.tenTour = tenTour
        if gia is not None:
            if gia <= 0:
                print("Giá không hợp lệ")
                return False
            t.gia = gia
        if soCho is not None:
            if soCho < 1:
                print("Số chỗ phải >=1")
                return False
            t.soCho = soCho
        t.lichTrinh = schedule
        t.ngayDi = new_ngay_di
        t.ngayVe = new_ngay_ve
        if huongDanVien is not None:
            t.huongDanVien = huongDanVien
        print("Cập nhật tour thành công")
        return True

    def XoaTour(self, maTour):
        if not self.currentUser or self.currentUser.role != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        t = self.TimTour(maTour)
        if t is None:
            print("Tour không tồn tại")
            return False
        for dt in self.danhSachDatTour:
            if dt.maTour == maTour and dt.trangThai == "da_thanh_toan":
                print("Không thể xóa! Tour đã có người đặt và thanh toán!")
                return False
        self.danhSachTour = [tour for tour in self.danhSachTour if tour.maTour != maTour]
        print("Xóa tour thành công")
        return True

    def DatTourMoi(self, dat: DatTour):
        if self.currentUser and self.currentUser.role == "user":
            dat.maKH = self.currentUser.maKH
        kh = self.TimKhacHang(dat.maKH)
        t = self.TimTour(dat.maTour)
        if any(d.maDat == dat.maDat for d in self.danhSachDatTour):
            print("Mã đặt tour đã tồn tại!")
            return False
        if not kh:
            print("Khách hàng không tồn tại")
            return False
        if not t:
            print("Tour không tồn tại")
            return False
        if dat.soNguoi <= 0:
            print("Số người phải >= 1")
            return False
        if dat.soNguoi > t.soCho:
            print("Không đủ chỗ")
            return False
        dat.tongTien = dat.soNguoi * t.gia
        if kh.soDu < dat.tongTien:
            print("Không đủ số dư")
            return False
        kh.soDu -= dat.tongTien
        t.soCho -= dat.soNguoi
        dat.trangThai = "da_thanh_toan"
        self.danhSachDatTour.append(dat)
        print("Đặt tour thành công")
        return True

    def HienThiDanhSachDatTour(self):
        if not self.currentUser:
            print("Bạn phải đăng nhập!")
            return []
        if self.currentUser.role == "admin":
            return self.danhSachDatTour
        return [d for d in self.danhSachDatTour if d.maKH == self.currentUser.maKH]

    def TimDatTourTheoMa(self, maDat):
        d = next((x for x in self.danhSachDatTour if x.maDat == maDat), None)
        if not d:
            return None
        if self.currentUser and self.currentUser.role == "user" and d.maKH != self.currentUser.maKH:
            print("Bạn không thể xem đơn của người khác!")
            return None
        return d

    def TimDatTourTheoKhach(self, maKH):
        if not self.currentUser:
            print("Bạn phải đăng nhập!")
            return []
        if self.currentUser.role == "admin":
            return [d for d in self.danhSachDatTour if d.maKH == maKH]
        if maKH != self.currentUser.maKH:
            print("Bạn không thể xem đơn của người khác!")
            return []
        return [d for d in self.danhSachDatTour if d.maKH == maKH]

    def CapNhatDatTour(self, maDat, maTour=None, soNguoi=None):
        if not self.currentUser or self.currentUser.role != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        d = self.TimDatTourTheoMa(maDat)
        if not d:
            print("Không tìm thấy đơn")
            return False
        if d.trangThai != "da_thanh_toan":
            print("Chỉ cập nhật đơn đã thanh toán")
            return False
        if (maTour is None or maTour == d.maTour) and (soNguoi is None or soNguoi == d.soNguoi):
            print("Không có dữ liệu cần cập nhật")
            return True
        kh = self.TimKhacHang(d.maKH)
        tourCu = self.TimTour(d.maTour)
        tourMoi = self.TimTour(maTour) if maTour else tourCu
        if not tourMoi:
            print("Tour mới không tồn tại")
            return False
        soNguoiMoi = soNguoi if soNguoi is not None else d.soNguoi
        if soNguoiMoi <= 0:
            print("Số người phải >= 1")
            return False
        if tourMoi.maTour == tourCu.maTour:
            soChoKhaDung = tourCu.soCho + d.soNguoi
        else:
            soChoKhaDung = tourMoi.soCho
        if soNguoiMoi > soChoKhaDung:
            print("Không đủ chỗ")
            return False
        tongTienMoi = soNguoiMoi * tourMoi.gia
        if tongTienMoi > (kh.soDu + d.tongTien):
            print("Không đủ số dư")
            return False
        tourCu.soCho += d.soNguoi
        kh.soDu += d.tongTien
        tourMoi.soCho -= soNguoiMoi
        kh.soDu -= tongTienMoi
        d.maTour = tourMoi.maTour
        d.soNguoi = soNguoiMoi
        d.tongTien = tongTienMoi
        print("Cập nhật thành công")
        return True

    def HuyDatTour(self, maDat):
        d = self.TimDatTourTheoMa(maDat)
        if not d:
            print("Không tìm thấy đơn đặt tour")
            return False
        if self.currentUser and self.currentUser.role == "user":
            if d.maKH != self.currentUser.maKH:
                print("Bạn không thể hủy đơn của người khác!")
                return False
        if d.trangThai == "huy":
            print("Đơn đã bị hủy trước đó")
            return False
        kh = self.TimKhacHang(d.maKH)
        tour = self.TimTour(d.maTour)
        if not kh or not tour:
            print("Lỗi dữ liệu: khách hàng hoặc tour không tồn tại")
            return False
        if d.trangThai == "chua_thanh_toan":
            d.trangThai = "huy"
            print("Hủy đơn chưa thanh toán (không hoàn tiền / không trả slot)")
            return True
        kh.soDu += d.tongTien
        tour.soCho += d.soNguoi
        d.trangThai = "huy"
        print("Hủy đơn đã thanh toán (đã hoàn tiền + trả slot)")
        return True

    def Logout(self):
        self.currentUser = None
        print("Đã đăng xuất")
