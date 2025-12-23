import tkinter as tk
from QuanLy.quan_li_du_lich import QuanLiDuLich
from QuanLy.storage import tai_tat_ca, luu_tat_ca
from GUI import GiaoDienCoSo

def chay():
    ql = QuanLiDuLich()
    tours, khs, dats, hdvs, users = tai_tat_ca()
    ql.danh_sach_tour = tours
    ql.danh_sach_khach_hang = khs
    ql.danh_sach_dat_tour = dats
    ql.danh_sach_hdv = hdvs
    ql.danh_sach_nguoi_dung = users or []
    ql.danh_sach_nap_tien = []
    # Đồng bộ trạng thái đơn: hủy các đơn chờ nếu tour đang diễn ra/đã hoàn thành
    try:
        ql.dong_bo_trang_thai_dat_theo_tour(save=True)
    except Exception:
        pass
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
