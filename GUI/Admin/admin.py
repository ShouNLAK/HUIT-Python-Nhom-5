import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import filedialog
import json
from Class.tour import Tour
from QuanLy.storage import luu_tat_ca
from GUI.Login.base import GiaoDienCoSo

def show_hdv_details(self, event=None):
    if not self.tv_hdv:
        return
    sel = self.tv_hdv.selection()
    if not sel:
        return
    values = self.tv_hdv.item(sel[0], 'values')
    if not values:
        return
    ma = values[0]
    hdv = None
    if hasattr(self.ql, 'danhSachHDV'):
        hdv = next((h for h in self.ql.danhSachHDV if str(h.get('maHDV', '')) == str(ma)), None)
    if not hdv:
        messagebox.showerror('Lỗi', 'Không tìm thấy thông tin HDV')
        return
    tours = [t for t in self.ql.danhSachTour if str(t.huongDanVien) == str(ma)]
    tour_ids = {t.maTour for t in tours}
    bookings = [d for d in self.ql.danhSachDatTour if d.maTour in tour_ids]
    passengers = []
    for d in bookings:
        kh = self.ql.TimKhacHang(d.maKH)
        passengers.append({
            'maKH': d.maKH,
            'tenKH': kh.tenKH if kh else 'N/A',
            'maTour': d.maTour,
            'soNguoi': d.soNguoi,
            'trangThai': d.trangThai
        })
    top, container = self.create_modal(f"Chi tiết HDV: {hdv.get('tenHDV', '')}", size=(820, 560))
    ttk.Label(container, text='THẺ HƯỚNG DẪN VIÊN', style='Title.TLabel').pack(anchor='w', pady=(0,12))

    tabs = ttk.Notebook(container)
    tabs.pack(fill='both', expand=True)

    info_tab = ttk.Frame(tabs, style='App.TFrame', padding=10)
    tours_tab = ttk.Frame(tabs, style='App.TFrame', padding=10)
    tabs.add(info_tab, text='Thông tin cá nhân')
    tabs.add(tours_tab, text='Tour phụ trách')

    info_card = ttk.Frame(info_tab, style='Card.TFrame', padding=12)
    info_card.pack(fill='both', expand=True)
    ttk.Label(info_card, text=f"Mã HDV: {hdv.get('maHDV', '')}", style='BodyBold.TLabel').grid(row=0, column=0, sticky='w', pady=4)
    ttk.Label(info_card, text=f"Họ tên: {hdv.get('tenHDV', '')}", style='Body.TLabel').grid(row=1, column=0, sticky='w', pady=4)
    ttk.Label(info_card, text=f"SĐT: {hdv.get('sdt', '')}", style='Body.TLabel').grid(row=2, column=0, sticky='w', pady=4)
    ttk.Label(info_card, text=f"Kinh nghiệm: {hdv.get('kinhNghiem', '')} năm", style='Body.TLabel').grid(row=3, column=0, sticky='w', pady=4)
    total_passengers = sum(p['soNguoi'] for p in passengers)
    ttk.Label(info_card, text=f"Số tour đang phụ trách: {len(tours)}", style='BodyBold.TLabel').grid(row=4, column=0, sticky='w', pady=(12,4))
    ttk.Label(info_card, text=f"Tổng lượt khách đã dẫn: {total_passengers}", style='Body.TLabel').grid(row=5, column=0, sticky='w')
    info_card.columnconfigure(0, weight=1)

    tour_container = ttk.Frame(tours_tab, style='App.TFrame')
    tour_container.pack(fill='both', expand=True)

    summary_card = ttk.Frame(tour_container, style='Card.TFrame', padding=12)
    summary_card.pack(fill='x', pady=(0,12))
    ttk.Label(summary_card, text=f'📋 Tổng số tour phụ trách: {len(tours)}', style='BodyBold.TLabel').pack(side='left', padx=12)
    ttk.Label(summary_card, text=f'👥 Tổng lượt khách: {sum(p["soNguoi"] for p in passengers)}', style='Body.TLabel').pack(side='left', padx=12)

    tour_frame = ttk.LabelFrame(tour_container, text='Danh sách tour được phân công', style='Card.TLabelframe', padding=12)
    tour_frame.pack(fill='both', expand=True)

    tv_tour = ttk.Treeview(tour_frame, columns=('Ma', 'Ten', 'NgayDi', 'NgayVe', 'Gia', 'ConCho', 'DaDat'), show='headings')
    headers = {
        'Ma': ('Mã Tour', 100, 'center'),
        'Ten': ('Tên Tour', 280, 'w'),
        'NgayDi': ('Khởi hành', 110, 'center'),
        'NgayVe': ('Kết thúc', 110, 'center'),
        'Gia': ('Giá', 120, 'center'),
        'ConCho': ('Còn chỗ', 90, 'center'),
        'DaDat': ('Đã đặt', 90, 'center')
    }
    for key, (text, width, anchor) in headers.items():
        tv_tour.heading(key, text=text)
        tv_tour.column(key, width=width, anchor=anchor)
    tour_scroll = ttk.Scrollbar(tour_frame, orient='vertical', command=tv_tour.yview)
    tv_tour.configure(yscrollcommand=tour_scroll.set)
    tv_tour.pack(side='left', fill='both', expand=True)
    tour_scroll.pack(side='right', fill='y')
    for tour in tours:
        try:
            capacity = int(tour.soCho)
        except Exception:
            capacity = tour.soCho if isinstance(tour.soCho, int) else 0
        booked = sum(d.soNguoi for d in bookings if d.maTour == tour.maTour and d.trangThai == 'da_thanh_toan')
        remaining = max(0, capacity - booked)
        tv_tour.insert('', tk.END, values=(
            tour.maTour, 
            tour.tenTour, 
            getattr(tour, 'ngayDi', '—'), 
            getattr(tour, 'ngayVe', '—'), 
            self.format_money(tour.gia),
            remaining,
            booked
        ))
    self.apply_zebra(tv_tour)

def show_kh_details(self, event=None):
    if not getattr(self, 'tv_kh', None):
        return
    sel = self.tv_kh.selection()
    if not sel:
        messagebox.showwarning('Chú ý', 'Chọn một khách hàng')
        return
    ma = self.tv_kh.item(sel[0], 'values')[0]
    kh = self.ql.TimKhacHang(ma)
    if not kh:
        messagebox.showerror('Lỗi', 'Không tìm thấy khách hàng')
        return
    orders = [d for d in self.ql.danhSachDatTour if d.maKH == kh.maKH]
    top, container = self.create_modal(f'Hồ sơ khách: {kh.tenKH}', size=(820, 540))
    ttk.Label(container, text='THẺ KHÁCH HÀNG', style='Title.TLabel').pack(anchor='w', pady=(0,12))
    
    tabs = ttk.Notebook(container)
    tabs.pack(fill='both', expand=True)
    
    info_tab = ttk.Frame(tabs, style='App.TFrame', padding=10)
    orders_tab = ttk.Frame(tabs, style='App.TFrame', padding=10)
    tabs.add(info_tab, text='Thông tin cá nhân')
    tabs.add(orders_tab, text='Đơn của khách hàng')
    
    info_card = ttk.Frame(info_tab, style='Card.TFrame', padding=12)
    info_card.pack(fill='both', expand=True)
    
    ttk.Label(info_card, text=f'Mã KH: {kh.maKH}', style='BodyBold.TLabel').pack(anchor='w', pady=4)
    ttk.Label(info_card, text=f'Tên KH: {kh.tenKH}', style='Body.TLabel').pack(anchor='w', pady=4)
    ttk.Label(info_card, text=f'Số điện thoại: {kh.soDT}', style='Body.TLabel').pack(anchor='w', pady=4)
    ttk.Label(info_card, text=f'Email: {kh.email}', style='Body.TLabel').pack(anchor='w', pady=4)
    ttk.Label(info_card, text=f'Ví / Số dư: {self.format_money(kh.soDu)}', style='BodyBold.TLabel').pack(anchor='w', pady=4)
    
    tv = ttk.Treeview(orders_tab, columns=('MaDat','MaTour','SoNguoi','TrangThai','Tong'), show='headings')
    for col, text, w in (('MaDat','Mã đặt',120),('MaTour','Mã tour',120),('SoNguoi','Số người',100),('TrangThai','Trạng thái',140),('Tong','Tổng tiền',140)):
        tv.heading(col, text=text)
        tv.column(col, width=w, anchor='center')
    scr = ttk.Scrollbar(orders_tab, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')
    for d in orders:
        tv.insert('', tk.END, values=(d.maDat, d.maTour, d.soNguoi, d.trangThai, self.format_money(d.tongTien)))
    self.apply_zebra(tv)
    
    btn_bar = ttk.Frame(container, padding=(0,12,0,0))
    btn_bar.pack(fill='x')
    ttk.Button(btn_bar, text='Đặt tour cho khách này', style='Accent.TButton', command=lambda: self.dat_tour_for_customer(kh.maKH)).pack(side='left', padx=4)
    ttk.Button(btn_bar, text='Hủy đơn của khách', style='Danger.TButton', command=lambda: self.huy_dat_for_customer(kh.maKH)).pack(side='left', padx=4)

def thong_ke(self):
    tong = sum(d.tongTien for d in self.ql.danhSachDatTour if d.trangThai == 'da_thanh_toan')
    counts = {}
    revenue_per_tour = {}
    for d in self.ql.danhSachDatTour:
        counts[d.maTour] = counts.get(d.maTour, 0) + 1
        if d.trangThai == 'da_thanh_toan':
            revenue_per_tour[d.maTour] = revenue_per_tour.get(d.maTour, 0) + d.tongTien
    popular = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    topcus = {}
    for d in self.ql.danhSachDatTour:
        if d.trangThai == 'da_thanh_toan':
            topcus[d.maKH] = topcus.get(d.maKH, 0) + d.tongTien
    loyal = sorted(topcus.items(), key=lambda x: x[1], reverse=True)
    
    top, container = self.create_modal('Báo cáo thống kê hệ thống')
    
    header = ttk.Frame(container, style='Card.TFrame', padding=16)
    header.pack(fill='x', pady=(0,16))
    ttk.Label(header, text='📊 BÁO CÁO THỐNG KÊ HỆ THỐNG', style='Title.TLabel').pack(anchor='w')
    
    revenue_card = ttk.Frame(header, style='Card.TFrame', relief='solid', borderwidth=2, padding=12)
    revenue_card.pack(fill='x', pady=(12,0))
    ttk.Label(revenue_card, text='💰 Tổng doanh thu', style='Body.TLabel').pack(anchor='w')
    ttk.Label(revenue_card, text=self.format_money(tong), font=('Segoe UI', 18, 'bold'), foreground='#1b6dc1').pack(anchor='w', pady=(4,0))
    
    summary = ttk.Frame(container, style='Card.TFrame', padding=8)
    summary.pack(fill='x', pady=(0,12))
    total_bookings = len(self.ql.danhSachDatTour)
    paid_bookings = sum(1 for d in self.ql.danhSachDatTour if d.trangThai == 'da_thanh_toan')
    ttk.Label(summary, text=f'📋 Tổng đơn: {total_bookings} | ✅ Đã thanh toán: {paid_bookings} | ⏳ Chưa thanh toán: {total_bookings - paid_bookings}', style='Body.TLabel').pack(anchor='w')
    
    tabs = ttk.Notebook(container)
    tabs.pack(fill='both', expand=True)
    
    tour_tab = ttk.Frame(tabs, style='App.TFrame', padding=12)
    customer_tab = ttk.Frame(tabs, style='App.TFrame', padding=12)
    tabs.add(tour_tab, text='🎯 Tour phổ biến')
    tabs.add(customer_tab, text='⭐ Khách hàng thân thiết')
    
    ttk.Label(tour_tab, text='Xếp hạng tour theo lượt đặt và doanh thu', style='Body.TLabel').pack(anchor='w', pady=(0,8))
    tv1 = ttk.Treeview(tour_tab, columns=('Rank','MaTour','SoDat','DoanhThu'), show='headings')
    for col, text, w in (
        ('Rank','#',50),
        ('MaTour','Mã tour',180),
        ('SoDat','Lượt đặt',120),
        ('DoanhThu','Doanh thu',180)):
        tv1.heading(col, text=text)
        tv1.column(col, width=w, anchor='center')
    scr1 = ttk.Scrollbar(tour_tab, orient='vertical', command=tv1.yview)
    tv1.configure(yscrollcommand=scr1.set)
    tv1.pack(side='left', fill='both', expand=True)
    scr1.pack(side='right', fill='y')
    for rank, (ma, c) in enumerate(popular, start=1):
        medal = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else f'{rank}'
        tv1.insert('', tk.END, values=(medal, ma, c, self.format_money(revenue_per_tour.get(ma,0))))
    self.apply_zebra(tv1)
    
    ttk.Label(customer_tab, text='Xếp hạng khách hàng theo tổng chi tiêu', style='Body.TLabel').pack(anchor='w', pady=(0,8))
    tv2 = ttk.Treeview(customer_tab, columns=('Rank','MaKH','Ten','TongChi'), show='headings')
    for col, text, w in (
        ('Rank','#',50),
        ('MaKH','Mã KH',140),
        ('Ten','Tên khách hàng',280),
        ('TongChi','Tổng chi tiêu',180)):
        tv2.heading(col, text=text)
        tv2.column(col, width=w, anchor='center' if col != 'Ten' else 'w')
    scr2 = ttk.Scrollbar(customer_tab, orient='vertical', command=tv2.yview)
    tv2.configure(yscrollcommand=scr2.set)
    tv2.pack(side='left', fill='both', expand=True)
    scr2.pack(side='right', fill='y')
    for rank, (ma, s) in enumerate(loyal, start=1):
        kh = self.ql.TimKhacHang(ma)
        name = kh.tenKH if kh else ma
        medal = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else f'{rank}'
        tv2.insert('', tk.END, values=(medal, ma, name, self.format_money(s)))
    self.apply_zebra(tv2)

def export_tour(self):
    sel = self.tv_tour.selection()
    if not sel:
        messagebox.showerror('Lỗi', 'Chưa chọn tour để export')
        return
    ma = self.tv_tour.item(sel[0], 'values')[0]
    t = self.ql.TimTour(ma)
    if not t:
        messagebox.showerror('Lỗi', 'Tour không tồn tại')
        return
    path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON files','*.json')], title='Lưu tour dưới dạng JSON')
    if not path:
        return
    obj = {
        'maTour': t.maTour,
        'tenTour': t.tenTour,
        'gia': t.gia,
        'soCho': t.soCho,
        'huongDanVien': t.huongDanVien,
        'ngayDi': getattr(t, 'ngayDi', None),
        'ngayVe': getattr(t, 'ngayVe', None),
        'lichTrinh': t.lichTrinh
    }
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        messagebox.showinfo('OK', f'Export thành công: {path}')
    except Exception as e:
        messagebox.showerror('Lỗi', f'Không thể lưu file: {e}')

def import_tour(self):
    path = filedialog.askopenfilename(filetypes=[('JSON files','*.json')], title='Chọn file tour JSON để import')
    if not path:
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        ma = data.get('maTour')
        ten = data.get('tenTour')
        gia = data.get('gia')
        soCho = data.get('soCho')
        lich = data.get('lichTrinh', [])
        hdv = data.get('huongDanVien')
        ngayDi = data.get('ngayDi')
        ngayVe = data.get('ngayVe')
        tour = Tour(ma, ten, gia, soCho, lich, hdv, ngayDi=ngayDi, ngayVe=ngayVe)
        if self.ql.ThemTour(tour):
            luu_tat_ca(self.ql)
            self.hien_thi_tour()
            messagebox.showinfo('OK', f'Import tour thành công: {ma}')
    except Exception as e:
        messagebox.showerror('Lỗi', f'Import thất bại: {e}')

GiaoDienCoSo.show_hdv_details = show_hdv_details
GiaoDienCoSo.show_kh_details = show_kh_details
GiaoDienCoSo.thong_ke = thong_ke
GiaoDienCoSo.export_tour = export_tour
GiaoDienCoSo.import_tour = import_tour
