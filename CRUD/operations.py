import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
from datetime import datetime
import json
import re
from Class.tour import TourDuLich
from Class.khach_hang import KhachHang
from Class.dat_tour import DatTour
from QuanLy.storage import luu_tat_ca
from GUI.Login.base import GiaoDienCoSo


def _trich_chu_so_tho(s):
    return re.sub(r'[^\d.]', '', s)


def tu_dong_dinh_dang_ngay(entry_widget):
    def on_key_release(event=None):
        content = entry_widget.get().strip()
        if len(content) == 8 and content.isdigit():
            formatted = f"{content[:2]}/{content[2:4]}/{content[4:]}"
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, formatted)
            entry_widget.icursor(tk.END)
    entry_widget.bind('<KeyRelease>', on_key_release)


def sua_khach(self):
    if not self.quyen_admin():
        return
    kh = self.get_selected_customer()
    if not kh:
        return
    top, container = self.create_modal('Cập nhật khách hàng', size=(600, 500))
    header = ttk.Frame(container, style='Card.TFrame', padding=12)
    header.pack(fill='x', pady=(0,12))
    ttk.Label(header, text=f'CẬP NHẬT KHÁCH HÀNG: {kh.ma_khach_hang}', style='Title.TLabel').pack(anchor='w')
    ttk.Label(header, text='Chỉnh sửa thông tin khách hàng', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    
    form_frame = ttk.Frame(container)
    form_frame.pack(fill='both', expand=True, padx=12, pady=(0,12))
    
    ttk.Label(form_frame, text='Mã khách hàng', style='Form.TLabel').grid(row=0, column=0, sticky='w', pady=8)
    ma_label = ttk.Label(form_frame, text=kh.ma_khach_hang, style='BodyBold.TLabel')
    ma_label.grid(row=0, column=1, sticky='w', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Họ và tên *', style='Form.TLabel').grid(row=1, column=0, sticky='w', pady=8)
    ten_entry = ttk.Entry(form_frame, font=self.font_body)
    ten_entry.insert(0, kh.ten_khach_hang)
    ten_entry.grid(row=1, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Số điện thoại *', style='Form.TLabel').grid(row=2, column=0, sticky='w', pady=8)
    sdt_entry = ttk.Entry(form_frame, font=self.font_body)
    sdt_entry.insert(0, kh.so_dien_thoai)
    sdt_entry.grid(row=2, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Email *', style='Form.TLabel').grid(row=3, column=0, sticky='w', pady=8)
    email_entry = ttk.Entry(form_frame, font=self.font_body)
    email_entry.insert(0, kh.email)
    email_entry.grid(row=3, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Số dư (VND)', style='Form.TLabel').grid(row=4, column=0, sticky='w', pady=8)
    sodu_entry = ttk.Entry(form_frame, font=self.font_body)
    sodu_entry.insert(0, str(kh.so_du))
    sodu_entry.grid(row=4, column=1, sticky='ew', padx=(12,0), pady=8)
    
    form_frame.columnconfigure(1, weight=1)
    
    entries = {'ten': ten_entry, 'sdt': sdt_entry, 'email': email_entry, 'sodu': sodu_entry}
    
    def format_sodu(event=None):
        try:
            val = entries['sodu'].get().replace(',', '').replace(' ', '')
            if val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
                formatted = f"{int(val):,}".replace(',', ' ')
                entries['sodu'].delete(0, tk.END)
                entries['sodu'].insert(0, formatted)
        except:
            pass

    def unformat_sodu(event=None):
        try:
            val = entries['sodu'].get().replace(' ', '').replace(',', '')
            entries['sodu'].delete(0, tk.END)
            entries['sodu'].insert(0, val)
        except:
            pass

    sodu_entry.bind('<FocusOut>', format_sodu)
    sodu_entry.bind('<FocusIn>', unformat_sodu)
    
    help_frame = ttk.Frame(container, style='Card.TFrame', padding=8)
    help_frame.pack(fill='x', pady=(0,12))
    ttk.Label(help_frame, text='• Các trường đánh dấu (*) là bắt buộc phải nhập', style='Body.TLabel', foreground='#52606d').pack(anchor='w')
    
    def ok():
        ten = entries['ten'].get().strip()
        sdt = entries['sdt'].get().strip()
        email = entries['email'].get().strip()
        try:
            so_du = float(_trich_chu_so_tho(entries['sodu'].get()) or 0)
        except Exception:
            messagebox.showerror('Lỗi', 'Số dư không hợp lệ')
            return
        if not ten or not sdt or not email:
            messagebox.showerror('Lỗi', 'Vui lòng nhập đủ Họ tên, SĐT, Email')
            return
        if not self.ql.hop_le_so_dien_thoai_vn(sdt):
            messagebox.showerror('Lỗi', 'Số điện thoại phải 10 số, đúng đầu số VN')
            return
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            messagebox.showerror('Lỗi', 'Email không hợp lệ')
            return
        if self.ql.cap_nhat_khach_hang(ma_khach_hang=kh.ma_khach_hang, ten_khach_hang=ten, so_dien_thoai=sdt, email=email, so_du=so_du):
            luu_tat_ca(self.ql)
            self.hien_thi_khach()
            top.destroy()

    self.modal_buttons(container, [
        {'text':'Lưu thay đổi', 'style':'Accent.TButton', 'command':ok},
        {'text':'Đóng', 'style':'Danger.TButton', 'command':top.destroy}
    ])


def xoa_khach(self):
    if not self.quyen_admin():
        return
    kh = self.get_selected_customer()
    if not kh:
        return
    if messagebox.askyesno('Xác nhận', f'Xóa khách hàng {kh.ten_khach_hang}?'):
        if self.ql.xoa_khach_hang(kh.ma_khach_hang):
            self.ql.danh_sach_nguoi_dung = [u for u in self.ql.danh_sach_nguoi_dung if u.ma_khach_hang != kh.ma_khach_hang]
            luu_tat_ca(self.ql)
            self.hien_thi_khach()

def get_selected_hdv(self):
    if not getattr(self, 'tv_hdv', None):
        return None
    sel = self.tv_hdv.selection()
    if not sel:
        messagebox.showwarning('Chú ý', 'Chọn một HDV trước')
        return None
    values = self.tv_hdv.item(sel[0], 'values')
    ma = values[0]
    if hasattr(self.ql, 'danh_sach_hdv'):
        return next((h for h in self.ql.danh_sach_hdv if str(h.get('maHDV')) == str(ma)), None)
    return None

def them_hdv(self):
    if not self.quyen_admin():
        return
    top, container = self.create_modal('Thêm hướng dẫn viên mới', size=(600, 500))
    
    header = ttk.Frame(container, style='Card.TFrame', padding=12)
    header.pack(fill='x', pady=(0,12))
    ttk.Label(header, text='THÊM HƯỚNG DẪN VIÊN MỚI', style='Title.TLabel').pack(anchor='w')
    ttk.Label(header, text='Nhập thông tin hướng dẫn viên để thêm vào hệ thống', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    
    form_frame = ttk.Frame(container)
    form_frame.pack(fill='both', expand=True, padx=12, pady=(0,12))
    
    ttk.Label(form_frame, text='Mã HDV *', style='Form.TLabel').grid(row=0, column=0, sticky='w', pady=8)
    ma_entry = ttk.Entry(form_frame, font=self.font_body)
    ma_entry.grid(row=0, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Họ và tên *', style='Form.TLabel').grid(row=1, column=0, sticky='w', pady=8)
    ten_entry = ttk.Entry(form_frame, font=self.font_body)
    ten_entry.grid(row=1, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Số điện thoại *', style='Form.TLabel').grid(row=2, column=0, sticky='w', pady=8)
    sdt_entry = ttk.Entry(form_frame, font=self.font_body)
    sdt_entry.grid(row=2, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Kinh nghiệm (năm) *', style='Form.TLabel').grid(row=3, column=0, sticky='w', pady=8)
    exp_entry = ttk.Entry(form_frame, font=self.font_body)
    exp_entry.grid(row=3, column=1, sticky='ew', padx=(12,0), pady=8)
    
    form_frame.columnconfigure(1, weight=1)
    
    entries = {'ma': ma_entry, 'ten': ten_entry, 'sdt': sdt_entry, 'exp': exp_entry}
    
    help_frame = ttk.Frame(container, style='Card.TFrame', padding=8)
    help_frame.pack(fill='x', pady=(0,12))
    ttk.Label(help_frame, text='• Tất cả các trường đều bắt buộc phải điền\n• Số điện thoại phải 10 số, đúng đầu số VN', style='Body.TLabel', foreground='#52606d').pack(anchor='w')
    
    def ok():
        data = {
            'maHDV': entries['ma'].get().strip(),
            'tenHDV': entries['ten'].get().strip(),
            'sdt': entries['sdt'].get().strip(),
            'kinhNghiem': entries['exp'].get().strip() or '0'
        }
        if not all(data.values()):
            messagebox.showerror('Lỗi', 'Vui lòng điền đầy đủ tất cả các trường thông tin')
            return
        if not hasattr(self.ql, 'danh_sach_hdv'):
            self.ql.danh_sach_hdv = []
        if any(str(h.get('maHDV')) == data['maHDV'] for h in self.ql.danh_sach_hdv):
            messagebox.showerror('Lỗi', 'Mã HDV đã tồn tại trong hệ thống')
            return
        if not self.ql.hop_le_so_dien_thoai_vn(data['sdt']):
            messagebox.showerror('Lỗi', 'Số điện thoại HDV phải 10 số, đúng đầu số VN')
            return
        self.ql.danh_sach_hdv.append(data)
        username = self.ql.ensure_user_for_hdv(data)
        luu_tat_ca(self.ql)
        self.hien_thi_hdv()
        top.destroy()
        if username:
            messagebox.showinfo('Thành công', f'Đã thêm HDV {data["tenHDV"]}\nTài khoản: {username} / Mật khẩu mặc định: 123')
        else:
            messagebox.showinfo('Thành công', f'Đã thêm HDV {data["tenHDV"]}')
    
    self.modal_buttons(container, [
        {'text':'Thêm HDV', 'style':'Accent.TButton', 'command':ok},
        {'text':'Đóng', 'style':'Danger.TButton', 'command':top.destroy}
    ])

def sua_hdv(self):
    if not self.quyen_admin():
        return
    hdv = self.get_selected_hdv()
    if not hdv:
        return
    top, container = self.create_modal('Cập nhật HDV', size=(600, 500))
    header = ttk.Frame(container, style='Card.TFrame', padding=12)
    header.pack(fill='x', pady=(0,12))
    ttk.Label(header, text=f'CẬP NHẬT HƯỚNG DẪN VIÊN: {hdv.get("maHDV", "")}', style='Title.TLabel').pack(anchor='w')
    ttk.Label(header, text='Chỉnh sửa thông tin hướng dẫn viên', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    
    form_frame = ttk.Frame(container)
    form_frame.pack(fill='both', expand=True, padx=12, pady=(0,12))
    
    ttk.Label(form_frame, text='Mã HDV', style='Form.TLabel').grid(row=0, column=0, sticky='w', pady=8)
    ma_label = ttk.Label(form_frame, text=hdv.get('maHDV', ''), style='BodyBold.TLabel')
    ma_label.grid(row=0, column=1, sticky='w', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Họ và tên *', style='Form.TLabel').grid(row=1, column=0, sticky='w', pady=8)
    ten_entry = ttk.Entry(form_frame, font=self.font_body)
    ten_entry.insert(0, hdv.get('tenHDV', ''))
    ten_entry.grid(row=1, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Số điện thoại *', style='Form.TLabel').grid(row=2, column=0, sticky='w', pady=8)
    sdt_entry = ttk.Entry(form_frame, font=self.font_body)
    sdt_entry.insert(0, hdv.get('sdt', ''))
    sdt_entry.grid(row=2, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Kinh nghiệm (năm) *', style='Form.TLabel').grid(row=3, column=0, sticky='w', pady=8)
    exp_entry = ttk.Entry(form_frame, font=self.font_body)
    exp_entry.insert(0, str(hdv.get('kinhNghiem', '')))
    exp_entry.grid(row=3, column=1, sticky='ew', padx=(12,0), pady=8)
    
    form_frame.columnconfigure(1, weight=1)
    
    entries = {'ten': ten_entry, 'sdt': sdt_entry, 'exp': exp_entry}
    
    help_frame = ttk.Frame(container, style='Card.TFrame', padding=8)
    help_frame.pack(fill='x', pady=(0,12))
    ttk.Label(help_frame, text='• Các trường đánh dấu (*) là bắt buộc phải nhập\n• Số điện thoại phải 10 số, đúng đầu số VN', style='Body.TLabel', foreground='#52606d').pack(anchor='w')
    
    def ok():
        hdv['tenHDV'] = entries['ten'].get().strip()
        hdv['sdt'] = entries['sdt'].get().strip()
        hdv['kinhNghiem'] = entries['exp'].get().strip()
        if not hdv['tenHDV'] or not hdv['sdt'] or not hdv['kinhNghiem']:
            messagebox.showerror('Lỗi', 'Vui lòng nhập đủ Họ tên, SĐT, Kinh nghiệm')
            return
        if not self.ql.hop_le_so_dien_thoai_vn(hdv['sdt']):
            messagebox.showerror('Lỗi', 'Số điện thoại HDV phải 10 số, đúng đầu số VN')
            return
        self.ql.ensure_user_for_hdv(hdv)
        luu_tat_ca(self.ql)
        self.hien_thi_hdv()
        top.destroy()
    
    self.modal_buttons(container, [
        {'text':'Lưu thay đổi', 'style':'Accent.TButton', 'command':ok},
        {'text':'Đóng', 'style':'Danger.TButton', 'command':top.destroy}
    ])

def xoa_hdv(self):
    if not self.quyen_admin():
        return
    hdv = self.get_selected_hdv()
    if not hdv:
        return
    if messagebox.askyesno('Xác nhận', f'Xóa HDV {hdv.get("tenHDV","")}?'):
        self.ql.danh_sach_hdv = [h for h in self.ql.danh_sach_hdv if h is not hdv]
        self.ql.danh_sach_nguoi_dung = [u for u in self.ql.danh_sach_nguoi_dung if not (u.vai_tro == 'hdv' and u.ma_khach_hang == hdv.get('maHDV'))]
        luu_tat_ca(self.ql)
        self.hien_thi_hdv()

def dat_tour_for_customer(self, ma_kh):
    self.dat_tour(preset_ma_kh=ma_kh)

def huy_dat_for_customer(self, ma_kh):
    ds = [d for d in self.ql.danh_sach_dat_tour if d.ma_khach_hang == ma_kh]
    if not ds:
        messagebox.showinfo('Thông báo', 'Khách hàng chưa có đơn')
        return
    
    kh = self.ql.tim_khach_hang(ma_kh)
    top, container = self.create_modal('Hủy đặt tour cho khách hàng', size=(800, 600))
    
    header = ttk.Frame(container, style='Card.TFrame', padding=12)
    header.pack(fill='x', pady=(0,12))
    ttk.Label(header, text=f'HỦY ĐẶT TOUR - KHÁCH HÀNG {ma_kh}', style='Title.TLabel').pack(anchor='w')
    ttk.Label(header, text=f'Chọn đơn cần hủy. Số dư hiện tại: {self.format_money(kh.so_du) if kh else "N/A"}', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    
    content = ttk.Frame(container)
    content.pack(fill='both', expand=True)
    
    tv = ttk.Treeview(content, columns=('MaDat','MaTour','TenTour','SoNguoi','TrangThai','Tong','NgayDat'), show='headings', height=8)
    for col, text, w in (
        ('MaDat','Mã đặt',100),
        ('MaTour','Mã tour',100),
        ('TenTour','Tên tour',200),
        ('SoNguoi','Số người',80),
        ('TrangThai','Trạng thái',120),
        ('Tong','Tổng tiền',120),
        ('NgayDat','Ngày đặt',100)
    ):
        tv.heading(col, text=text)
        tv.column(col, width=w, anchor='center' if col != 'TenTour' else 'w')
    scr = ttk.Scrollbar(content, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    
    for d in ds:
        tour = self.ql.tim_tour(d.ma_tour)
        ten_tour = tour.ten_tour if tour else 'N/A'
        tv.insert('', tk.END, values=(
            d.ma_dat_tour, 
            d.ma_tour, 
            ten_tour, 
            d.so_nguoi, 
            d.trang_thai, 
            self.format_money(d.tong_tien), 
            d.ngay_dat or '-'
        ))
    self.apply_zebra(tv)
    
    detail_frame = ttk.LabelFrame(content, text='Chi tiết đơn được chọn', style='Card.TLabelframe', padding=12)
    detail_frame.pack(fill='x', pady=(12,0))
    detail_label = ttk.Label(detail_frame, text='Chọn một đơn để xem chi tiết', style='Body.TLabel')
    detail_label.pack(anchor='w')
    
    def on_select(event):
        sel = tv.selection()
        if sel:
            item = tv.item(sel[0], 'values')
            ma_dat = item[0]
            d = next((dd for dd in ds if dd.ma_dat_tour == ma_dat), None)
            if d:
                tour = self.ql.tim_tour(d.ma_tour)
                detail_text = f"""
Mã đặt: {d.ma_dat_tour}
Tour: {tour.ten_tour if tour else 'N/A'} ({d.ma_tour})
Số người: {d.so_nguoi}
Trạng thái: {d.trang_thai}
Tổng tiền: {self.format_money(d.tong_tien)}
Ngày đặt: {d.ngay_dat or 'N/A'}
                """.strip()
                detail_label.config(text=detail_text)
        else:
            detail_label.config(text='Chọn một đơn để xem chi tiết')
    
    tv.bind('<<TreeviewSelect>>', on_select)
    
    def ok():
        sel = tv.selection()
        if not sel:
            messagebox.showwarning('Chú ý', 'Chọn một đơn để hủy')
            return
        ma = tv.item(sel[0], 'values')[0]
        if messagebox.askyesno('Xác nhận', f'Hủy đơn {ma}?'):
            if self.ql.huy_dat_tour(ma):
                luu_tat_ca(self.ql)
                messagebox.showinfo('Thông báo', 'Đã hủy đơn')
                self.refresh_lists()
                top.destroy()
    
    self.modal_buttons(container, [
        {'text':'Hủy đơn', 'style':'Danger.TButton', 'command':ok},
        {'text':'Đóng', 'style':'App.TButton', 'command':top.destroy}
    ])

def them_tour(self):
    if not self.quyen_admin():
        return
    top, container = self.create_modal('Thêm Tour mới', size=(1100, 720))
    header = ttk.Frame(container, style='Card.TFrame', padding=12)
    header.pack(fill='x', pady=(0,12))
    ttk.Label(header, text='THÊM TOUR MỚI', style='Title.TLabel').pack(anchor='w')
    ttk.Label(header, text='Nhập thông tin tour ở cột trái và xây dựng lịch trình chi tiết ở cột phải.', style='Body.TLabel').pack(anchor='w', pady=(4,0))

    workspace = ttk.Frame(container)
    workspace.pack(fill='both', expand=True)

    left_col = ttk.Frame(workspace)
    left_col.pack(side='left', fill='y', padx=(0,12))
    right_col = ttk.Frame(workspace)
    right_col.pack(side='left', fill='both', expand=True)

    entries = {}

    def add_entry(frame, text, name, row, default=''):
        ttk.Label(frame, text=text, style='Form.TLabel').grid(row=row, column=0, sticky='w', pady=4)
        widget = ttk.Entry(frame, font=self.font_body)
        if default:
            widget.insert(0, default)
        widget.grid(row=row, column=1, sticky='ew', padx=(8,0), pady=4)
        frame.columnconfigure(1, weight=1)
        entries[name] = widget

    basic = ttk.LabelFrame(left_col, text='Thông tin tour', style='Card.TLabelframe', padding=12)
    basic.pack(fill='x')
    add_entry(basic, 'Mã tour *', 'ma', 0)
    add_entry(basic, 'Tên tour *', 'ten', 1)
    gia_entry = add_entry(basic, 'Giá (VND) *', 'gia', 2)
    add_entry(basic, 'Số chỗ tối đa *', 'socho', 3)

    def format_gia(event=None):
        try:
            val = entries['gia'].get().replace(',', '').replace(' ', '')
            if val.isdigit():
                formatted = f"{int(val):,}".replace(',', ' ')
                entries['gia'].delete(0, tk.END)
                entries['gia'].insert(0, formatted)
        except:
            pass

    def unformat_gia(event=None):
        try:
            val = entries['gia'].get().replace(' ', '').replace(',', '')
            entries['gia'].delete(0, tk.END)
            entries['gia'].insert(0, val)
        except:
            pass

    entries['gia'].bind('<FocusOut>', format_gia)
    entries['gia'].bind('<FocusIn>', unformat_gia)

    meta = ttk.LabelFrame(left_col, text='Phân công & thời gian', style='Card.TLabelframe', padding=12)
    meta.pack(fill='x', pady=(12,0))
    ttk.Label(meta, text='Mã HDV', style='Form.TLabel').grid(row=0, column=0, sticky='w', pady=4)
    hdv_values = [h.get('maHDV', '') for h in getattr(self.ql, 'danh_sach_hdv', [])]
    hdv_combo = ttk.Combobox(meta, values=hdv_values, state='readonly', font=self.font_body)
    hdv_combo.grid(row=0, column=1, sticky='ew', padx=(8,0), pady=4)
    entries['hdv'] = hdv_combo

    hdv_name_label = ttk.Label(meta, text='', style='Body.TLabel')
    hdv_name_label.grid(row=1, column=0, columnspan=2, sticky='w')

    def update_hdv_name(event=None):
        ma_hdv = hdv_combo.get()
        if ma_hdv:
            hdv = next((h for h in getattr(self.ql, 'danh_sach_hdv', []) if str(h.get('maHDV', '')) == str(ma_hdv)), None)
            if hdv:
                hdv_name_label.config(text=f"Tên HDV: {hdv.get('tenHDV', '')}")
            else:
                hdv_name_label.config(text="")
        else:
            hdv_name_label.config(text="")

    hdv_combo.bind('<<ComboboxSelected>>', update_hdv_name)

    add_entry(meta, 'Ngày đi (DD/MM/YYYY, YYYY-MM-DD, etc.)', 'ngaydi', 2)
    add_entry(meta, 'Ngày về (DD/MM/YYYY, YYYY-MM-DD, etc.)', 'ngayve', 3)
    
    tu_dong_dinh_dang_ngay(entries['ngaydi'])
    tu_dong_dinh_dang_ngay(entries['ngayve'])

    ngay_di_format = ttk.Label(meta, text='', style='Body.TLabel')
    ngay_di_format.grid(row=4, column=0, columnspan=2, sticky='w')
    ngay_ve_format = ttk.Label(meta, text='', style='Body.TLabel')
    ngay_ve_format.grid(row=5, column=0, columnspan=2, sticky='w')

    def cap_nhat_dien_giai_ngay():
        d1 = self.ql.phan_tich_ngay(entries['ngaydi'].get())
        d2 = self.ql.phan_tich_ngay(entries['ngayve'].get())
        if d1:
            ngay_di_format.config(text=f"Ngày đi: {self.ql.dien_giai_ngay(d1)}")
        else:
            ngay_di_format.config(text="")
        if d2:
            ngay_ve_format.config(text=f"Ngày về: {self.ql.dien_giai_ngay(d2)}")
        else:
            ngay_ve_format.config(text="")

    entries['ngaydi'].bind('<FocusOut>', lambda e: cap_nhat_dien_giai_ngay())
    entries['ngayve'].bind('<FocusOut>', lambda e: cap_nhat_dien_giai_ngay())

    tips = ttk.LabelFrame(left_col, text='Ghi chú', style='Card.TLabelframe', padding=10)
    tips.pack(fill='x', pady=(12,0))
    ttk.Label(tips, text='Nhập các mốc lịch trình ở cột phải. Thời gian phải nằm trong khoảng ngày đi và ngày về.', style='Body.TLabel', wraplength=280, justify='left').pack(anchor='w')

    right_lich = ttk.LabelFrame(right_col, text='Biên tập lịch trình trực quan', style='Card.TLabelframe', padding=12)
    right_lich.pack(fill='both', expand=True)
    editor = self.build_inline_lich_editor(right_lich, initial=None)
    editor['frame'].pack(fill='both', expand=True)

    btn_bar = ttk.Frame(container, padding=(0,16,0,0))
    btn_bar.pack(fill='x')

    def ok():
        try:
            ma = entries['ma'].get().strip()
            ten = entries['ten'].get().strip()
            gia_str = entries['gia'].get().replace(' ', '').replace(',', '')
            gia = float(gia_str)
            socho = int(entries['socho'].get())
            hdv = entries['hdv'].get().strip()
            ngayDi = entries['ngaydi'].get().strip() or None
            ngayVe = entries['ngayve'].get().strip() or None
            lich = editor['get_items']()
            if not ma or not ten:
                raise Exception('Thiếu thông tin bắt buộc')
            d1 = self.ql.phan_tich_ngay(ngayDi) if ngayDi else None
            d2 = self.ql.phan_tich_ngay(ngayVe) if ngayVe else None
            if ngayDi and not d1:
                raise Exception('Ngày đi sai định dạng')
            if ngayVe and not d2:
                raise Exception('Ngày về sai định dạng')
            if d1 and d2 and d1 > d2:
                raise Exception('Ngày đi phải trước hoặc bằng ngày về')
            today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            if d1 and d1 < today:
                raise Exception('Không được đặt ngày đi trước ngày hệ thống')
            tour = TourDuLich(ma, ten, gia, socho, lich or [], hdv, ngay_di=ngayDi, ngay_ve=ngayVe)
            if ngayDi and ngayVe and lich:
                for entry in lich:
                    if 'ngay' in entry and entry['ngay']:
                        di = self.ql.phan_tich_ngay(entry['ngay'])
                        if not di:
                            raise Exception('Ngày trong lịch trình sai định dạng')
                        if di < d1 or di > d2:
                            raise Exception('Lịch trình ngoài phạm vi ngày tour')
        except Exception as e:
            messagebox.showerror('Lỗi', f'Dữ liệu không hợp lệ: {e}')
            return
        if self.ql.them_tour(tour):
            luu_tat_ca(self.ql)
            self.hien_thi_tour()
            top.destroy()
            messagebox.showinfo('Thành công', f'Đã thêm tour {ten}')

    ttk.Button(btn_bar, text='Lưu tour', style='Accent.TButton', command=ok).pack(side='left', padx=4)
    ttk.Button(btn_bar, text='Làm mới biểu mẫu', style='App.TButton', command=lambda: [w.delete(0, tk.END) for k, w in entries.items() if hasattr(w, 'delete') and k not in ('hdv',)]).pack(side='left', padx=4)
    ttk.Button(btn_bar, text='Đóng', style='Danger.TButton', command=top.destroy).pack(side='left', padx=4)

def sua_tour(self):
    if not self.quyen_admin():
        return
    sel = self.tv_tour.selection()
    if not sel:
        messagebox.showerror('Lỗi', 'Chưa chọn tour')
        return
    item = sel[0]
    values = self.tv_tour.item(item, 'values')
    t = self.ql.tim_tour(values[0])
    if not t:
        messagebox.showerror('Lỗi', 'Không tìm thấy tour')
        return
    top, container = self.create_modal(f'Sửa Tour: {t.ten_tour}', size=(820, 640))
    header = ttk.Frame(container, style='Card.TFrame')
    header.pack(fill='x', pady=(0,16))
    ttk.Label(header, text=f'CHỈNH SỬA TOUR: {t.ma_tour}', style='Title.TLabel').pack(anchor='w')
    ttk.Label(header, text='Cập nhật thông tin và lịch trình của tour', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    content = ttk.Frame(container)
    content.pack(fill='both', expand=True)
    left_form = ttk.LabelFrame(content, text='Thông tin cơ bản', style='Card.TLabelframe', padding=12)
    left_form.pack(side='left', fill='y', padx=(0,12))

    entries = {}

    ttk.Label(left_form, text='Tên tour *', style='Form.TLabel').grid(row=0, column=0, sticky='w', pady=4)
    ten_entry = ttk.Entry(left_form, font=self.font_body, width=24)
    ten_entry.insert(0, t.ten_tour)
    ten_entry.grid(row=0, column=1, sticky='ew', padx=(8,0), pady=4)
    entries['ten'] = ten_entry

    ttk.Label(left_form, text='Giá (VND) *', style='Form.TLabel').grid(row=1, column=0, sticky='w', pady=4)
    gia_entry = ttk.Entry(left_form, font=self.font_body, width=24)
    gia_entry.insert(0, str(t.gia_tour))
    gia_entry.grid(row=1, column=1, sticky='ew', padx=(8,0), pady=4)
    entries['gia'] = gia_entry

    def format_gia(event=None):
        try:
            val = entries['gia'].get().replace(',', '').replace(' ', '')
            if val.isdigit():
                formatted = f"{int(val):,}".replace(',', ' ')
                entries['gia'].delete(0, tk.END)
                entries['gia'].insert(0, formatted)
        except:
            pass

    def unformat_gia(event=None):
        try:
            val = entries['gia'].get().replace(' ', '').replace(',', '')
            entries['gia'].delete(0, tk.END)
            entries['gia'].insert(0, val)
        except:
            pass

    gia_entry.bind('<FocusOut>', format_gia)
    gia_entry.bind('<FocusIn>', unformat_gia)

    ttk.Label(left_form, text='Số chỗ tối đa *', style='Form.TLabel').grid(row=2, column=0, sticky='w', pady=4)
    socho_entry = ttk.Entry(left_form, font=self.font_body, width=24)
    socho_entry.insert(0, str(t.so_cho))
    socho_entry.grid(row=2, column=1, sticky='ew', padx=(8,0), pady=4)
    entries['socho'] = socho_entry

    ttk.Label(left_form, text='Mã HDV', style='Form.TLabel').grid(row=3, column=0, sticky='w', pady=4)
    hdv_values = [h.get('maHDV', '') for h in getattr(self.ql, 'danh_sach_hdv', [])]
    hdv_combo = ttk.Combobox(left_form, values=hdv_values, state='readonly', font=self.font_body, width=22)
    hdv_combo.set(str(t.huong_dan_vien or ''))
    hdv_combo.grid(row=3, column=1, sticky='ew', padx=(8,0), pady=4)
    entries['hdv'] = hdv_combo

    hdv_name_label = ttk.Label(left_form, text='', style='Body.TLabel')
    hdv_name_label.grid(row=4, column=0, columnspan=2, sticky='w')

    def update_hdv_name(event=None):
        ma_hdv = hdv_combo.get()
        if ma_hdv:
            hdv = next((h for h in getattr(self.ql, 'danh_sach_hdv', []) if str(h.get('maHDV', '')) == str(ma_hdv)), None)
            if hdv:
                hdv_name_label.config(text=f"Tên HDV: {hdv.get('tenHDV', '')}")
            else:
                hdv_name_label.config(text="")
        else:
            hdv_name_label.config(text="")

    hdv_combo.bind('<<ComboboxSelected>>', update_hdv_name)
    update_hdv_name()

    ttk.Label(left_form, text='Ngày đi (DD/MM/YYYY, YYYY-MM-DD, etc.)', style='Form.TLabel').grid(row=5, column=0, sticky='w', pady=4)
    ngaydi_entry = ttk.Entry(left_form, font=self.font_body, width=24)
    ngaydi_entry.insert(0, getattr(t, 'ngay_di', '') or '')
    ngaydi_entry.grid(row=5, column=1, sticky='ew', padx=(8,0), pady=4)
    entries['ngaydi'] = ngaydi_entry

    ttk.Label(left_form, text='Ngày về (DD/MM/YYYY, YYYY-MM-DD, etc.)', style='Form.TLabel').grid(row=6, column=0, sticky='w', pady=4)
    ngayve_entry = ttk.Entry(left_form, font=self.font_body, width=24)
    ngayve_entry.insert(0, getattr(t, 'ngay_ve', '') or '')
    ngayve_entry.grid(row=6, column=1, sticky='ew', padx=(8,0), pady=4)
    entries['ngayve'] = ngayve_entry

    tu_dong_dinh_dang_ngay(entries['ngaydi'])
    tu_dong_dinh_dang_ngay(entries['ngayve'])

    ngay_di_format = ttk.Label(left_form, text='', style='Body.TLabel')
    ngay_di_format.grid(row=7, column=0, columnspan=2, sticky='w')
    ngay_ve_format = ttk.Label(left_form, text='', style='Body.TLabel')
    ngay_ve_format.grid(row=8, column=0, columnspan=2, sticky='w')

    def cap_nhat_dien_giai_ngay():
        d1 = self.ql.phan_tich_ngay(entries['ngaydi'].get())
        d2 = self.ql.phan_tich_ngay(entries['ngayve'].get())
        if d1:
            ngay_di_format.config(text=f"Ngày đi: {self.ql.dien_giai_ngay(d1)}")
        else:
            ngay_di_format.config(text="")
        if d2:
            ngay_ve_format.config(text=f"Ngày về: {self.ql.dien_giai_ngay(d2)}")
        else:
            ngay_ve_format.config(text="")

    entries['ngaydi'].bind('<FocusOut>', lambda e: cap_nhat_dien_giai_ngay())
    entries['ngayve'].bind('<FocusOut>', lambda e: cap_nhat_dien_giai_ngay())
    cap_nhat_dien_giai_ngay()

    left_form.columnconfigure(1, weight=1)
    
    right_lich = ttk.LabelFrame(content, text='Lịch trình chi tiết', style='Card.TLabelframe', padding=12)
    right_lich.pack(side='left', fill='both', expand=True)
    editor = self.build_inline_lich_editor(right_lich, initial=t.lich_trinh)
    editor['frame'].pack(fill='both', expand=True)
    btn_bar = ttk.Frame(container, padding=(0,16,0,0))
    btn_bar.pack(fill='x')
    def ok():
        try:
            ten = entries['ten'].get().strip()
            gia_str = entries['gia'].get().replace(' ', '').replace(',', '')
            gia = float(gia_str)
            soCho = int(entries['socho'].get())
            hdv = entries['hdv'].get().strip()
            ngayDi = entries['ngaydi'].get().strip() or None
            ngayVe = entries['ngayve'].get().strip() or None
            lich = editor['get_items']()
            if not ten:
                raise Exception('Tên tour không được để trống')
            d1 = self.ql.phan_tich_ngay(ngayDi) if ngayDi else None
            d2 = self.ql.phan_tich_ngay(ngayVe) if ngayVe else None
            if ngayDi and not d1:
                raise Exception('Ngày đi sai định dạng')
            if ngayVe and not d2:
                raise Exception('Ngày về sai định dạng')
            if d1 and d2 and d1 > d2:
                raise Exception('Ngày đi phải trước hoặc bằng ngày về')
            today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            if d1 and d1 < today:
                raise Exception('Không được đặt ngày đi trước ngày hệ thống')
            if ngayDi and ngayVe and lich:
                for entry in lich:
                    if 'ngay' in entry and entry['ngay']:
                        di = self.ql.phan_tich_ngay(entry['ngay'])
                        if not di:
                            raise Exception('Ngày trong lịch trình sai định dạng')
                        if di < d1 or di > d2:
                            raise Exception('Lịch trình ngoài phạm vi ngày tour')
        except Exception as e:
            messagebox.showerror('Lỗi', f'Dữ liệu không hợp lệ: {e}')
            return
        if self.ql.cap_nhat_tour(t.ma_tour, ten_tour=ten, gia_tour=gia, so_cho=soCho, lich_trinh=lich, huong_dan_vien=hdv, ngay_di=ngayDi, ngay_ve=ngayVe):
            luu_tat_ca(self.ql)
            self.hien_thi_tour()
            top.destroy()
            messagebox.showinfo('Thành công', f'Đã cập nhật tour {ten}')
    ttk.Button(btn_bar, text='Cập nhật', style='Accent.TButton', command=ok).pack(side='left', padx=4)
    ttk.Button(btn_bar, text='Đóng', style='Danger.TButton', command=top.destroy).pack(side='left', padx=4)

def xoa_tour(self):
    if not self.quyen_admin():
        return
    sel = self.tv_tour.selection()
    if not sel:
        messagebox.showerror('Lỗi', 'Chưa chọn tour')
        return
    item = sel[0]
    values = self.tv_tour.item(item, 'values')
    t = self.ql.tim_tour(values[0])
    if not t:
        messagebox.showerror('Lỗi', 'Không tìm thấy tour')
        return
    if messagebox.askyesno('Xác nhận', f'Xóa tour {t.ten_tour}?'):
        if self.ql.xoa_tour(t.ma_tour):
            luu_tat_ca(self.ql)
            self.hien_thi_tour()

def them_khach(self):
    if not self.quyen_admin():
        return
    top, container = self.create_modal('Thêm khách hàng mới', size=(600, 500))
    header = ttk.Frame(container, style='Card.TFrame', padding=12)
    header.pack(fill='x', pady=(0,12))
    ttk.Label(header, text='THÊM KHÁCH HÀNG MỚI', style='Title.TLabel').pack(anchor='w')
    ttk.Label(header, text='Nhập đầy đủ thông tin khách hàng vào biểu mẫu bên dưới', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    
    form_frame = ttk.Frame(container)
    form_frame.pack(fill='both', expand=True, padx=12, pady=(0,12))
    
    ttk.Label(form_frame, text='Mã khách hàng *', style='Form.TLabel').grid(row=0, column=0, sticky='w', pady=8)
    ma_entry = ttk.Entry(form_frame, font=self.font_body)
    ma_entry.grid(row=0, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Họ và tên *', style='Form.TLabel').grid(row=1, column=0, sticky='w', pady=8)
    ten_entry = ttk.Entry(form_frame, font=self.font_body)
    ten_entry.grid(row=1, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Số điện thoại *', style='Form.TLabel').grid(row=2, column=0, sticky='w', pady=8)
    sdt_entry = ttk.Entry(form_frame, font=self.font_body)
    sdt_entry.grid(row=2, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Email *', style='Form.TLabel').grid(row=3, column=0, sticky='w', pady=8)
    email_entry = ttk.Entry(form_frame, font=self.font_body)
    email_entry.grid(row=3, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Số dư ban đầu (VND)', style='Form.TLabel').grid(row=4, column=0, sticky='w', pady=8)
    sodu_entry = ttk.Entry(form_frame, font=self.font_body)
    sodu_entry.grid(row=4, column=1, sticky='ew', padx=(12,0), pady=8)
    
    form_frame.columnconfigure(1, weight=1)
    
    entries = {'ma': ma_entry, 'ten': ten_entry, 'sdt': sdt_entry, 'email': email_entry, 'sodu': sodu_entry}
    
    def format_sodu(event=None):
        try:
            val = entries['sodu'].get().replace(',', '').replace(' ', '')
            if val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
                formatted = f"{int(val):,}".replace(',', ' ')
                entries['sodu'].delete(0, tk.END)
                entries['sodu'].insert(0, formatted)
        except:
            pass

    def unformat_sodu(event=None):
        try:
            val = entries['sodu'].get().replace(' ', '').replace(',', '')
            entries['sodu'].delete(0, tk.END)
            entries['sodu'].insert(0, val)
        except:
            pass

    sodu_entry.bind('<FocusOut>', format_sodu)
    sodu_entry.bind('<FocusIn>', unformat_sodu)
    
    help_frame = ttk.Frame(container, style='Card.TFrame', padding=8)
    help_frame.pack(fill='x', pady=(0,12))
    ttk.Label(help_frame, text='• Các trường đánh dấu (*) là bắt buộc phải nhập\n• Số dư có thể để trống (mặc định 0)', style='Body.TLabel', foreground='#52606d').pack(anchor='w')
    
    def ok():
        try:
            ma = entries['ma'].get().strip()
            ten = entries['ten'].get().strip()
            sdt = entries['sdt'].get().strip()
            email = entries['email'].get().strip()
            if not ma or not ten or not sdt or not email:
                messagebox.showerror('Lỗi', 'Vui lòng nhập đủ Mã KH, Họ tên, SĐT, Email')
                return
            if not self.ql.hop_le_so_dien_thoai_vn(sdt):
                messagebox.showerror('Lỗi', 'Số điện thoại phải 10 số, đúng đầu số VN')
                return
            so_du = float(_trich_chu_so_tho(entries['sodu'].get()) or 0)
        except Exception:
            messagebox.showerror('Lỗi', 'Số dư không hợp lệ')
            return
        kh = KhachHang(ma, ten, sdt, email, so_du)
        success, msg = self.ql.them_khach_hang(kh)
        if success:
            username = self.ql.ensure_user_for_khach(kh)
            luu_tat_ca(self.ql)
            self.hien_thi_khach()
            top.destroy()
            if username:
                messagebox.showinfo('Thành công', f'{msg}\nTài khoản: {username} / Mật khẩu mặc định: 123')
            else:
                messagebox.showinfo('Thành công', msg)
        else:
            messagebox.showerror('Lỗi', msg)
    
    self.modal_buttons(container, [
        {'text':'Lưu khách hàng', 'style':'Accent.TButton', 'command':ok},
        {'text':'Đóng', 'style':'Danger.TButton', 'command':top.destroy}
    ])

def dang_ky_guest(self):
    top, container = self.create_modal('Đăng ký tài khoản khách', size=(580, 480), maximize=False)
    form = ttk.Frame(container)
    form.pack(fill='x')
    fields = [
        {'name':'username','label':'Tên đăng nhập'},
        {'name':'password','label':'Mật khẩu','show':'*'},
        {'name':'fullname','label':'Tên khách'},
        {'name':'phone','label':'Số điện thoại (10 số)'},
        {'name':'email','label':'Email liên hệ'}
    ]
    entries = self.build_form_fields(form, fields)
    def ok():
        username = entries['username'].get().strip()
        password = entries['password'].get().strip()
        tenthat = entries['fullname'].get().strip()
        phone = entries['phone'].get().strip()
        email = entries['email'].get().strip()
        if not username or not password or not tenthat:
            messagebox.showerror('Lỗi', 'Điền đầy đủ thông tin')
            return
        if not self.ql.hop_le_so_dien_thoai_vn(phone):
            messagebox.showerror('Lỗi', 'Số điện thoại phải 10 số, đúng đầu số VN')
            return
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            messagebox.showerror('Lỗi', 'Email không hợp lệ')
            return
        existing = [
            int(k.ma_khach_hang.replace('KH',''))
            for k in self.ql.danh_sach_khach_hang
            if k.ma_khach_hang and k.ma_khach_hang.startswith('KH') and k.ma_khach_hang.replace('KH','').isdigit()
        ]
        nxt = (max(existing)+1) if existing else 1
        ma = f'KH{str(nxt).zfill(3)}'
        kh = KhachHang(ma, tenthat, phone, email, 0)
        success, msg = self.ql.them_khach_hang(kh, allow_public=True, auto_link_account=False)
        if not success:
            messagebox.showerror('Lỗi', msg)
            return
        success, msg = self.ql.dang_ky_nguoi_dung(username, password, role='user', ma_khach_hang=ma, ten_day_du=tenthat)
        if success:
            luu_tat_ca(self.ql)
            messagebox.showinfo('Thông báo', f'Đăng ký thành công. Tài khoản: {username}')
            top.destroy()
        else:
            self.ql.danh_sach_khach_hang = [k for k in self.ql.danh_sach_khach_hang if k.ma_khach_hang != ma]
            messagebox.showerror('Lỗi', msg)
    self.modal_buttons(container, [
        {'text':'Đăng ký', 'style':'Accent.TButton', 'command':ok},
        {'text':'Đóng', 'style':'Danger.TButton', 'command':top.destroy}
    ])

def dat_tour(self, preset_ma_kh=None):
    top, container = self.create_modal('Đặt tour cho khách hàng', size=(700, 600))
    header = ttk.Frame(container, style='Card.TFrame', padding=12)
    header.pack(fill='x', pady=(0,12))
    ttk.Label(header, text='ĐẶT TOUR CHO KHÁCH HÀNG', style='Title.TLabel').pack(anchor='w')
    if preset_ma_kh:
        ttk.Label(header, text=f'Tạo đơn đặt tour mới cho khách hàng {preset_ma_kh}', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    else:
        ttk.Label(header, text='Tạo đơn đặt tour mới trong hệ thống', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    
    form_frame = ttk.Frame(container)
    form_frame.pack(fill='both', expand=True, padx=12, pady=(0,12))
    
    ttk.Label(form_frame, text='Mã đặt *', style='Form.TLabel').grid(row=0, column=0, sticky='w', pady=8)
    madat_entry = ttk.Entry(form_frame, font=self.font_body)
    madat_entry.grid(row=0, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Mã tour *', style='Form.TLabel').grid(row=1, column=0, sticky='w', pady=8)
    matour_entry = ttk.Entry(form_frame, font=self.font_body)
    matour_entry.grid(row=1, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Số người *', style='Form.TLabel').grid(row=2, column=0, sticky='w', pady=8)
    songuoi_entry = ttk.Entry(form_frame, font=self.font_body)
    songuoi_entry.grid(row=2, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Ngày đặt', style='Form.TLabel').grid(row=3, column=0, sticky='w', pady=8)
    ngay_entry = ttk.Entry(form_frame, font=self.font_body)
    ngay_entry.grid(row=3, column=1, sticky='ew', padx=(12,0), pady=8)
    
    ttk.Label(form_frame, text='Mã khách hàng *', style='Form.TLabel').grid(row=4, column=0, sticky='w', pady=8)
    makh_entry = ttk.Entry(form_frame, font=self.font_body)
    makh_entry.grid(row=4, column=1, sticky='ew', padx=(12,0), pady=8)
    
    form_frame.columnconfigure(1, weight=1)
    
    entries = {'madat': madat_entry, 'matour': matour_entry, 'songuoi': songuoi_entry, 'ngay': ngay_entry, 'makh': makh_entry}
    
    if preset_ma_kh:
        makh_entry.delete(0, tk.END)
        makh_entry.insert(0, preset_ma_kh)
        makh_entry.configure(state='readonly')
    
    tu_dong_dinh_dang_ngay(entries['ngay'])
    
    kh_info_frame = ttk.LabelFrame(form_frame, text='Thông tin khách hàng', style='Card.TLabelframe', padding=8)
    kh_info_frame.grid(row=5, column=0, columnspan=2, sticky='ew', pady=(16,8))
    kh_info_label = ttk.Label(kh_info_frame, text='Số dư: - | Tên: -', style='Body.TLabel')
    kh_info_label.pack(anchor='w')
    
    tour_info_frame = ttk.LabelFrame(form_frame, text='Thông tin tour', style='Card.TLabelframe', padding=8)
    tour_info_frame.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(8,8))
    tour_info_label = ttk.Label(tour_info_frame, text='Giá: - | Tên: - | Còn chỗ: -', style='Body.TLabel')
    tour_info_label.pack(anchor='w')
    
    total_frame = ttk.LabelFrame(form_frame, text='Tổng tiền dự kiến', style='Card.TLabelframe', padding=8)
    total_frame.grid(row=7, column=0, columnspan=2, sticky='ew', pady=(8,8))
    total_label = ttk.Label(total_frame, text='Tổng: - VND', style='BodyBold.TLabel')
    total_label.pack(anchor='w')
    
    def cap_nhat_thong_tin():
        ma_kh = entries['makh'].get().strip()
        kh = next((k for k in getattr(self.ql, 'danh_sach_khach_hang', []) if k.ma_khach_hang == ma_kh), None)
        if kh:
            kh_info_label.config(text=f'Số dư: {self.format_money(kh.so_du)} | Tên: {kh.ten_khach_hang}')
        else:
            kh_info_label.config(text='Số dư: - | Tên: -')
        
        ma_tour = entries['matour'].get().strip()
        tour = self.ql.tim_tour(ma_tour)
        if tour:
            try:
                capacity = int(tour.so_cho)
                booked = sum(d.so_nguoi for d in self.ql.danh_sach_dat_tour if d.ma_tour == ma_tour and d.trang_thai == 'da_thanh_toan')
                remaining = max(0, capacity - booked)
            except:
                remaining = tour.so_cho if isinstance(tour.so_cho, int) else 0
            tour_info_label.config(text=f'Giá: {self.format_money(tour.gia_tour)} | Tên: {tour.ten_tour} | Còn chỗ: {remaining}')
        else:
            tour_info_label.config(text='Giá: - | Tên: - | Còn chỗ: -')
        
        try:
            so_nguoi = int(entries['songuoi'].get())
            if tour:
                total = so_nguoi * tour.gia_tour
                total_label.config(text=f'Tổng: {self.format_money(total)} VND')
            else:
                total_label.config(text='Tổng: - VND')
        except:
            total_label.config(text='Tổng: - VND')
    
    entries['makh'].bind('<FocusOut>', lambda e: cap_nhat_thong_tin())
    entries['matour'].bind('<FocusOut>', lambda e: cap_nhat_thong_tin())
    entries['songuoi'].bind('<FocusOut>', lambda e: cap_nhat_thong_tin())
    cap_nhat_thong_tin()
    
    help_frame = ttk.Frame(container, style='Card.TFrame', padding=8)
    help_frame.pack(fill='x', pady=(0,12))
    ttk.Label(help_frame, text='• Đảm bảo mã tour và mã khách hàng đã tồn tại trong hệ thống\n• Kiểm tra số dư khách hàng đủ để thanh toán', style='Body.TLabel', foreground='#52606d').pack(anchor='w')
    
    def ok():
        ma_khach_hang = entries['makh'].get() if self.ql.nguoi_dung_hien_tai and self.ql.nguoi_dung_hien_tai.vai_tro == 'admin' else (self.ql.nguoi_dung_hien_tai.ma_khach_hang if self.ql.nguoi_dung_hien_tai else '')
        try:
            madat = entries['madat'].get().strip()
            matour = entries['matour'].get().strip()
            songuoi = int(entries['songuoi'].get())
            ngay = entries['ngay'].get().strip()
            if not madat or not matour or not ma_khach_hang:
                messagebox.showerror('Lỗi', 'Vui lòng điền đầy đủ thông tin bắt buộc')
                return
            if ngay:
                parsed = self.ql.phan_tich_ngay(ngay)
                if not parsed:
                    messagebox.showerror('Lỗi', 'Ngày đặt không đúng định dạng')
                    return
            dt = DatTour(madat, ma_khach_hang, matour, songuoi, ngay)
        except ValueError:
            messagebox.showerror('Lỗi', 'Số người phải là số nguyên hợp lệ')
            return
        except Exception as e:
            messagebox.showerror('Lỗi', f'Dữ liệu không hợp lệ: {e}')
            return

        if self.ql.dat_tour_moi(dt):
            luu_tat_ca(self.ql)
            messagebox.showinfo('Thành công', f'Đã tạo đơn đặt tour {madat}')
            self.refresh_lists()
            top.destroy()
    
    self.modal_buttons(container, [
        {'text':'Đặt tour', 'style':'Accent.TButton', 'command':ok},
        {'text':'Đóng', 'style':'Danger.TButton', 'command':top.destroy}
    ])

def huy_dat(self, preset_ma_dat=None):
    top, container = self.create_modal('Hủy đặt tour')
    form = ttk.Frame(container)
    form.pack(fill='x')
    entries = self.build_form_fields(form, [{'name':'madat','label':'Mã đặt cần hủy'}])
    if preset_ma_dat:
        entries['madat'].delete(0, tk.END)
        entries['madat'].insert(0, preset_ma_dat)
        entries['madat'].configure(state='readonly')
    info_label = ttk.Label(form, text='', style='Body.TLabel')
    info_label.grid(row=1, column=0, columnspan=2, sticky='w', pady=(8,0))
    def cap_nhat_thong_tin_dat(evt=None):
        ma = entries['madat'].get().strip()
        d = next((dd for dd in getattr(self.ql, 'danh_sach_dat_tour', []) if dd.ma_dat_tour == ma), None)
        if not d:
            info_label.config(text='Không tìm thấy đơn đặt')
            return
        kh = next((k for k in getattr(self.ql, 'danh_sach_khach_hang', []) if k.ma_khach_hang == d.ma_khach_hang), None)
        bal = getattr(kh, 'so_du', 0) if kh else 0
        info_label.config(text=f'Khách: {d.ma_khach_hang} | Tour: {d.ma_tour} | Số người: {d.so_nguoi} | Số dư KH: {self.format_money(bal)}')
    entries['madat'].bind('<FocusOut>', cap_nhat_thong_tin_dat)
    cap_nhat_thong_tin_dat()
    def ok():
        if self.ql.huy_dat_tour(entries['madat'].get()):
            luu_tat_ca(self.ql)
            messagebox.showinfo('Thông báo', 'Hủy đặt thành công')
            self.refresh_lists()
            top.destroy()
        else:
            messagebox.showerror('Lỗi', 'Hủy thất bại')
    self.modal_buttons(container, [
        {'text':'Hủy đơn', 'style':'Danger.TButton', 'command':ok},
        {'text':'Đóng', 'style':'App.TButton', 'command':top.destroy}
    ])

def dang_xuat(self):
    luu_tat_ca(self.ql)
    self.ql.dang_xuat()
    try:
        try:
            self.stop_balance_updater()
        except Exception:
            pass
        self.root.unbind('<Configure>')
        self.root.state('normal')
        self.root.geometry('460x260')
    except Exception:
        pass
    self.build_dang_nhap()

def quyen_admin(self):
    if not self.ql.nguoi_dung_hien_tai or self.ql.nguoi_dung_hien_tai.vai_tro != 'admin':
        messagebox.showerror('Lỗi', 'Bạn không có quyền thực hiện!')
        return False
    return True

GiaoDienCoSo.sua_khach = sua_khach
GiaoDienCoSo.xoa_khach = xoa_khach
GiaoDienCoSo.get_selected_hdv = get_selected_hdv
GiaoDienCoSo.them_hdv = them_hdv
GiaoDienCoSo.sua_hdv = sua_hdv
GiaoDienCoSo.xoa_hdv = xoa_hdv
GiaoDienCoSo.dat_tour_for_customer = dat_tour_for_customer
GiaoDienCoSo.huy_dat_for_customer = huy_dat_for_customer
GiaoDienCoSo.them_tour = them_tour
GiaoDienCoSo.sua_tour = sua_tour
GiaoDienCoSo.xoa_tour = xoa_tour
GiaoDienCoSo.them_khach = them_khach
GiaoDienCoSo.dang_ky_guest = dang_ky_guest
GiaoDienCoSo.dat_tour = dat_tour
GiaoDienCoSo.huy_dat = huy_dat
GiaoDienCoSo.dang_xuat = dang_xuat
GiaoDienCoSo.quyen_admin = quyen_admin
