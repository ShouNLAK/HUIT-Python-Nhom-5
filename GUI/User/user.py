import tkinter as tk
from tkinter import messagebox, ttk
from Class.dat_tour import DatTour
from QuanLy.storage import luu_tat_ca
from GUI.Login.base import GiaoDienCoSo

def nap_tien(self):
    if not self.ql.currentUser or self.ql.currentUser.role != 'user':
        messagebox.showerror('Lỗi', 'Chức năng chỉ dành cho khách hàng')
        return
    top, container = self.create_modal('Nạp tiền')
    form = ttk.Frame(container)
    form.pack(fill='x')
    entries = self.build_form_fields(form, [{'name':'sotien','label':'Số tiền cần nạp'}])
    def ok():
        try:
            so = float(entries['sotien'].get())
            if so <= 0:
                raise Exception()
        except Exception:
            messagebox.showerror('Lỗi', 'Số tiền không hợp lệ')
            return
        kh = self.ql.TimKhacHang(self.ql.currentUser.maKH)
        if not kh:
            messagebox.showerror('Lỗi', 'Khách hàng không tồn tại')
            return
        kh.soDu += so
        luu_tat_ca(self.ql)
        self.hien_thi_khach_user()
        self.refresh_lists()
        messagebox.showinfo('Thông báo', f'Nạp {so} thành công')
        top.destroy()
    self.modal_buttons(container, [
        {'text':'Nạp tiền', 'style':'Accent.TButton', 'command':ok},
        {'text':'Đóng', 'style':'Danger.TButton', 'command':top.destroy}
    ])

def xem_don_user(self):
    if not self.ql.currentUser:
        messagebox.showerror('Lỗi', 'Bạn cần đăng nhập')
        return
    ds = [d for d in self.ql.danhSachDatTour if d.maKH == self.ql.currentUser.maKH]
    if not ds:
        messagebox.showinfo('Đơn của tôi', 'Không có đơn')
        return
    top, container = self.create_modal('Đơn của tôi', size=(780, 500))
    ttk.Label(container, text='Danh sách đơn đặt tour của bạn', style='Title.TLabel').pack(anchor='w', pady=(0,12))
    list_frame = ttk.Frame(container)
    list_frame.pack(fill='both', expand=True)
    tv = ttk.Treeview(list_frame, columns=('MaDat','MaTour','SoNguoi','TrangThai','Tong'), show='headings')
    for col, text, w in (('MaDat','Mã đặt',120),('MaTour','Mã tour',120),('SoNguoi','Số người',90),('TrangThai','Trạng thái',140),('Tong','Tổng tiền',140)):
        tv.heading(col, text=text)
        tv.column(col, width=w, anchor='center')
    scr = ttk.Scrollbar(list_frame, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    for d in ds:
        status_display = 'Đã thanh toán' if d.trangThai == 'da_thanh_toan' else 'Chưa thanh toán'
        tv.insert('', tk.END, values=(d.maDat, d.maTour, d.soNguoi, status_display, self.format_money(d.tongTien)))
    self.apply_zebra(tv)
    btn_bar = ttk.Frame(container, padding=(0,12,0,0))
    btn_bar.pack(fill='x')
    def thanh_toan_don():
        sel = tv.selection()
        if not sel:
            messagebox.showwarning('Chú ý', 'Chọn một đơn để thanh toán')
            return
        vals = tv.item(sel[0], 'values')
        ma_dat = vals[0]
        dt = next((d for d in self.ql.danhSachDatTour if d.maDat == ma_dat), None)
        if not dt:
            messagebox.showerror('Lỗi', 'Không tìm thấy đơn')
            return
        if dt.trangThai == 'da_thanh_toan':
            messagebox.showinfo('Thông báo', 'Đơn này đã được thanh toán')
            return
        kh = self.ql.TimKhacHang(self.ql.currentUser.maKH)
        if not kh:
            messagebox.showerror('Lỗi', 'Không tìm thấy khách hàng')
            return
        if kh.soDu < dt.tongTien:
            messagebox.showerror('Lỗi', f'Số dư không đủ. Cần {self.format_money(dt.tongTien)}, hiện có {self.format_money(kh.soDu)}')
            return
        if messagebox.askyesno('Xác nhận', f'Thanh toán {self.format_money(dt.tongTien)} cho đơn {ma_dat}?'):
            kh.soDu -= dt.tongTien
            dt.trangThai = 'da_thanh_toan'
            luu_tat_ca(self.ql)
            messagebox.showinfo('Thành công', 'Thanh toán thành công!')
            self.refresh_lists()
            tv.item(sel[0], values=(dt.maDat, dt.maTour, dt.soNguoi, 'Đã thanh toán', self.format_money(dt.tongTien)))
    def huy_don():
        sel = tv.selection()
        if not sel:
            messagebox.showwarning('Chú ý', 'Chọn một đơn để hủy')
            return
        vals = tv.item(sel[0], 'values')
        ma_dat = vals[0]
        if messagebox.askyesno('Xác nhận', f'Hủy đơn {ma_dat}?'):
            if self.ql.HuyDatTour(ma_dat):
                luu_tat_ca(self.ql)
                tv.delete(sel[0])
                messagebox.showinfo('Thông báo', 'Đã hủy đơn')
                self.refresh_lists()
    ttk.Button(btn_bar, text='Thanh toán đơn đã chọn', style='Accent.TButton', command=thanh_toan_don).pack(side='left', padx=4)
    ttk.Button(btn_bar, text='Hủy đơn', style='Danger.TButton', command=huy_don).pack(side='left', padx=4)
    ttk.Button(btn_bar, text='Đóng', style='App.TButton', command=top.destroy).pack(side='left', padx=4)

def book_selected_tour_for_user(self):
    sel = self.tv_tour.selection()
    if not sel:
        messagebox.showerror('Lỗi', 'Chưa chọn tour để đặt')
        return
    item = sel[0]
    maTour = self.tv_tour.item(item, 'values')[0]
    if not self.ql.currentUser or self.ql.currentUser.role != 'user':
        messagebox.showerror('Lỗi', 'Chức năng dành cho khách hàng đăng nhập')
        return
    tour = self.ql.TimTour(maTour)
    if not tour:
        messagebox.showerror('Lỗi', 'Không tìm thấy tour')
        return
    top, container = self.create_modal('Đặt tour', size=(520, 400))
    ttk.Label(container, text=f'Đặt tour: {tour.tenTour}', style='Title.TLabel').pack(anchor='w')
    ttk.Label(container, text=f'Giá: {self.format_money(tour.gia)} / người', style='Body.TLabel').pack(anchor='w', pady=(4,12))
    form = ttk.Frame(container)
    form.pack(fill='x')
    ttk.Label(form, text='Mã tour', style='Form.TLabel').grid(row=0, column=0, sticky='w')
    e1 = ttk.Entry(form, font=self.font_body)
    e1.insert(0, maTour)
    e1.configure(state='readonly')
    e1.grid(row=0, column=1, sticky='ew', padx=(12,0))
    ttk.Label(form, text='Số người', style='Form.TLabel').grid(row=1, column=0, sticky='w', pady=(8,0))
    qty_var = tk.StringVar()
    e2 = ttk.Entry(form, font=self.font_body, textvariable=qty_var)
    e2.grid(row=1, column=1, sticky='ew', padx=(12,0), pady=(8,0))
    total_var = tk.StringVar(value='0 VND')
    ttk.Label(form, text='Tổng thanh toán', style='Form.TLabel').grid(row=2, column=0, sticky='w', pady=(8,0))
    total_label = ttk.Label(form, textvariable=total_var, style='BodyBold.TLabel')
    total_label.grid(row=2, column=1, sticky='w', pady=(8,0))
    form.columnconfigure(1, weight=1)
    def update_total(*args):
        try:
            so = int(qty_var.get())
            if so <= 0:
                raise ValueError
            total = so * tour.gia
            total_var.set(self.format_money(total))
        except Exception:
            total_var.set('0 VND')
    qty_var.trace_add('write', lambda *args: update_total())
    note = ttk.Label(container, text='Bạn có thể đặt trước và thanh toán sau trong mục "Đơn của tôi"', style='Body.TLabel')
    note.pack(anchor='w', pady=(12,0))
    def create_booking(pay_now=False):
        try:
            so = int(qty_var.get())
            if so <= 0:
                raise Exception()
        except Exception:
            messagebox.showerror('Lỗi', 'Số người không hợp lệ')
            return
        maKH = self.ql.currentUser.maKH
        existing = [int(d.maDat.replace('D','')) for d in self.ql.danhSachDatTour if d.maDat and d.maDat.startswith('D')]
        nxt = (max(existing)+1) if existing else 1
        maDat = f'D{str(nxt).zfill(4)}'
        dt = DatTour(maDat, maKH, maTour, so, 'now')
        dt.trangThai = 'chua_thanh_toan'
        dt.tongTien = so * tour.gia
        if pay_now:
            kh = self.ql.TimKhacHang(maKH)
            if kh and kh.soDu >= dt.tongTien:
                kh.soDu -= dt.tongTien
                dt.trangThai = 'da_thanh_toan'
            else:
                messagebox.showerror('Lỗi', 'Số dư không đủ để thanh toán ngay')
                return
        self.ql.danhSachDatTour.append(dt)
        luu_tat_ca(self.ql)
        self.refresh_lists()
        if pay_now:
            messagebox.showinfo('Thông báo', 'Đặt tour và thanh toán thành công!')
        else:
            messagebox.showinfo('Thông báo', 'Đặt tour thành công! Vui lòng thanh toán trong "Đơn của tôi".')
        top.destroy()
    btn_bar = ttk.Frame(container)
    btn_bar.pack(fill='x', pady=(16,0))
    ttk.Button(btn_bar, text='Đặt trước (chưa thanh toán)', style='App.TButton', command=lambda: create_booking(False)).pack(side='left', padx=4)
    ttk.Button(btn_bar, text='Thanh toán & đặt tour', style='Accent.TButton', command=lambda: create_booking(True)).pack(side='left', padx=4)
    ttk.Button(btn_bar, text='Đóng', style='Danger.TButton', command=top.destroy).pack(side='left', padx=4)

def update_user_right_panel(self, maTour):
    if hasattr(self, 'greet_label'):
        name = ''
        if self.ql.currentUser:
            kh = self.ql.TimKhacHang(self.ql.currentUser.maKH)
            name = kh.tenKH if kh else self.ql.currentUser.maKH
        self.greet_label.config(text=f"Xin chào, {name}")
    if hasattr(self, 'balance_label'):
        bal = 0
        if self.ql.currentUser:
            kh = self.ql.TimKhacHang(self.ql.currentUser.maKH)
            bal = kh.soDu if kh else 0
        self.balance_label.config(text=f"Số dư: {self.format_money(bal)}")
    for w in self.context_body.winfo_children():
        w.destroy()
    t = self.ql.TimTour(maTour)
    if not t:
        ttk.Label(self.context_body, text='Chưa chọn tour', style='Body.TLabel').pack()
        return
    card = ttk.LabelFrame(self.context_body, text='Tour đã chọn', style='Card.TLabelframe', padding=10)
    card.pack(fill='x', pady=(0,12))
    ttk.Label(card, text=t.tenTour, style='Title.TLabel').pack(anchor='w')
    ttk.Label(card, text=f"Giá: {self.format_money(t.gia)} | Số chỗ: {t.soCho}", style='Body.TLabel').pack(anchor='w', pady=(6,0))
    
    summary = ttk.LabelFrame(self.context_body, text='Lịch trình', style='Card.TLabelframe', padding=10)
    summary.pack(fill='both', expand=True)
    cols = ('Ngay','DiaDiem','MoTa')
    tv = ttk.Treeview(summary, columns=cols, show='headings', height=6)
    tv.heading('Ngay', text='Ngày')
    tv.heading('DiaDiem', text='Địa điểm')
    tv.heading('MoTa', text='Mô tả')
    tv.column('Ngay', width=100, anchor='center')
    tv.column('DiaDiem', width=160, anchor='w')
    tv.column('MoTa', width=220, anchor='w')
    scr = ttk.Scrollbar(summary, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    for l in t.lichTrinh:
        ngay = l.get('ngay','')
        dia = l.get('diaDiem', l.get('dia_diem','')) or ''
        mota = l.get('moTa', l.get('mo_ta','')) or ''
        tv.insert('', tk.END, values=(ngay, dia, mota))
    self.apply_zebra(tv)

GiaoDienCoSo.nap_tien = nap_tien
GiaoDienCoSo.xem_don_user = xem_don_user
GiaoDienCoSo.book_selected_tour_for_user = book_selected_tour_for_user
GiaoDienCoSo.update_user_right_panel = update_user_right_panel
