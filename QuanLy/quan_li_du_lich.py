from Class.user import User
from Class.tour import Tour
from Class.khach_hang import KhachHang
from Class.dat_tour import DatTour


class QuanLiDuLich:
    def __init__(self):
        self.danhSachTour = []
        self.danhSachKhachHang = []
        self.danhSachDatTour = []
        self.users = []
        self.currentUser = None

    def DangKyUser(self, username, password, role="user", maKH=None):
        for u in self.users:
            if u.username == username:
                print("Tên đăng nhập đã tồn tại")
                return False
        if role not in ["admin", "user"]:
            print("Vai trò không hợp lệ")
            return False
        if role == "user" and self.TimKhacHang(maKH) is None:
            print("Mã khách hàng không tồn tại!")
            return False
        self.users.append(User(username, password, role, maKH))
        print("Tạo tài khoản thành công")
        return True

    def Login(self, username, password):
        for u in self.users:
            if u.username == username and u.password == password:
                self.currentUser = u
                print(f"Đăng nhập thành công (vai trò: {u.role})")
                return True
        print("Sai tài khoản hoặc mật khẩu")
        return False

    def ThemKhachHang(self, kh: KhachHang):
        if not self.currentUser or self.currentUser.role != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        if not kh.maKH or not kh.tenKH:
            print("Mã khách hàng hoặc Tên khách hàng không được rỗng")
            return False
        if self.TimKhacHang(kh.maKH) is not None:
            print("Mã khách hàng đã tồn tại!")
            return False
        if not kh.soDT.isdigit() or len(kh.soDT) != 10:
            print("Số điện thoại không hợp lệ!")
            return False
        if "@" not in kh.email:
            print("Email không hợp lệ!")
            return False
        if kh.soDu < 0:
            print("Số dư không hợp lệ")
            return False
        self.danhSachKhachHang.append(kh)
        print("Thêm khách hàng thành công")
        return True

    def HienThiDanhSachKhachHang(self):
        if not self.currentUser:
            print("Bạn phải đăng nhập!")
            return []
        if self.currentUser.role == "admin":
            return self.danhSachKhachHang
        return [kh for kh in self.danhSachKhachHang if kh.maKH == self.currentUser.maKH]

    def TimKhacHang(self, maKH: str):
        for kh in self.danhSachKhachHang:
            if kh.maKH == maKH:
                return kh
        return None

    def CapNhatKhachHang(self, maKH=None, tenKH=None, soDT=None, email=None, soDu=None):
        if not self.currentUser or self.currentUser.role != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        kh = self.TimKhacHang(maKH)
        if kh is None:
            print("Khách hàng không tồn tại!")
            return False
        if tenKH is not None:
            kh.tenKH = tenKH
        if soDT is not None:
            if not soDT.isdigit() or len(soDT) != 10:
                print("Số điện thoại không hợp lệ!")
                return False
            kh.soDT = soDT
        if email is not None:
            if "@" not in email:
                print("Email không hợp lệ!")
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
        if getattr(tour, 'ngayDi', None) and getattr(tour, 'ngayVe', None):
            try:
                from datetime import datetime
                d1 = datetime.strptime(tour.ngayDi, '%Y-%m-%d')
                d2 = datetime.strptime(tour.ngayVe, '%Y-%m-%d')
                if d2 < d1:
                    print("Ngày kết thúc phải sau ngày khởi hành")
                    return False
            except Exception:
                print("Định dạng ngày không hợp lệ (YYYY-MM-DD)")
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

    def CapNhatTour(self, maTour=None, tenTour=None, gia=None, soCho=None, lichTrinh=None, huongDanVien=None):
        if not self.currentUser or self.currentUser.role != "admin":
            print("Bạn không có quyền thực hiện!")
            return False
        t = self.TimTour(maTour)
        if t is None:
            print("Tour không tồn tại!")
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
        if lichTrinh is not None:
            t.lichTrinh = lichTrinh
        if hasattr(self, 'ngayDi') and getattr(self, 'ngayDi') is not None:
            try:
                t.ngayDi = getattr(self, 'ngayDi')
            except Exception:
                pass
        if hasattr(self, 'ngayVe') and getattr(self, 'ngayVe') is not None:
            try:
                t.ngayVe = getattr(self, 'ngayVe')
            except Exception:
                pass
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
