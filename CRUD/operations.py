import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
from datetime import datetime
import json
from Class.tour import Tour
from Class.khach_hang import KhachHang
from Class.user import User
from Class.dat_tour import DatTour
from QuanLy.storage import luu_tat_ca
from GUI.Login.base import GiaoDienCoSo

def sua_khach(self):
    if not self.quyen_admin():
        return
    kh = self.get_selected_customer()
    if not kh:
        return
    top, container = self.create_modal('Cập nhật khách hàng', size=(520, 360))
    form = ttk.Frame(container)
    form.pack(fill='x')
    fields = [
        {'name':'ten','label':'Tên khách','default':kh.tenKH},
        {'name':'sdt','label':'Số điện thoại','default':kh.soDT},
        {'name':'email','label':'Email','default':kh.email},
        {'name':'sodu','label':'Số dư','default':str(kh.soDu)}
    ]
    entries = self.build_form_fields(form, fields)
    def ok():
        ten = entries['ten'].get()
        sdt = entries['sdt'].get()
        email = entries['email'].get()
        try:
            so_du = float(entries['sodu'].get())
        except Exception:
            messagebox.showerror('Lỗi', 'Số dư không hợp lệ')
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
        {'name':'sdt','label':'Số điện thoại *', 'help': 'SĐT liên lạc'},
        {'name':'exp','label':'Kinh nghiệm (năm) *', 'help': 'Số năm kinh nghiệm'}
    ]
    entries = self.build_form_fields(form_card, fields)
    
    help_frame = ttk.Frame(container, style='Card.TFrame', padding=8)
    help_frame.pack(fill='x', pady=(12,0))
    ttk.Label(help_frame, text='💡 Tất cả các trường đều bắt buộc phải điền', style='Body.TLabel', foreground='#52606d').pack(anchor='w')
    
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
        self.ql.danhSachHDV.append(data)
        luu_tat_ca(self.ql)
        self.hien_thi_hdv()
        top.destroy()
        messagebox.showinfo('Thành công', f'Đã thêm HDV {data["tenHDV"]}')
    self.modal_buttons(container, [
        {'text':'💾 Thêm HDV', 'style':'Accent.TButton', 'command':ok},
        {'text':'❌ Đóng', 'style':'Danger.TButton', 'command':top.destroy}
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
    add_entry(meta, 'Ngày đi (YYYY-MM-DD)', 'ngaydi', 1)
    add_entry(meta, 'Ngày về (YYYY-MM-DD)', 'ngayve', 2)

    tips = ttk.LabelFrame(left_col, text='Ghi chú', style='Card.TLabelframe', padding=10)
    tips.pack(fill='x', pady=(12,0))
    ttk.Label(tips, text='• Sử dụng lịch trình bên phải để thêm các mốc cụ thể\n• Thời gian trong lịch trình nên nằm trong khoảng ngày đi/đến', style='Body.TLabel', wraplength=280, justify='left').pack(anchor='w')

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
            tour = Tour(ma, ten, gia, socho, lich or [], hdv, ngayDi=ngayDi, ngayVe=ngayVe)
            if ngayDi and ngayVe and lich:
                d1 = datetime.strptime(ngayDi, '%Y-%m-%d')
                d2 = datetime.strptime(ngayVe, '%Y-%m-%d')
                for entry in lich:
                    if 'ngay' in entry and entry['ngay']:
                        di = datetime.strptime(entry['ngay'], '%Y-%m-%d')
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
        ('Ngày đi (YYYY-MM-DD)', 'ngaydi', getattr(t,'ngayDi','') or ''),
        ('Ngày về (YYYY-MM-DD)', 'ngayve', getattr(t,'ngayVe','') or '')
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
            if ngayDi and ngayVe and lich:
                d1 = datetime.strptime(ngayDi, '%Y-%m-%d')
                d2 = datetime.strptime(ngayVe, '%Y-%m-%d')
                for entry in lich:
                    if 'ngay' in entry and entry['ngay']:
                        di = datetime.strptime(entry['ngay'], '%Y-%m-%d')
                        if di < d1 or di > d2:
                            raise Exception('Lịch trình ngoài phạm vi ngày tour')
        except Exception as e:
            messagebox.showerror('Lỗi', f'Dữ liệu không hợp lệ: {e}')
            return
        if self.ql.CapNhatTour(t.maTour, tenTour=ten, gia=gia, soCho=soCho, lichTrinh=lich, huongDanVien=hdv):
            for tour in self.ql.danhSachTour:
                if tour.maTour == t.maTour:
                    tour.ngayDi = ngayDi
                    tour.ngayVe = ngayVe
                    break
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
        {'name':'sdt','label':'Số điện thoại', 'help': 'Số điện thoại liên lạc'},
        {'name':'email','label':'Email', 'help': 'Địa chỉ email'},
        {'name':'sodu','label':'Số dư ban đầu (VND)', 'help': 'Số tiền ban đầu trong ví'}
    ]
    entries = self.build_form_fields(form_card, fields)
    
    help_frame = ttk.Frame(container, style='Card.TFrame', padding=8)
    help_frame.pack(fill='x', pady=(12,0))
    ttk.Label(help_frame, text='💡 Gợi ý: Các trường đánh dấu (*) là bắt buộc phải nhập', style='Body.TLabel', foreground='#52606d').pack(anchor='w')
    
    def ok():
        try:
            ma = entries['ma'].get().strip()
            ten = entries['ten'].get().strip()
            sdt = entries['sdt'].get().strip()
            email = entries['email'].get().strip()
            if not ma or not ten:
                messagebox.showerror('Lỗi', 'Vui lòng nhập đầy đủ thông tin bắt buộc (Mã KH, Họ tên)')
                return
            soDu = float(entries['sodu'].get()) if entries['sodu'].get() else 0
        except Exception:
            messagebox.showerror('Lỗi', 'Số dư không hợp lệ')
            return
        kh = KhachHang(ma, ten, sdt, email, soDu)
        if self.ql.ThemKhachHang(kh):
            luu_tat_ca(self.ql)
            self.hien_thi_khach()
            top.destroy()
            messagebox.showinfo('Thành công', f'Đã thêm khách hàng {ten}')
    self.modal_buttons(container, [
        {'text':'💾 Lưu khách hàng', 'style':'Accent.TButton', 'command':ok},
        {'text':'❌ Đóng', 'style':'Danger.TButton', 'command':top.destroy}
    ])

def dang_ky_guest(self):
    top, container = self.create_modal('Đăng ký tài khoản khách')
    form = ttk.Frame(container)
    form.pack(fill='x')
    fields = [
        {'name':'username','label':'Tên đăng nhập'},
        {'name':'password','label':'Mật khẩu','show':'*'},
        {'name':'fullname','label':'Tên khách'}
    ]
    entries = self.build_form_fields(form, fields)
    def ok():
        username = entries['username'].get()
        password = entries['password'].get()
        tenthat = entries['fullname'].get()
        if not username or not password or not tenthat:
            messagebox.showerror('Lỗi', 'Điền đầy đủ thông tin')
            return
        existing = [int(k.maKH.replace('KH','')) for k in self.ql.danhSachKhachHang if k.maKH and k.maKH.startswith('KH')]
        nxt = (max(existing)+1) if existing else 1
        ma = f'KH{str(nxt).zfill(3)}'
        kh = KhachHang(ma, tenthat, '', '', 0)
        if self.ql.ThemKhachHang(kh):
            self.ql.users.append(User(username, password, 'user', ma))
            luu_tat_ca(self.ql)
            messagebox.showinfo('Thông báo', f'Đăng ký thành công. Tài khoản: {username}')
            top.destroy()
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
        {'name':'ngay','label':'Ngày đặt', 'help': 'YYYY-MM-DD'},
        {'name':'makh','label':'Mã khách hàng *', 'help': 'Mã KH đặt tour'}
    ]
    entries = self.build_form_fields(form_card, fields)
    if preset_ma_kh:
        entries['makh'].delete(0, tk.END)
        entries['makh'].insert(0, preset_ma_kh)
        entries['makh'].configure(state='readonly')
    
    help_frame = ttk.Frame(container, style='Card.TFrame', padding=8)
    help_frame.pack(fill='x', pady=(12,0))
    ttk.Label(help_frame, text='💡 Đảm bảo mã tour và mã khách hàng đã tồn tại trong hệ thống', style='Body.TLabel', foreground='#52606d').pack(anchor='w')
    
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
        {'text':'✅ Đặt tour', 'style':'Accent.TButton', 'command':ok},
        {'text':'❌ Đóng', 'style':'Danger.TButton', 'command':top.destroy}
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
