import tkinter as tk
from Class.user import User
from QuanLy.quan_li_du_lich import QuanLiDuLich
from QuanLy.storage import tai_tat_ca, luu_tat_ca
from GUI import GiaoDienCoSo

def chay():
    ql = QuanLiDuLich()
    tours, khs, dats, hdvs, users = tai_tat_ca()
    ql.danhSachTour = tours
    ql.danhSachKhachHang = khs
    ql.danhSachDatTour = dats
    ql.danhSachHDV = hdvs
    ql.users = users
    if not ql.users:
        ql.users.append(User('admin', 'admin', 'admin'))
    goc = tk.Tk()
    GiaoDienCoSo(goc, ql)
    def dong():
        luu_tat_ca(ql)
        goc.destroy()
    goc.protocol('WM_DELETE_WINDOW', dong)
    goc.mainloop()

if __name__ == '__main__':
    chay()
