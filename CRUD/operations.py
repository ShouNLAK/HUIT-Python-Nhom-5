import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
from datetime import datetime
import json
import re
from Class.tour import Tour
from Class.khach_hang import KhachHang
from Class.dat_tour import DatTour
from QuanLy.storage import luu_tat_ca
from GUI.Login.base import GiaoDienCoSo


def tu_dong_dinh_dang_ngay(entry_widget):
    """Auto-format date entry: when user types 8 digits (e.g., 02122025), auto-insert slashes to make DD/MM/YYYY."""
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
    top, container = self.create_modal('Cập nhật khách hàng')
    form = ttk.Frame(container)
    form.pack(fill='x')
    fields = [
        {'name':'ten','label':'Họ và tên','default':kh.tenKH},
        {'name':'sdt','label':'Số điện thoại *','default':kh.soDT},
        {'name':'email','label':'Email','default':kh.email},
        {'name':'sodu','label':'Số dư','default':str(kh.soDu)}
    ]
    entries = self.build_form_fields(form, fields)

    def ok():
        ten = entries['ten'].get().strip()
        sdt = entries['sdt'].get().strip()
        email = entries['email'].get().strip()
        try:
            so_du = float(entries['sodu'].get())
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
        if self.ql.CapNhatKhachHang(maKH=kh.maKH, tenKH=ten, soDT=sdt, email=email, soDu=so_du):
            luu_tat_ca(self.ql)
            self.hien_thi_khach()
            top.destroy()

    self.modal_buttons(container, [
        {'text':'Lưu', 'style':'Accent.TButton', 'command':ok},
        {'text':'Đóng', 'style':'Danger.TButton', 'command':top.destroy}
    ])


def xoa_khach(self):
    if not self.quyen_admin():
        return
    kh = self.get_selected_customer()
    if not kh:
        return
    if messagebox.askyesno('Xác nhận', f'Xóa khách hàng {kh.tenKH}?'):
        if self.ql.XoaKhachHang(kh.maKH):
            self.ql.users = [u for u in self.ql.users if u.maKH != kh.maKH]
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
    if hasattr(self.ql, 'danhSachHDV'):
        return next((h for h in self.ql.danhSachHDV if str(h.get('maHDV')) == str(ma)), None)
    return None

def them_hdv(self):
    if not self.quyen_admin():
        return
    top, container = self.create_modal('Thêm hướng dẫn viên mới')
    
    header = ttk.Frame(container, style='Card.TFrame', padding=12)
    header.pack(fill='x', pady=(0,16))
    ttk.Label(header, text='THÊM HƯỚNG DẪN VIÊN MỚI', style='Title.TLabel').pack(anchor='w')
    ttk.Label(header, text='Nhập thông tin hướng dẫn viên để thêm vào hệ thống', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    
    form_card = ttk.LabelFrame(container, text='Thông tin hướng dẫn viên', style='Card.TLabelframe', padding=20)
    form_card.pack(fill='both', expand=True)
    
    fields = [
        {'name':'ma','label':'Mã HDV *', 'help': 'VD: HDV001'},
        {'name':'ten','label':'Họ và tên *', 'help': 'Tên đầy đủ'},
        {'name':'sdt','label':'Số điện thoại *', 'help': '10 số, đúng đầu số VN'},
        {'name':'exp','label':'Kinh nghiệm (năm) *', 'help': 'Số năm kinh nghiệm'}
    ]
    entries = self.build_form_fields(form_card, fields)
    
    help_frame = ttk.Frame(container, style='Card.TFrame', padding=8)
    help_frame.pack(fill='x', pady=(12,0))
    ttk.Label(help_frame, text='Tất cả các trường đều bắt buộc phải điền', style='Body.TLabel', foreground='#52606d').pack(anchor='w')
    
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
        if not hasattr(self.ql, 'danhSachHDV'):
            self.ql.danhSachHDV = []
        if any(str(h.get('maHDV')) == data['maHDV'] for h in self.ql.danhSachHDV):
            messagebox.showerror('Lỗi', 'Mã HDV đã tồn tại trong hệ thống')
            return
        if not self.ql.hop_le_so_dien_thoai_vn(data['sdt']):
            messagebox.showerror('Lỗi', 'Số điện thoại HDV phải 10 số, đúng đầu số VN')
            return
        self.ql.danhSachHDV.append(data)
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
    top, container = self.create_modal('Cập nhật HDV', size=(520, 360))
    form = ttk.Frame(container)
    form.pack(fill='x')
    fields = [
        {'name':'ten','label':'Tên HDV','default':hdv.get('tenHDV','')},
        {'name':'sdt','label':'Số điện thoại','default':hdv.get('sdt','')},
        {'name':'exp','label':'Kinh nghiệm (năm)','default':str(hdv.get('kinhNghiem',''))}
    ]
    entries = self.build_form_fields(form, fields)
    def ok():
        hdv['tenHDV'] = entries['ten'].get().strip()
        hdv['sdt'] = entries['sdt'].get().strip()
        hdv['kinhNghiem'] = entries['exp'].get().strip()
        if not self.ql.hop_le_so_dien_thoai_vn(hdv['sdt']):
            messagebox.showerror('Lỗi', 'Số điện thoại HDV phải 10 số, đúng đầu số VN')
            return
        self.ql.DongBoTenTuHDV(hdv.get('maHDV'))
        self.ql.ensure_user_for_hdv(hdv)
        luu_tat_ca(self.ql)
        self.hien_thi_hdv()
        top.destroy()
    self.modal_buttons(container, [
        {'text':'Lưu', 'style':'Accent.TButton', 'command':ok},
        {'text':'Đóng', 'style':'Danger.TButton', 'command':top.destroy}
    ])

def xoa_hdv(self):
    if not self.quyen_admin():
        return
    hdv = self.get_selected_hdv()
    if not hdv:
        return
    if messagebox.askyesno('Xác nhận', f'Xóa HDV {hdv.get("tenHDV","")}?'):
        self.ql.danhSachHDV = [h for h in self.ql.danhSachHDV if h is not hdv]
        self.ql.users = [u for u in self.ql.users if not (u.role == 'hdv' and u.maKH == hdv.get('maHDV'))]
        luu_tat_ca(self.ql)
        self.hien_thi_hdv()

def dat_tour_for_customer(self, ma_kh):
    self.dat_tour(preset_ma_kh=ma_kh)

def huy_dat_for_customer(self, ma_kh):
    ds = [d for d in self.ql.danhSachDatTour if d.maKH == ma_kh]
    if not ds:
        messagebox.showinfo('Thông báo', 'Khách hàng chưa có đơn')
        return
    top, container = self.create_modal('Chọn đơn để hủy', size=(620, 400))
    tv = ttk.Treeview(container, columns=('MaDat','MaTour','TrangThai','Tong'), show='headings')
    for col, text, w in (('MaDat','Mã đặt',140),('MaTour','Mã tour',120),('TrangThai','Trạng thái',140),('Tong','Tổng',140)):
        tv.heading(col, text=text)
        tv.column(col, width=w, anchor='center')
    scr = ttk.Scrollbar(container, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    for d in ds:
        tv.insert('', tk.END, values=(d.maDat, d.maTour, d.trangThai, self.format_money(d.tongTien)))
    self.apply_zebra(tv)
    def ok():
        sel = tv.selection()
        if not sel:
            messagebox.showwarning('Chú ý', 'Chọn một đơn để hủy')
            return
        ma = tv.item(sel[0], 'values')[0]
        if self.ql.HuyDatTour(ma):
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
    add_entry(basic, 'Giá (VND) *', 'gia', 2)
    add_entry(basic, 'Số chỗ tối đa *', 'socho', 3)

    meta = ttk.LabelFrame(left_col, text='Phân công & thời gian', style='Card.TLabelframe', padding=12)
    meta.pack(fill='x', pady=(12,0))
    ttk.Label(meta, text='Mã HDV', style='Form.TLabel').grid(row=0, column=0, sticky='w', pady=4)
    hdv_values = [h.get('maHDV', '') for h in getattr(self.ql, 'danhSachHDV', [])]
    hdv_combo = ttk.Combobox(meta, values=hdv_values, state='readonly', font=self.font_body)
    hdv_combo.grid(row=0, column=1, sticky='ew', padx=(8,0), pady=4)
    entries['hdv'] = hdv_combo
    add_entry(meta, 'Ngày đi (DD/MM/YYYY)', 'ngaydi', 1)
    add_entry(meta, 'Ngày về (DD/MM/YYYY)', 'ngayve', 2)
    
    tu_dong_dinh_dang_ngay(entries['ngaydi'])
    tu_dong_dinh_dang_ngay(entries['ngayve'])

    ngay_format = ttk.Label(meta, text='', style='Body.TLabel')
    ngay_format.grid(row=3, column=0, columnspan=2, sticky='w')

    def cap_nhat_dien_giai_ngay():
        d1 = self.ql.phan_tich_ngay(entries['ngaydi'].get())
        d2 = self.ql.phan_tich_ngay(entries['ngayve'].get())
        parts = []
        if d1:
            parts.append(f"Đi: {self.ql.dien_giai_ngay(d1)}")
        if d2:
            parts.append(f"Về: {self.ql.dien_giai_ngay(d2)}")
        ngay_format.config(text=' | '.join(parts))

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
            gia = float(entries['gia'].get())
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
                raise Exception('Ngày đi sai định dạng (DD/MM/YYYY)')
            if ngayVe and not d2:
                raise Exception('Ngày về sai định dạng (DD/MM/YYYY)')
            today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            if d1 and d1 < today:
                raise Exception('Không được đặt ngày đi trước ngày hệ thống')
            tour = Tour(ma, ten, gia, socho, lich or [], hdv, ngayDi=ngayDi, ngayVe=ngayVe)
            if ngayDi and ngayVe and lich:
                for entry in lich:
                    if 'ngay' in entry and entry['ngay']:
                        di = self.ql.phan_tich_ngay(entry['ngay'])
                        if not di:
                            raise Exception('Ngày trong lịch trình sai định dạng (DD/MM/YYYY)')
                        if di < d1 or di > d2:
                            raise Exception('Lịch trình ngoài phạm vi ngày tour')
        except Exception as e:
            messagebox.showerror('Lỗi', f'Dữ liệu không hợp lệ: {e}')
            return
        if self.ql.ThemTour(tour):
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
    t = self.ql.TimTour(values[0])
    if not t:
        messagebox.showerror('Lỗi', 'Không tìm thấy tour')
        return
    top, container = self.create_modal(f'Sửa Tour: {t.tenTour}', size=(820, 640))
    header = ttk.Frame(container, style='Card.TFrame')
    header.pack(fill='x', pady=(0,16))
    ttk.Label(header, text=f'CHỈNH SỬA TOUR: {t.maTour}', style='Title.TLabel').pack(anchor='w')
    ttk.Label(header, text='Cập nhật thông tin và lịch trình của tour', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    content = ttk.Frame(container)
    content.pack(fill='both', expand=True)
    left_form = ttk.LabelFrame(content, text='Thông tin cơ bản', style='Card.TLabelframe', padding=12)
    left_form.pack(side='left', fill='y', padx=(0,12))
    field_data = [
        ('Tên tour *', 'ten', t.tenTour),
        ('Giá (VND) *', 'gia', str(t.gia)),
        ('Số chỗ tối đa *', 'socho', str(t.soCho)),
        ('Mã HDV', 'hdv', str(t.huongDanVien or '')),
        ('Ngày đi (DD/MM/YYYY)', 'ngaydi', getattr(t,'ngayDi','') or ''),
        ('Ngày về (DD/MM/YYYY)', 'ngayve', getattr(t,'ngayVe','') or '')
    ]
    entries = {}
    for idx, (label, name, default) in enumerate(field_data):
        ttk.Label(left_form, text=label, style='Form.TLabel').grid(row=idx, column=0, sticky='w', pady=4)
        e = ttk.Entry(left_form, font=self.font_body, width=24)
        if default:
            e.insert(0, default)
        e.grid(row=idx, column=1, sticky='ew', padx=(8,0), pady=4)
        entries[name] = e
    left_form.columnconfigure(1, weight=1)
    
    tu_dong_dinh_dang_ngay(entries['ngaydi'])
    tu_dong_dinh_dang_ngay(entries['ngayve'])
    
    right_lich = ttk.LabelFrame(content, text='Lịch trình chi tiết', style='Card.TLabelframe', padding=12)
    right_lich.pack(side='left', fill='both', expand=True)
    editor = self.build_inline_lich_editor(right_lich, initial=t.lichTrinh)
    editor['frame'].pack(fill='both', expand=True)
    btn_bar = ttk.Frame(container, padding=(0,16,0,0))
    btn_bar.pack(fill='x')
    def ok():
        try:
            ten = entries['ten'].get().strip()
            gia = float(entries['gia'].get())
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
                raise Exception('Ngày đi sai định dạng (DD/MM/YYYY)')
            if ngayVe and not d2:
                raise Exception('Ngày về sai định dạng (DD/MM/YYYY)')
            today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
            if d1 and d1 < today:
                raise Exception('Không được đặt ngày đi trước ngày hệ thống')
            if ngayDi and ngayVe and lich:
                for entry in lich:
                    if 'ngay' in entry and entry['ngay']:
                        di = self.ql.phan_tich_ngay(entry['ngay'])
                        if not di:
                            raise Exception('Ngày trong lịch trình sai định dạng (DD/MM/YYYY)')
                        if di < d1 or di > d2:
                            raise Exception('Lịch trình ngoài phạm vi ngày tour')
        except Exception as e:
            messagebox.showerror('Lỗi', f'Dữ liệu không hợp lệ: {e}')
            return
        if self.ql.CapNhatTour(t.maTour, tenTour=ten, gia=gia, soCho=soCho, lichTrinh=lich, huongDanVien=hdv, ngayDi=ngayDi, ngayVe=ngayVe):
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
    t = self.ql.TimTour(values[0])
    if not t:
        messagebox.showerror('Lỗi', 'Không tìm thấy tour')
        return
    if messagebox.askyesno('Xác nhận', f'Xóa tour {t.tenTour}?'):
        if self.ql.XoaTour(t.maTour):
            luu_tat_ca(self.ql)
            self.hien_thi_tour()

def them_khach(self):
    if not self.quyen_admin():
        return
    top, container = self.create_modal('Thêm khách hàng mới')
    header = ttk.Frame(container, style='Card.TFrame', padding=12)
    header.pack(fill='x', pady=(0,16))
    ttk.Label(header, text='THÊM KHÁCH HÀNG MỚI', style='Title.TLabel').pack(anchor='w')
    ttk.Label(header, text='Nhập đầy đủ thông tin khách hàng vào biểu mẫu bên dưới', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    
    form_card = ttk.LabelFrame(container, text='Thông tin khách hàng', style='Card.TLabelframe', padding=20)
    form_card.pack(fill='both', expand=True)
    
    fields = [
        {'name':'ma','label':'Mã khách hàng *', 'help': 'VD: KH001'},
        {'name':'ten','label':'Họ và tên *', 'help': 'Tên đầy đủ của khách hàng'},
        {'name':'sdt','label':'Số điện thoại *', 'help': '10 số, đúng đầu số VN'},
        {'name':'email','label':'Email', 'help': 'Địa chỉ email'},
        {'name':'sodu','label':'Số dư ban đầu (VND)', 'help': 'Số tiền ban đầu trong ví'}
    ]
    entries = self.build_form_fields(form_card, fields)
    
    help_frame = ttk.Frame(container, style='Card.TFrame', padding=8)
    help_frame.pack(fill='x', pady=(12,0))
    ttk.Label(help_frame, text='Các trường đánh dấu (*) là bắt buộc phải nhập', style='Body.TLabel', foreground='#52606d').pack(anchor='w')
    
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
            soDu = float(entries['sodu'].get()) if entries['sodu'].get() else 0
        except Exception:
            messagebox.showerror('Lỗi', 'Số dư không hợp lệ')
            return
        kh = KhachHang(ma, ten, sdt, email, soDu)
        if self.ql.ThemKhachHang(kh):
            username = self.ql.ensure_user_for_khach(kh)
            luu_tat_ca(self.ql)
            self.hien_thi_khach()
            top.destroy()
            if username:
                messagebox.showinfo('Thành công', f'Đã thêm khách hàng {ten}\nTài khoản: {username} / Mật khẩu mặc định: 123')
            else:
                messagebox.showinfo('Thành công', f'Đã thêm khách hàng {ten}')
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
            int(k.maKH.replace('KH',''))
            for k in self.ql.danhSachKhachHang
            if k.maKH and k.maKH.startswith('KH') and k.maKH.replace('KH','').isdigit()
        ]
        nxt = (max(existing)+1) if existing else 1
        ma = f'KH{str(nxt).zfill(3)}'
        kh = KhachHang(ma, tenthat, phone, email, 0)
        if not self.ql.ThemKhachHang(kh, allow_public=True, auto_link_account=False):
            messagebox.showerror('Lỗi', 'Không tạo được khách hàng mới')
            return
        success, msg = self.ql.DangKyUser(username, password, role='user', maKH=ma, fullName=tenthat)
        if success:
            luu_tat_ca(self.ql)
            messagebox.showinfo('Thông báo', f'Đăng ký thành công. Tài khoản: {username}')
            top.destroy()
        else:
            self.ql.danhSachKhachHang = [k for k in self.ql.danhSachKhachHang if k.maKH != ma]
            messagebox.showerror('Lỗi', msg)
    self.modal_buttons(container, [
        {'text':'Đăng ký', 'style':'Accent.TButton', 'command':ok},
        {'text':'Đóng', 'style':'Danger.TButton', 'command':top.destroy}
    ])

def dat_tour(self, preset_ma_kh=None):
    top, container = self.create_modal('Đặt tour cho khách hàng')
    header = ttk.Frame(container, style='Card.TFrame', padding=12)
    header.pack(fill='x', pady=(0,16))
    ttk.Label(header, text='ĐẶT TOUR CHO KHÁCH HÀNG', style='Title.TLabel').pack(anchor='w')
    if preset_ma_kh:
        ttk.Label(header, text=f'Tạo đơn đặt tour mới cho khách hàng {preset_ma_kh}', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    else:
        ttk.Label(header, text='Tạo đơn đặt tour mới trong hệ thống', style='Body.TLabel').pack(anchor='w', pady=(4,0))
    
    form_card = ttk.LabelFrame(container, text='Thông tin đơn đặt', style='Card.TLabelframe', padding=20)
    form_card.pack(fill='both', expand=True)
    
    fields = [
        {'name':'madat','label':'Mã đặt *', 'help': 'VD: DT001'},
        {'name':'matour','label':'Mã tour *', 'help': 'Mã tour muốn đặt'},
        {'name':'songuoi','label':'Số người *', 'help': 'Số lượng người tham gia'},
        {'name':'ngay','label':'Ngày đặt', 'help': 'DD/MM/YYYY'},
        {'name':'makh','label':'Mã khách hàng *', 'help': 'Mã KH đặt tour'}
    ]
    entries = self.build_form_fields(form_card, fields)
    if preset_ma_kh:
        entries['makh'].delete(0, tk.END)
        entries['makh'].insert(0, preset_ma_kh)
        entries['makh'].configure(state='readonly')
    
    tu_dong_dinh_dang_ngay(entries['ngay'])
    
    help_frame = ttk.Frame(container, style='Card.TFrame', padding=8)
    help_frame.pack(fill='x', pady=(12,0))
    ttk.Label(help_frame, text='Đảm bảo mã tour và mã khách hàng đã tồn tại trong hệ thống', style='Body.TLabel', foreground='#52606d').pack(anchor='w')
    
    def ok():
        maKH = entries['makh'].get() if self.ql.currentUser and self.ql.currentUser.role == 'admin' else (self.ql.currentUser.maKH if self.ql.currentUser else '')
        try:
            madat = entries['madat'].get().strip()
            matour = entries['matour'].get().strip()
            songuoi = int(entries['songuoi'].get())
            ngay = entries['ngay'].get().strip()
            if not madat or not matour or not maKH:
                messagebox.showerror('Lỗi', 'Vui lòng điền đầy đủ thông tin bắt buộc')
                return
            if ngay:
                parsed = self.ql.phan_tich_ngay(ngay)
                if not parsed:
                    messagebox.showerror('Lỗi', 'Ngày đặt không đúng định dạng (DD/MM/YYYY)')
                    return
            dt = DatTour(madat, maKH, matour, songuoi, ngay)
        except ValueError:
            messagebox.showerror('Lỗi', 'Số người phải là số nguyên hợp lệ')
            return
        except Exception as e:
            messagebox.showerror('Lỗi', f'Dữ liệu không hợp lệ: {e}')
            return

        if self.ql.DatTourMoi(dt):
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
    def ok():
        if self.ql.HuyDatTour(entries['madat'].get()):
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
    self.ql.Logout()
    try:
        self.root.state('normal')
        self.root.geometry('460x260')
    except Exception:
        pass
    self.build_dang_nhap()

def quyen_admin(self):
    if not self.ql.currentUser or self.ql.currentUser.role != 'admin':
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
