import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import filedialog
import json
from datetime import datetime
from collections import defaultdict
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
    ttk.Label(summary_card, text=f'Tổng số tour phụ trách: {len(tours)}', style='BodyBold.TLabel').pack(side='left', padx=12)
    ttk.Label(summary_card, text=f'Tổng lượt khách: {sum(p["soNguoi"] for p in passengers)}', style='Body.TLabel').pack(side='left', padx=12)

    tour_frame = ttk.LabelFrame(tour_container, text='Danh sách tour được phân công', style='Card.TLabelframe', padding=12)
    tour_frame.pack(fill='both', expand=True)

    tv_tour = ttk.Treeview(tour_frame, columns=('Ma', 'Ten', 'NgayDi', 'NgayVe', 'Gia', 'ConCho', 'DaDat'), show='headings')
    headers = {
        'Ma': ('Mã Tour', 100, 'center'),
        'Ten': ('Tên Tour', 260, 'w'),
        'NgayDi': ('Khởi hành', 220, 'center'),
        'NgayVe': ('Kết thúc', 220, 'center'),
        'Gia': ('Giá', 110, 'center'),
        'ConCho': ('Còn chỗ', 80, 'center'),
        'DaDat': ('Đã đặt', 80, 'center')
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
        ngay_di_obj = self.ql.phan_tich_ngay(getattr(tour, 'ngayDi', None))
        ngay_ve_obj = self.ql.phan_tich_ngay(getattr(tour, 'ngayVe', None))
        ngay_di_hien_thi = self.ql.dien_giai_ngay(ngay_di_obj) if ngay_di_obj else '—'
        ngay_ve_hien_thi = self.ql.dien_giai_ngay(ngay_ve_obj) if ngay_ve_obj else '—'
        tv_tour.insert('', tk.END, values=(
            tour.maTour,
            tour.tenTour,
            ngay_di_hien_thi,
            ngay_ve_hien_thi,
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
    orders = list(getattr(self.ql, 'danhSachDatTour', []) or [])
    if not orders:
        messagebox.showinfo('Thông báo', 'Chưa có dữ liệu đặt tour để thống kê')
        return

    def parse_date(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        if text.lower() in ('now', 'today'):
            return datetime.today()
        for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
            try:
                return datetime.strptime(text[:10], fmt)
            except Exception:
                continue
        return None

    def safe_amount(v):
        try:
            return float(v)
        except Exception:
            return 0.0

    def safe_int(v):
        try:
            return int(v)
        except Exception:
            return 0

    paid = [o for o in orders if getattr(o, 'trangThai', '') == 'da_thanh_toan']
    pending = [o for o in orders if getattr(o, 'trangThai', '') == 'chua_thanh_toan']
    canceled = [o for o in orders if getattr(o, 'trangThai', '') == 'huy']
    total_bookings = len(orders)
    total_revenue = sum(safe_amount(getattr(o, 'tongTien', 0)) for o in paid)
    avg_ticket = total_revenue / len(paid) if paid else 0
    total_customers = len({o.maKH for o in orders})
    seats_paid = sum(safe_int(getattr(o, 'soNguoi', 0)) for o in paid)
    outstanding = sum(safe_amount(getattr(o, 'tongTien', 0)) for o in pending)
    cancelled_value = sum(safe_amount(getattr(o, 'tongTien', 0)) for o in canceled)

    status_counts = defaultdict(int)
    monthly_revenue = defaultdict(float)
    daily_revenue = defaultdict(float)
    tour_stats = {}
    customer_stats = {}
    latest_date = None
    today = datetime.today().date()

    for o in orders:
        status = getattr(o, 'trangThai', '') or 'khac'
        status_counts[status] += 1
        amount = safe_amount(getattr(o, 'tongTien', 0))
        seats = safe_int(getattr(o, 'soNguoi', 0))
        dt = parse_date(getattr(o, 'ngayDat', None))
        if dt:
            month_key = dt.strftime('%Y-%m')
            if status == 'da_thanh_toan':
                monthly_revenue[month_key] += amount
                daily_revenue[dt.date()] += amount
                latest_date = dt if not latest_date or dt > latest_date else latest_date
        stat = tour_stats.setdefault(o.maTour, {'bookings': 0, 'paid': 0, 'revenue': 0, 'seats': 0})
        stat['bookings'] += 1
        stat['seats'] += seats
        if status == 'da_thanh_toan':
            stat['paid'] += 1
            stat['revenue'] += amount
        cust = customer_stats.setdefault(o.maKH, {'orders': 0, 'paid_orders': 0, 'spend': 0})
        cust['orders'] += 1
        if status == 'da_thanh_toan':
            cust['paid_orders'] += 1
            cust['spend'] += amount

    months_sorted = sorted(monthly_revenue.keys(), key=lambda k: datetime.strptime(k, '%Y-%m'))
    if len(months_sorted) > 6:
        months_sorted = months_sorted[-6:]
    month_chart = [(datetime.strptime(m, '%Y-%m').strftime('%m/%Y'), monthly_revenue[m]) for m in months_sorted]
    top_tours = sorted(tour_stats.items(), key=lambda item: (-item[1]['revenue'], -item[1]['paid'], item[0]))[:5]
    top_customers = sorted(customer_stats.items(), key=lambda item: (-item[1]['spend'], item[0]))[:5]

    def format_rate(num, den):
        return (num / den * 100) if den else 0

    conversion_rate = format_rate(len(paid), total_bookings)
    cancel_rate = format_rate(len(canceled), total_bookings)
    last_30_revenue = sum(v for d, v in daily_revenue.items() if (today - d).days <= 30)
    previous_30_revenue = sum(v for d, v in daily_revenue.items() if 30 < (today - d).days <= 60)
    growth = 0
    if previous_30_revenue:
        growth = ((last_30_revenue - previous_30_revenue) / previous_30_revenue) * 100

    palette = {
        'primary': '#1b6dc1',
        'accent': '#1aa5a5',
        'danger': '#c44536',
        'muted': '#8a94a6',
        'surface': '#f8fafc'
    }

    top, container = self.create_modal('Báo cáo thống kê nâng cao', size=(1180, 780))

    header = ttk.Frame(container, style='Card.TFrame', padding=16)
    header.pack(fill='x', pady=(0, 16))
    ttk.Label(header, text='BÁO CÁO THỐNG KÊ HỆ THỐNG QUẢN LÝ DU LỊCH', style='Title.TLabel').pack(anchor='w')
    info_line = f"Dữ liệu cập nhật: {latest_date.strftime('%d/%m/%Y') if latest_date else 'Chưa xác định'}"
    ttk.Label(header, text=info_line, style='Body.TLabel', foreground=palette['muted']).pack(anchor='w')

    cards = ttk.Frame(container, style='App.TFrame')
    cards.pack(fill='x', pady=(0, 12))
    cards.columnconfigure((0, 1, 2, 3), weight=1)

    card_data = [
        ('Doanh thu đã thu', self.format_money(total_revenue), f"30 ngày gần nhất: {self.format_money(last_30_revenue)}"),
        ('Đơn đã thanh toán', f"{len(paid)} / {total_bookings}", f"Tỉ lệ chuyển đổi: {conversion_rate:.1f}%"),
        ('Số khách & chỗ', f"{total_customers} khách | {seats_paid} chỗ", f"Giá trị TB/đơn: {self.format_money(avg_ticket)}"),
        ('Đơn hủy / treo', f"{len(canceled)} hủy | {len(pending)} chờ", f"Giá trị treo: {self.format_money(outstanding)}")
    ]

    for idx, (title, value, sub) in enumerate(card_data):
        card = ttk.Frame(cards, style='Card.TFrame', padding=14)
        card.grid(row=0, column=idx, sticky='nsew', padx=6)
        ttk.Label(card, text=title, style='BodyBold.TLabel').pack(anchor='w')
        ttk.Label(card, text=value, font=('Segoe UI', 16, 'bold'), foreground=palette['primary']).pack(anchor='w', pady=(4, 2))
        ttk.Label(card, text=sub, style='Body.TLabel', foreground=palette['muted']).pack(anchor='w')

    charts = ttk.Frame(container, style='App.TFrame')
    charts.pack(fill='x', pady=(0, 12))

    left_chart = ttk.Frame(charts, style='Card.TFrame', padding=14)
    right_chart = ttk.Frame(charts, style='Card.TFrame', padding=14)
    left_chart.pack(side='left', fill='both', expand=True, padx=(0, 6))
    right_chart.pack(side='left', fill='both', expand=True, padx=(6, 0))

    ttk.Label(left_chart, text='Doanh thu theo tháng (6 kỳ gần nhất)', style='BodyBold.TLabel').pack(anchor='w')
    bar_canvas = tk.Canvas(left_chart, height=240, background=palette['surface'], highlightthickness=0)
    bar_canvas.pack(fill='x', pady=(8, 0))

    def render_bar_chart(event=None):
        bar_canvas.delete('all')
        if not month_chart:
            bar_canvas.create_text(10, 20, anchor='nw', text='Chưa có giao dịch đã thanh toán', font=('Segoe UI', 10), fill=palette['muted'])
            return
        width = bar_canvas.winfo_width() or 540
        height = bar_canvas.winfo_height() or 240
        padding_bottom = 40
        padding_top = 30
        padding_side = 24
        usable_width = width - padding_side * 2
        usable_height = height - padding_top - padding_bottom
        max_val = max(v for _, v in month_chart) or 1
        bar_w = usable_width / len(month_chart)
        for idx, (label, value) in enumerate(month_chart):
            x0 = padding_side + idx * bar_w + 6
            x1 = padding_side + (idx + 1) * bar_w - 6
            bar_h = usable_height * (value / max_val)
            y1 = height - padding_bottom
            y0 = y1 - bar_h
            bar_canvas.create_rectangle(x0, y0, x1, y1, fill=palette['primary'], width=0)
            bar_canvas.create_text((x0 + x1) / 2, y1 + 16, text=label, font=('Segoe UI', 9), fill=palette['muted'])
            if bar_h > 20:
                bar_canvas.create_text((x0 + x1) / 2, y0 - 10, text=self.format_money(value), font=('Segoe UI', 8), fill='#2d3748')
        bar_canvas.create_line(padding_side, y1, width - padding_side, y1, fill='#d3d9e3')

    bar_canvas.bind('<Configure>', render_bar_chart)
    render_bar_chart()

    ttk.Label(right_chart, text='Cơ cấu trạng thái đơn', style='BodyBold.TLabel').pack(anchor='w')
    donut = tk.Canvas(right_chart, height=240, background=palette['surface'], highlightthickness=0)
    donut.pack(fill='x', pady=(8, 0))

    status_mapping = [
        ('da_thanh_toan', 'Đã thanh toán', palette['primary']),
        ('chua_thanh_toan', 'Chờ thanh toán', palette['accent']),
        ('huy', 'Đã hủy', palette['danger'])
    ]

    def render_donut(event=None):
        donut.delete('all')
        data = [(label, status_counts.get(key, 0), color) for key, label, color in status_mapping]
        total = sum(v for _, v, _ in data)
        w = donut.winfo_width() or 360
        h = donut.winfo_height() or 240
        chart_size = min(w - 160, h - 40)
        cx = 80 + chart_size / 2
        cy = h / 2
        radius = chart_size / 2 - 10
        if total == 0:
            donut.create_text(cx, cy, text='Chưa có dữ liệu', font=('Segoe UI', 11), fill=palette['muted'])
            return
        start = 90
        for _, value, color in data:
            extent = (value / total) * 360 if total else 0
            donut.create_arc(cx - radius, cy - radius, cx + radius, cy + radius,
                             start=start, extent=-extent, fill=color, outline='')
            start -= extent
        inner_r = radius * 0.55
        donut.create_oval(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r, fill=palette['surface'], outline=palette['surface'])
        donut.create_text(cx, cy - 8, text=f"{total} đơn", font=('Segoe UI', 11, 'bold'), fill='#1f2937')
        donut.create_text(cx, cy + 12, text=f"Hủy: {cancel_rate:.1f}%", font=('Segoe UI', 9), fill=palette['muted'])
        legend_x = cx + radius + 30
        legend_y = cy - 40
        for label, value, color in data:
            donut.create_rectangle(legend_x, legend_y - 6, legend_x + 14, legend_y + 6, fill=color, outline=color)
            donut.create_text(legend_x + 22, legend_y, anchor='w', text=f"{label}: {value}", font=('Segoe UI', 9), fill='#111')
            legend_y += 28

    donut.bind('<Configure>', render_donut)
    render_donut()

    lower = ttk.Frame(container, style='App.TFrame')
    lower.pack(fill='both', expand=True)

    left_panel = ttk.Frame(lower, style='Card.TFrame', padding=14)
    right_panel = ttk.Frame(lower, style='Card.TFrame', padding=14)
    left_panel.pack(side='left', fill='both', expand=True, padx=(0, 6))
    right_panel.pack(side='left', fill='both', expand=True, padx=(6, 0))

    ttk.Label(left_panel, text='Top tour theo doanh thu', style='BodyBold.TLabel').pack(anchor='w')
    tour_canvas = tk.Canvas(left_panel, height=180, background=palette['surface'], highlightthickness=0)
    tour_canvas.pack(fill='x', pady=(8, 12))

    def render_top_tour_chart(event=None):
        tour_canvas.delete('all')
        if not top_tours:
            tour_canvas.create_text(10, 14, anchor='nw', text='Chưa có tour sinh doanh thu', font=('Segoe UI', 10), fill=palette['muted'])
            return
        width = tour_canvas.winfo_width() or 520
        height = tour_canvas.winfo_height() or 180
        max_val = max(stat['revenue'] for _, stat in top_tours) or 1
        bar_height = 26
        padding_left = 14
        padding_top = 10
        available_width = width - 220
        for idx, (ma, stat) in enumerate(top_tours):
            y0 = padding_top + idx * (bar_height + 8)
            y1 = y0 + bar_height
            if y1 > height:
                break
            bar_len = available_width * (stat['revenue'] / max_val)
            tour_canvas.create_rectangle(160, y0, 160 + bar_len, y1, fill=palette['primary'], outline='')
            tour_obj = self.ql.TimTour(ma) if hasattr(self.ql, 'TimTour') else None
            name = tour_obj.tenTour if tour_obj else ma
            if len(name) > 18:
                name = name[:16] + '..'
            tour_canvas.create_text(padding_left, y0 + bar_height / 2, anchor='w', text=name, font=('Segoe UI', 9, 'bold'), fill='#1f2933')
            tour_canvas.create_text(160 + bar_len + 8, y0 + bar_height / 2, anchor='w',
                                     text=self.format_money(stat['revenue']), font=('Segoe UI', 8), fill=palette['muted'])

    tour_canvas.bind('<Configure>', render_top_tour_chart)
    render_top_tour_chart()

    ttk.Label(left_panel, text='Bảng xếp hạng tour (doanh thu / lượt đặt / số chỗ)', style='Body.TLabel').pack(anchor='w')
    tv1 = ttk.Treeview(left_panel, columns=('Rank', 'MaTour', 'Ten', 'Dat', 'ThanhToan', 'DoanhThu', 'Cho'), show='headings')
    for col, text, w in (
        ('Rank', '#', 40),
        ('MaTour', 'Mã tour', 90),
        ('Ten', 'Tên tour', 180),
        ('Dat', 'Lượt đặt', 80),
        ('ThanhToan', 'Đã TT', 80),
        ('DoanhThu', 'Doanh thu', 120),
        ('Cho', 'Số chỗ', 80)):
        tv1.heading(col, text=text)
        tv1.column(col, width=w, anchor='center' if col != 'Ten' else 'w')
    scr1 = ttk.Scrollbar(left_panel, orient='vertical', command=tv1.yview)
    tv1.configure(yscrollcommand=scr1.set, height=6)
    tv1.pack(side='left', fill='both', expand=True, pady=(6, 0))
    scr1.pack(side='left', fill='y', padx=(2, 0))
    for rank, (ma, stat) in enumerate(top_tours, start=1):
        tour_obj = self.ql.TimTour(ma) if hasattr(self.ql, 'TimTour') else None
        name = tour_obj.tenTour if tour_obj else ma
        tv1.insert('', tk.END, values=(rank, ma, name, stat['bookings'], stat['paid'], self.format_money(stat['revenue']), stat['seats']))
    self.apply_zebra(tv1)

    ttk.Label(right_panel, text='Khách hàng chi tiêu cao', style='BodyBold.TLabel').pack(anchor='w')
    tv2 = ttk.Treeview(right_panel, columns=('Rank', 'MaKH', 'Ten', 'Don', 'DaTT', 'Chi'), show='headings')
    for col, text, w in (
        ('Rank', '#', 40),
        ('MaKH', 'Mã KH', 90),
        ('Ten', 'Tên khách', 170),
        ('Don', 'Tổng đơn', 90),
        ('DaTT', 'Đã TT', 90),
        ('Chi', 'Tổng chi', 120)):
        tv2.heading(col, text=text)
        tv2.column(col, width=w, anchor='center' if col not in ('Ten',) else 'w')
    scr2 = ttk.Scrollbar(right_panel, orient='vertical', command=tv2.yview)
    tv2.configure(yscrollcommand=scr2.set, height=8)
    tv2.pack(side='left', fill='both', expand=True, pady=(6, 0))
    scr2.pack(side='left', fill='y', padx=(2, 0))
    for rank, (ma, stat) in enumerate(top_customers, start=1):
        kh = self.ql.TimKhacHang(ma) if hasattr(self.ql, 'TimKhacHang') else None
        name = kh.tenKH if kh else ma
        tv2.insert('', tk.END, values=(rank, ma, name, stat['orders'], stat['paid_orders'], self.format_money(stat['spend'])))
    self.apply_zebra(tv2)

    insight = ttk.Frame(container, style='Card.TFrame', padding=12)
    insight.pack(fill='x', pady=(12, 0))
    ttk.Label(insight, text='Nhận định nhanh', style='BodyBold.TLabel').pack(anchor='w')
    best_tour_text = 'Chưa có tour thanh toán' if not top_tours else f"Tour nổi bật: {self.ql.TimTour(top_tours[0][0]).tenTour if hasattr(self.ql, 'TimTour') and self.ql.TimTour(top_tours[0][0]) else top_tours[0][0]} ({self.format_money(top_tours[0][1]['revenue'])})"
    best_cus_text = 'Chưa có khách thanh toán' if not top_customers else f"Khách chi tiêu cao nhất: {self.ql.TimKhacHang(top_customers[0][0]).tenKH if hasattr(self.ql, 'TimKhacHang') and self.ql.TimKhacHang(top_customers[0][0]) else top_customers[0][0]} ({self.format_money(top_customers[0][1]['spend'])})"
    growth_text = f"Tăng trưởng 30 ngày so với 30 ngày trước: {growth:+.1f}%" if previous_30_revenue else "Chưa đủ dữ liệu so sánh tăng trưởng"
    bullets = [
        best_tour_text,
        best_cus_text,
        f"Tỉ lệ hủy hiện tại: {cancel_rate:.1f}% (giá trị hủy: {self.format_money(cancelled_value)})",
        growth_text
    ]
    ttk.Label(insight, text='\n'.join(f"• {b}" for b in bullets), style='Body.TLabel').pack(anchor='w', pady=(6, 0))

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
