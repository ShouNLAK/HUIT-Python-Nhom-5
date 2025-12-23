import base64
import io
import os
import tempfile
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from Class.dat_tour import DatTour
from QuanLy.storage import luu_tat_ca
from GUI.Login.base import GiaoDienCoSo, PIL_AVAILABLE

def nap_tien(self):
    if not self.ql.nguoi_dung_hien_tai or self.ql.nguoi_dung_hien_tai.vai_tro != 'user':
        messagebox.showerror('Lỗi', 'Chức năng chỉ dành cho khách hàng')
        return
    top, container = self.create_modal('Nạp tiền vào ví', size=(680, 620))
    
    header_frame = ttk.Frame(container, style='Card.TFrame', padding=16)
    header_frame.pack(fill='x', pady=(0, 16))
    ttk.Label(header_frame, text='Nạp tiền vào tài khoản', style='Title.TLabel').pack(anchor='w')
    ttk.Label(header_frame, text='Quét mã QR để nạp tiền nhanh chóng và an toàn', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    
    form_card = ttk.LabelFrame(container, text='Thông tin nạp tiền', padding=16, style='Card.TLabelframe')
    form_card.pack(fill='x', pady=(0, 16))
    form = ttk.Frame(form_card)
    form.pack(fill='x')
    ttk.Label(form, text='Số tiền cần nạp (VND):', style='Form.TLabel').grid(row=0, column=0, sticky='w', pady=8)
    amount_entry = ttk.Entry(form, font=self.font_body, width=30)
    amount_entry.grid(row=0, column=1, sticky='ew', padx=(12, 0), pady=8)
    form.columnconfigure(1, weight=1)
    entries = {'sotien': amount_entry}
    
    status_var = tk.StringVar(value='Nhập số tiền và nhấn "Tạo mã QR" để bắt đầu')
    status_label = ttk.Label(container, textvariable=status_var, style='BodyBold.TLabel', wraplength=620)
    status_label.pack(anchor='w', pady=(0, 12))
    
    qr_box = ttk.LabelFrame(container, text='Mã QR thanh toán', padding=20, style='Card.TLabelframe')
    qr_box.pack(fill='both', expand=True, pady=(0, 12))
    qr_label = ttk.Label(qr_box, text='Chưa tạo mã QR\n\nVui lòng nhập số tiền và tạo mã QR', style='Body.TLabel', justify='center')
    qr_label.pack(anchor='center', expand=True)
    
    url_var = tk.StringVar(value='')
    link_card = ttk.LabelFrame(container, text='Đường dẫn thanh toán', padding=12, style='Card.TLabelframe')
    link_card.pack(fill='x', pady=(0, 16))
    link_row = ttk.Frame(link_card)
    link_row.pack(fill='x')
    link_entry = ttk.Entry(link_row, textvariable=url_var, state='readonly', font=('Segoe UI', 9))
    link_entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
    def copy_link():
        val = url_var.get()
        if not val:
            messagebox.showwarning('Chú ý', 'Chưa có đường dẫn để sao chép')
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(val)
        messagebox.showinfo('Sao chép', 'Đã sao chép liên kết vào clipboard')
    ttk.Button(link_row, text='Sao chép', style='Ghost.TButton', command=copy_link).pack(side='left')
    
    request_state = {'id': None, 'job': None, 'listener': None}

    def stop_polling():
        job = request_state.get('job')
        if job:
            try:
                self.root.after_cancel(job)
            except Exception:
                pass
            request_state['job'] = None
        lst = request_state.get('listener')
        if lst:
            try:
                self.ql.remove_payment_listener(lst)
            except Exception:
                pass
            request_state['listener'] = None

    def update_qr_image(source):
        if not source:
            return
        try:
            photo = None
            if isinstance(source, str) and source.startswith('data:image'):
                encoded = source.split(',', 1)[1] if ',' in source else ''
                if not encoded:
                    raise ValueError('QR data rỗng')
                raw = base64.b64decode(encoded)
                if PIL_AVAILABLE:
                    from PIL import Image, ImageTk
                    img = Image.open(io.BytesIO(raw))
                    img = img.resize((280, 280))
                    photo = ImageTk.PhotoImage(img)
                else:
                    photo = tk.PhotoImage(data=encoded, format='png')
            elif isinstance(source, str) and os.path.exists(source):
                if PIL_AVAILABLE:
                    from PIL import Image, ImageTk
                    img = Image.open(source)
                    img = img.resize((280, 280))
                    photo = ImageTk.PhotoImage(img)
                else:
                    photo = tk.PhotoImage(file=source)
            if not photo:
                raise ValueError('Không thể dựng ảnh QR')
            qr_label.configure(image=photo, text='')
            qr_label.image = photo
        except Exception as exc:
            qr_label.configure(text=f'Không tải được ảnh QR: {exc}', image='')
            qr_label.image = None

    def poll_status():
        req_id = request_state.get('id')
        if not req_id:
            return
        info = self.ql.lay_thong_tin_nap_tien(req_id)
        if not info:
            status_var.set('Không tìm thấy yêu cầu, có thể đã bị xóa')
            stop_polling()
            return
        state = info.get('trangThai')
        if state == 'confirmed':
            try:
                handle_confirmation(info)
            except Exception:
                pass
            return
        if state == 'expired':
            status_var.set('Mã QR đã hết hạn, vui lòng tạo lại')
            stop_polling()
            return
        expires = info.get('expiresAt') or ''
        status_var.set(f'Đang chờ bạn quét QR... (Hết hạn: {expires})')
        request_state['job'] = self.root.after(2000, poll_status)

    def tao_qr():
        try:
            so = float(entries['sotien'].get())
            if so <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror('Lỗi', 'Vui lòng nhập số tiền hợp lệ (lớn hơn 0)')
            return
        success, payload = self.ql.tao_yeu_cau_nap_tien(self.ql.nguoi_dung_hien_tai.ma_khach_hang, so)
        if not success:
            messagebox.showerror('Lỗi', payload)
            return
        request_state['id'] = payload['maGiaoDich']
        def _on_payment(info):
            try:
                if info and info.get('maGiaoDich') == request_state.get('id'):
                    try:
                        self.root.after(0, lambda: handle_confirmation(info))
                    except Exception:
                        handle_confirmation(info)
            except Exception:
                pass
        try:
            ok = self.ql.add_payment_listener(_on_payment)
            if ok:
                request_state['listener'] = _on_payment
        except Exception:
            request_state['listener'] = None
        status_var.set(f'Đang chờ quét mã QR để nạp {self.format_money(so)}...')
        url_var.set(payload.get('qrUrl', ''))
        update_qr_image(payload.get('qrDataUri') or payload.get('qrPath'))
        stop_polling()
        request_state['job'] = self.root.after(2000, poll_status)

    def close_modal():
        req_id = request_state.get('id')
        if req_id:
            info = None
            try:
                info = self.ql.lay_thong_tin_nap_tien(req_id)
            except Exception:
                info = None
            if info:
                text = (f"Mã giao dịch: {info.get('maGiaoDich')}\n"
                        f"Số tiền: {self.format_money(info.get('soTien', 0))}\n"
                        f"Trạng thái: {info.get('trangThai')}\n"
                        f"Hết hạn: {info.get('expiresAt')}\n")
                messagebox.showinfo('Chi tiết hoá đơn', text)
        stop_polling()
        top.destroy()

    def handle_confirmation(info):
        try:
            stop_polling()
        except Exception:
            pass
        try:
            amount = info.get('soTien', 0)
            luu_tat_ca(self.ql)
            self.hien_thi_khach_user()
            self.refresh_lists()
        except Exception:
            pass
        try:
            if top.winfo_exists():
                top.destroy()
        except Exception:
            pass
        try:
            ma = info.get('maGiaoDich')
            text = (f"Giao dịch {ma}\n"
                    f"Số tiền: {self.format_money(info.get('soTien', 0))}\n"
                    f"Trạng thái: {info.get('trangThai')}\n"
                    f"Hết hạn: {info.get('expiresAt')}\n")
            messagebox.showinfo('Nạp tiền thành công', text)
        except Exception:
            pass

    btn_frame = ttk.Frame(container)
    btn_frame.pack(fill='x')
    ttk.Button(btn_frame, text='🎯 Tạo mã QR', style='Accent.TButton', command=tao_qr).pack(side='left', padx=(0, 8))
    ttk.Button(btn_frame, text='✖ Đóng', style='Danger.TButton', command=close_modal).pack(side='left')
    top.protocol('WM_DELETE_WINDOW', close_modal)

def xem_don_user(self):
    if not self.ql.nguoi_dung_hien_tai:
        messagebox.showerror('Lỗi', 'Bạn cần đăng nhập')
        return
    ds = [d for d in self.ql.danh_sach_dat_tour if d.ma_khach_hang == self.ql.nguoi_dung_hien_tai.ma_khach_hang]
    if not ds:
        messagebox.showinfo('Đơn của tôi', 'Không có đơn')
        return
    top, container = self.create_modal('Đơn của tôi', size=(780, 500))
    ttk.Label(container, text='Danh sách đơn đặt tour của bạn', style='Title.TLabel').pack(anchor='w', pady=(0,12))
    list_frame = ttk.Frame(container)
    list_frame.pack(fill='both', expand=True)
    tv = ttk.Treeview(list_frame, columns=('ma_dat','ma_tour','so_nguoi','trang_thai','tong'), show='headings')
    for col, text, w in (('ma_dat','Mã đặt',120),('ma_tour','Mã tour',120),('so_nguoi','Số người',90),('trang_thai','Trạng thái',140),('tong','Tổng tiền',140)):
        tv.heading(col, text=text)
        tv.column(col, width=w, anchor='center')
    scr = ttk.Scrollbar(list_frame, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    for d in ds:
        status_display = 'Đã thanh toán' if d.trang_thai == 'da_thanh_toan' else 'Chưa thanh toán'
        tv.insert('', tk.END, values=(d.ma_dat_tour, d.ma_tour, d.so_nguoi, status_display, self.format_money(d.tong_tien)))
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
        dt = next((d for d in self.ql.danh_sach_dat_tour if d.ma_dat_tour == ma_dat), None)
        if not dt:
            messagebox.showerror('Lỗi', 'Không tìm thấy đơn')
            return
        if dt.trang_thai == 'da_thanh_toan':
            messagebox.showinfo('Thông báo', 'Đơn này đã được thanh toán')
            return
        kh = self.ql.tim_khach_hang(self.ql.nguoi_dung_hien_tai.ma_khach_hang)
        if not kh:
            messagebox.showerror('Lỗi', 'Không tìm thấy khách hàng')
            return
        if kh.so_du < dt.tong_tien:
            messagebox.showerror('Lỗi', f'Số dư không đủ. Cần {self.format_money(dt.tong_tien)}, hiện có {self.format_money(kh.so_du)}')
            return
        if messagebox.askyesno('Xác nhận', f'Thanh toán {self.format_money(dt.tong_tien)} cho đơn {ma_dat}?'):
            kh.so_du -= dt.tong_tien
            dt.trang_thai = 'da_thanh_toan'
            luu_tat_ca(self.ql)
            messagebox.showinfo('Thành công', 'Thanh toán thành công!')
            self.refresh_lists()
            tv.item(sel[0], values=(dt.ma_dat_tour, dt.ma_tour, dt.so_nguoi, 'Đã thanh toán', self.format_money(dt.tong_tien)))
            top.destroy()
    def huy_don():
        sel = tv.selection()
        if not sel:
            messagebox.showwarning('Chú ý', 'Chọn một đơn để hủy')
            return
        vals = tv.item(sel[0], 'values')
        ma_dat = vals[0]
        if messagebox.askyesno('Xác nhận', f'Hủy đơn {ma_dat}?'):
            if self.ql.huy_dat_tour(ma_dat):
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
    ma_tour = self.tv_tour.item(item, 'values')[0]
    if not self.ql.nguoi_dung_hien_tai or self.ql.nguoi_dung_hien_tai.vai_tro != 'user':
        messagebox.showerror('Lỗi', 'Chức năng dành cho khách hàng đăng nhập')
        return
    tour = self.ql.tim_tour(ma_tour)
    if not tour:
        messagebox.showerror('Lỗi', 'Không tìm thấy tour')
        return
    top, container = self.create_modal('Đặt tour', size=(520, 400))
    ttk.Label(container, text=f'Đặt tour: {tour.ten_tour}', style='Title.TLabel').pack(anchor='w')
    ttk.Label(container, text=f'Giá: {self.format_money(tour.gia_tour)} / người', style='Body.TLabel').pack(anchor='w', pady=(4,12))
    form = ttk.Frame(container)
    form.pack(fill='x')
    ttk.Label(form, text='Mã tour', style='Form.TLabel').grid(row=0, column=0, sticky='w')
    e1 = ttk.Entry(form, font=self.font_body)
    e1.insert(0, ma_tour)
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
            total = so * tour.gia_tour
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
        ma_khach_hang = self.ql.nguoi_dung_hien_tai.ma_khach_hang
        existing = [int(d.ma_dat_tour.replace('D','')) for d in self.ql.danh_sach_dat_tour if d.ma_dat_tour and d.ma_dat_tour.startswith('D')]
        nxt = (max(existing)+1) if existing else 1
        ma_dat = f'D{str(nxt).zfill(4)}'
        dt = DatTour(ma_dat, ma_khach_hang, ma_tour, so, 'now')
        dt.trang_thai = 'chua_thanh_toan'
        dt.tong_tien = so * tour.gia_tour
        if pay_now:
            kh = self.ql.tim_khach_hang(ma_khach_hang)
            if kh and kh.so_du >= dt.tong_tien:
                kh.so_du -= dt.tong_tien
                dt.trang_thai = 'da_thanh_toan'
            else:
                messagebox.showerror('Lỗi', 'Số dư không đủ để thanh toán ngay')
                return
        self.ql.danh_sach_dat_tour.append(dt)
        luu_tat_ca(self.ql)
        self.refresh_lists()
        top.destroy()
        if pay_now:
            messagebox.showinfo('Thành công', 'Đặt tour và thanh toán thành công!')
        else:
            messagebox.showinfo('Thành công', 'Đặt tour thành công! Vui lòng thanh toán trong "Đơn của tôi".')
    btn_bar = ttk.Frame(container)
    btn_bar.pack(fill='x', pady=(16,0))
    ttk.Button(btn_bar, text='Đặt trước (chưa thanh toán)', style='App.TButton', command=lambda: create_booking(False)).pack(side='left', padx=4)
    ttk.Button(btn_bar, text='Thanh toán & đặt tour', style='Accent.TButton', command=lambda: create_booking(True)).pack(side='left', padx=4)
    ttk.Button(btn_bar, text='Đóng', style='Danger.TButton', command=top.destroy).pack(side='left', padx=4)

def update_user_right_panel(self, ma_tour):
    if hasattr(self, 'greet_label'):
        name = ''
        if self.ql.nguoi_dung_hien_tai:
            kh = self.ql.tim_khach_hang(self.ql.nguoi_dung_hien_tai.ma_khach_hang)
            name = kh.ten_khach_hang if kh else self.ql.nguoi_dung_hien_tai.ma_khach_hang
        self.greet_label.config(text=f"Xin chào, {name}")
    if hasattr(self, 'balance_label'):
        bal = 0
        if self.ql.nguoi_dung_hien_tai:
            kh = self.ql.tim_khach_hang(self.ql.nguoi_dung_hien_tai.ma_khach_hang)
            bal = kh.so_du if kh else 0
        self.balance_label.config(text=f"Số dư: {self.format_money(bal)}")
    for w in self.context_body.winfo_children():
        w.destroy()
    t = self.ql.tim_tour(ma_tour)
    if not t:
        ttk.Label(self.context_body, text='Chưa chọn tour', style='Body.TLabel').pack()
        return
    card = ttk.LabelFrame(self.context_body, text='Tour đã chọn', style='Card.TLabelframe', padding=10)
    card.pack(fill='x', pady=(0,12))
    ttk.Label(card, text=t.ten_tour, style='Title.TLabel').pack(anchor='w')
    ttk.Label(card, text=f"Giá: {self.format_money(t.gia_tour)} | Số chỗ: {t.so_cho}", style='Body.TLabel').pack(anchor='w', pady=(6,0))
    
    summary = ttk.LabelFrame(self.context_body, text='Lịch trình', style='Card.TLabelframe', padding=10)
    summary.pack(fill='both', expand=True)
    cols = ('ngay','dia_diem','mo_ta')
    tv = ttk.Treeview(summary, columns=cols, show='headings', height=6)
    tv.heading('ngay', text='Ngày')
    tv.heading('dia_diem', text='Địa điểm')
    tv.heading('mo_ta', text='Mô tả')
    tv.column('ngay', width=100, anchor='center')
    tv.column('dia_diem', width=160, anchor='w')
    tv.column('mo_ta', width=220, anchor='w')
    scr = ttk.Scrollbar(summary, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    for l in t.lich_trinh:
        ngay = l.get('ngay','')
        dia = l.get('dia_diem', l.get('diaDiem','')) or ''
        mota = l.get('mo_ta', l.get('moTa','')) or ''
        tv.insert('', tk.END, values=(ngay, dia, mota))
    self.apply_zebra(tv)

GiaoDienCoSo.nap_tien = nap_tien
GiaoDienCoSo.xem_don_user = xem_don_user
GiaoDienCoSo.book_selected_tour_for_user = book_selected_tour_for_user
GiaoDienCoSo.update_user_right_panel = update_user_right_panel
