class NguoiDung:
    def __init__(self, ten_dang_nhap, mat_khau, vai_tro="user", ma_khach_hang=None, ten_hien_thi=None):
        self.ten_dang_nhap = ten_dang_nhap
        self.mat_khau = mat_khau
        self.vai_tro = vai_tro
        self.ma_khach_hang = ma_khach_hang
        self.ten_hien_thi = ten_hien_thi or ten_dang_nhap
