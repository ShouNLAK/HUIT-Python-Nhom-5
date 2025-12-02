import tkinter as tk
from QuanLy.quan_li_du_lich import QuanLiDuLich
from QuanLy.storage import tai_tat_ca, luu_tat_ca
from GUI import GiaoDienCoSo

def chay():
    ql = QuanLiDuLich()
    tours, khs, dats, hdvs, users, nap_tiens = tai_tat_ca()
    ql.danhSachTour = tours
    ql.danhSachKhachHang = khs
    ql.danhSachDatTour = dats
    ql.danhSachHDV = hdvs
    ql.users = users or []
    ql.danhSachNapTien = nap_tiens or []
    ql.set_auto_save(lambda: luu_tat_ca(ql))
    ql.ensure_default_accounts()
    ql.dong_bo_tai_khoan_lien_ket()
    ql.khoi_dong_webhook_server()
    goc = tk.Tk()
    GiaoDienCoSo(goc, ql)
    def dong():
        luu_tat_ca(ql)
        ql.dung_webhook_nap_tien()
        goc.destroy()
    goc.protocol('WM_DELETE_WINDOW', dong)
    goc.mainloop()

if __name__ == '__main__':
    chay()
