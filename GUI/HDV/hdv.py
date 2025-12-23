import tkinter as tk
from tkinter import messagebox, ttk
from GUI.Login.base import GiaoDienCoSo


def hdv_xem_khach(self):
    sel = self.tv_tour.selection()
    if not sel:
        messagebox.showerror('Lỗi', 'Chưa chọn tour')
        return
    item = sel[0]
    values = self.tv_tour.item(item, 'values')
    ma = values[0]
    ds = [d for d in self.ql.danh_sach_dat_tour if d.ma_tour == ma and d.trang_thai == 'da_thanh_toan']
    if not ds:
        messagebox.showinfo('Khách', 'Chưa có khách đã thanh toán')
        return
    top, container = self.create_modal('Khách đã thanh toán', size=(520, 380))
    tv = ttk.Treeview(container, columns=('ma_khach_hang', 'ten', 'sdt', 'so_nguoi'), show='headings')
    for col, text in (('ma_khach_hang', 'Mã KH'), ('ten', 'Tên'), ('sdt', 'SĐT'), ('so_nguoi', 'Số người')):
        tv.heading(col, text=text)
        tv.column(col, width=120 if col != 'ten' else 160, anchor='center' if col != 'ten' else 'w')
    scr = ttk.Scrollbar(container, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    for d in ds:
        kh = self.ql.tim_khach_hang(d.ma_khach_hang)
        name = kh.ten_khach_hang if kh else d.ma_khach_hang
        tv.insert('', tk.END, values=(d.ma_khach_hang, name, getattr(kh, 'so_dien_thoai', ''), d.so_nguoi))
    self.apply_zebra(tv)


def hdv_xem_lich_trinh(self):
    sel = self.tv_tour.selection()
    if not sel:
        messagebox.showerror('Lỗi', 'Chưa chọn tour')
        return
    item = sel[0]
    values = self.tv_tour.item(item, 'values')
    ma = values[0]
    t = self.ql.tim_tour(ma)
    if not t:
        messagebox.showerror('Lỗi', 'Không tìm thấy tour')
        return
    top, container = self.create_modal('Lịch trình chi tiết', size=(640, 420))
    tv = ttk.Treeview(container, columns=('ngay', 'dia_diem', 'mo_ta', 'phuong_tien'), show='headings')
    for col, text, w in (
        ('ngay', 'Ngày', 110),
        ('dia_diem', 'Địa điểm', 160),
        ('mo_ta', 'Mô tả', 220),
        ('phuong_tien', 'Phương tiện', 120),
    ):
        tv.heading(col, text=text)
        tv.column(col, width=w, anchor='center' if col == 'ngay' else 'w')
    scr = ttk.Scrollbar(container, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    for l in t.lich_trinh:
        tv.insert('', tk.END, values=(l.get('ngay', ''), l.get('dia_diem', '') or '', l.get('mo_ta', '') or '', l.get('phuong_tien', '') or ''))
    self.apply_zebra(tv)


def update_hdv_right_panel(self, ma_tour):
    for w in self.context_body.winfo_children():
        w.destroy()
    t = self.ql.tim_tour(ma_tour)
    if not t:
        ttk.Label(self.context_body, text='Không tìm thấy tour', style='Body.TLabel').pack()
        return
    self.hdv_title.config(text=t.ten_tour)
    info = ttk.LabelFrame(self.context_body, text='Thông tin tour', style='Card.TLabelframe', padding=10)
    info.pack(fill='x', pady=(0, 12))
    ttk.Label(info, text=f"Mã: {t.ma_tour}", style='Body.TLabel').grid(row=0, column=0, sticky='w')
    ttk.Label(info, text=f"Giá: {self.format_money(t.gia_tour)}", style='Body.TLabel').grid(row=0, column=1, sticky='w', padx=12)
    ttk.Label(info, text=f"Số chỗ: {t.so_cho}", style='Body.TLabel').grid(row=0, column=2, sticky='w', padx=12)

    passengers = ttk.LabelFrame(self.context_body, text='Hành khách đã thanh toán', style='Card.TLabelframe', padding=10)
    passengers.pack(fill='x', pady=(0, 12))
    tv = ttk.Treeview(passengers, columns=('ma_khach_hang', 'ten', 'sdt', 'so_nguoi'), show='headings', height=4)
    for col, text, w in (
        ('ma_khach_hang', 'Mã KH', 80),
        ('ten', 'Tên', 150),
        ('sdt', 'SĐT', 120),
        ('so_nguoi', 'Số người', 90),
    ):
        tv.heading(col, text=text)
        tv.column(col, width=w, anchor='center' if col != 'ten' else 'w')
    scr = ttk.Scrollbar(passengers, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    paid = [d for d in self.ql.danh_sach_dat_tour if d.ma_tour == ma_tour and d.trang_thai == 'da_thanh_toan']
    for d in paid:
        kh = self.ql.tim_khach_hang(d.ma_khach_hang)
        tv.insert('', tk.END, values=(d.ma_khach_hang, kh.ten_khach_hang if kh else d.ma_khach_hang, getattr(kh, 'so_dien_thoai', ''), d.so_nguoi))
    self.apply_zebra(tv)

    schedule = ttk.LabelFrame(self.context_body, text='Lịch trình', style='Card.TLabelframe', padding=10)
    schedule.pack(fill='both', expand=True)
    cols = ('ngay', 'dia_diem', 'mo_ta', 'phuong_tien', 'nhiet_do')
    tv2 = ttk.Treeview(schedule, columns=cols, show='headings', height=6)
    settings = {
        'ngay': ('Ngày', 100, 'center'),
        'dia_diem': ('Địa điểm', 150, 'w'),
        'mo_ta': ('Mô tả', 200, 'w'),
        'phuong_tien': ('Phương tiện', 120, 'center'),
        'nhiet_do': ('Nhiệt độ', 110, 'center'),
    }
    for col in cols:
        text, width, anchor = settings[col]
        tv2.heading(col, text=text)
        tv2.column(col, width=width, anchor=anchor)
    scr2 = ttk.Scrollbar(schedule, orient='vertical', command=tv2.yview)
    tv2.configure(yscrollcommand=scr2.set)
    tv2.pack(side='left', fill='both', expand=True)
    scr2.pack(side='right', fill='y')
    for l in t.lich_trinh:
        ngay = l.get('ngay', '')
        dia = l.get('dia_diem', '') or ''
        mota = l.get('mo_ta', '') or ''
        phuong = l.get('phuong_tien', '') or ''
        tv2.insert('', tk.END, values=(ngay, dia, mota, phuong, '—'))
    self.apply_zebra(tv2)

    def _on_prefetch_hdv(iid, res):
        try:
            if not res or (isinstance(res, dict) and res.get('error')):
                return
            weather = res.get('weather')
            old = list(tv2.item(iid, 'values'))
            if weather:
                if isinstance(weather, dict) and 'min' in weather and 'max' in weather:
                    old[4] = f"{weather['min']}°C - {weather['max']}°C"
                elif isinstance(weather, dict) and 'current' in weather:
                    old[4] = f"{weather['current']}°C"
            tv2.item(iid, values=tuple(old))
        except Exception:
            pass

    for iid in tv2.get_children():
        vals = tv2.item(iid, 'values')
        place = vals[1]
        datev = vals[0]
        if place:
            self._run_async(self._fetch_place_preview, lambda r, _iid=iid: _on_prefetch_hdv(_iid, r), place, datev)


GiaoDienCoSo.hdv_xem_khach = hdv_xem_khach
GiaoDienCoSo.hdv_xem_lich_trinh = hdv_xem_lich_trinh
GiaoDienCoSo.update_hdv_right_panel = update_hdv_right_panel
