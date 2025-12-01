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
    ds = [d for d in self.ql.danhSachDatTour if d.maTour == ma and d.trangThai == 'da_thanh_toan']
    if not ds:
        messagebox.showinfo('Khách', 'Chưa có khách đã thanh toán')
        return
    top, container = self.create_modal('Khách đã thanh toán', size=(520, 380))
    tv = ttk.Treeview(container, columns=('MaKH','Ten','SDT','SoNguoi'), show='headings')
    for col, text in (('MaKH','Mã KH'),('Ten','Tên'),('SDT','SĐT'),('SoNguoi','Số người')):
        tv.heading(col, text=text)
        tv.column(col, width=120 if col != 'Ten' else 160, anchor='center' if col != 'Ten' else 'w')
    scr = ttk.Scrollbar(container, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    for d in ds:
        kh = self.ql.TimKhacHang(d.maKH)
        name = kh.tenKH if kh else d.maKH
        tv.insert('', tk.END, values=(d.maKH, name, getattr(kh, 'soDT', ''), d.soNguoi))
    self.apply_zebra(tv)

def hdv_xem_lich_trinh(self):
    sel = self.tv_tour.selection()
    if not sel:
        messagebox.showerror('Lỗi', 'Chưa chọn tour')
        return
    item = sel[0]
    values = self.tv_tour.item(item, 'values')
    ma = values[0]
    t = self.ql.TimTour(ma)
    if not t:
        messagebox.showerror('Lỗi', 'Không tìm thấy tour')
        return
    top, container = self.create_modal('Lịch trình chi tiết', size=(640, 420))
    tv = ttk.Treeview(container, columns=('Ngay','DiaDiem','MoTa','PhuongTien'), show='headings')
    for col, text, w in (
        ('Ngay','Ngày',110),
        ('DiaDiem','Địa điểm',160),
        ('MoTa','Mô tả',220),
        ('PhuongTien','Phương tiện',120)):
        tv.heading(col, text=text)
        tv.column(col, width=w, anchor='center' if col == 'Ngay' else 'w')
    scr = ttk.Scrollbar(container, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    for l in t.lichTrinh:
        tv.insert('', tk.END, values=(l.get('ngay',''), l.get('diaDiem', l.get('dia_diem','')) or '', l.get('moTa', l.get('mo_ta','')) or '', l.get('phuongTien', l.get('phuong_tien','')) or ''))
    self.apply_zebra(tv)

def update_hdv_right_panel(self, maTour):
    for w in self.context_body.winfo_children():
        w.destroy()
    t = self.ql.TimTour(maTour)
    if not t:
        ttk.Label(self.context_body, text='Không tìm thấy tour', style='Body.TLabel').pack()
        return
    self.hdv_title.config(text=t.tenTour)
    info = ttk.LabelFrame(self.context_body, text='Thông tin tour', style='Card.TLabelframe', padding=10)
    info.pack(fill='x', pady=(0,12))
    ttk.Label(info, text=f"Mã: {t.maTour}", style='Body.TLabel').grid(row=0, column=0, sticky='w')
    ttk.Label(info, text=f"Giá: {self.format_money(t.gia)}", style='Body.TLabel').grid(row=0, column=1, sticky='w', padx=12)
    ttk.Label(info, text=f"Số chỗ: {t.soCho}", style='Body.TLabel').grid(row=0, column=2, sticky='w', padx=12)
    
    passengers = ttk.LabelFrame(self.context_body, text='Hành khách đã thanh toán', style='Card.TLabelframe', padding=10)
    passengers.pack(fill='x', pady=(0,12))
    tv = ttk.Treeview(passengers, columns=('MaKH','Ten','SDT','SoNguoi'), show='headings', height=4)
    for col, text, w in (
        ('MaKH','Mã KH',80),
        ('Ten','Tên',150),
        ('SDT','SĐT',120),
        ('SoNguoi','Số người',90)):
        tv.heading(col, text=text)
        tv.column(col, width=w, anchor='center' if col != 'Ten' else 'w')
    scr = ttk.Scrollbar(passengers, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    paid = [d for d in self.ql.danhSachDatTour if d.maTour == maTour and d.trangThai == 'da_thanh_toan']
    for d in paid:
        kh = self.ql.TimKhacHang(d.maKH)
        tv.insert('', tk.END, values=(d.maKH, kh.tenKH if kh else d.maKH, getattr(kh,'soDT',''), d.soNguoi))
    self.apply_zebra(tv)
    
    schedule = ttk.LabelFrame(self.context_body, text='Lịch trình', style='Card.TLabelframe', padding=10)
    schedule.pack(fill='both', expand=True)
    cols = ('Ngay','DiaDiem','MoTa','PhuongTien','NhietDo')
    tv2 = ttk.Treeview(schedule, columns=cols, show='headings', height=6)
    settings = {
        'Ngay': ('Ngày', 100, 'center'),
        'DiaDiem': ('Địa điểm', 150, 'w'),
        'MoTa': ('Mô tả', 200, 'w'),
        'PhuongTien': ('Phương tiện', 120, 'center'),
        'NhietDo': ('Nhiệt độ', 110, 'center')
    }
    for col in cols:
        text, width, anchor = settings[col]
        tv2.heading(col, text=text)
        tv2.column(col, width=width, anchor=anchor)
    scr2 = ttk.Scrollbar(schedule, orient='vertical', command=tv2.yview)
    tv2.configure(yscrollcommand=scr2.set)
    tv2.pack(side='left', fill='both', expand=True)
    scr2.pack(side='right', fill='y')
    for l in t.lichTrinh:
        ngay = l.get('ngay','')
        dia = l.get('diaDiem', l.get('dia_diem','')) or ''
        mota = l.get('moTa', l.get('mo_ta','')) or ''
        phuong = l.get('phuongTien', l.get('phuong_tien','')) or ''
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
