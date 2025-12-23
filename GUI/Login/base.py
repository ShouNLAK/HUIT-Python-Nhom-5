import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from QuanLy.quan_li_du_lich import QuanLiDuLich
from QuanLy.storage import luu_tat_ca
import urllib.parse
import urllib.request
import json
from datetime import datetime
import webbrowser
import os
import io
from tkinter import filedialog
import threading
import random
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


class ChuDeHienDai:
    def __init__(self, root):
        self.root = root
        self.nen = '#f5f6fa'
        self.be_mat = '#ffffff'
        self.chinh = '#1b6dc1'
        self.nguy_hiem = '#c44536'
        self.nhan_manh = '#1aa5a5'
        self.van_ban = '#1f2933'
        self.kieu = ttk.Style()
        try:
            self.kieu.theme_use('clam')
        except Exception:
            pass
        self.cau_hinh_co_ban()

    def cau_hinh_co_ban(self):
        self.root.configure(bg=self.nen)
        self.kieu.configure('App.TFrame', background=self.nen)
        self.kieu.configure('Card.TFrame', background=self.be_mat, relief='flat')
        self.kieu.configure('Header.TLabel', background=self.chinh, foreground='white', font=('Segoe UI', 14, 'bold'))
        self.kieu.configure('Title.TLabel', background=self.nen, foreground=self.van_ban, font=('Segoe UI', 12, 'bold'))
        self.kieu.configure('Body.TLabel', background=self.be_mat, foreground=self.van_ban, font=('Segoe UI', 10))
        self.kieu.configure('BodyBold.TLabel', background=self.be_mat, foreground=self.van_ban, font=('Segoe UI', 10, 'bold'))
        self.kieu.configure('Context.TFrame', background=self.be_mat)
        self.kieu.configure('App.TButton', font=('Segoe UI', 10), padding=6)
        self.kieu.map('App.TButton', background=[('!disabled', self.chinh), ('active', '#0f58a6')], foreground=[('!disabled', 'white')])
        self.kieu.configure('Accent.TButton', font=('Segoe UI', 10), padding=6)
        self.kieu.map('Accent.TButton', background=[('!disabled', self.nhan_manh), ('active', '#168b8b')], foreground=[('!disabled', 'white')])
        self.kieu.configure('Danger.TButton', font=('Segoe UI', 10), padding=6)
        self.kieu.map('Danger.TButton', background=[('!disabled', self.nguy_hiem), ('active', '#a13224')], foreground=[('!disabled', 'white')])
        self.kieu.configure('Toolbar.TButton', font=('Segoe UI', 10, 'bold'), padding=(14, 8))
        self.kieu.map('Toolbar.TButton', background=[('!disabled', '#1f6feb'), ('active', '#1553b2')], foreground=[('!disabled', 'white')])
        self.kieu.configure('Ghost.TButton', font=('Segoe UI', 10), padding=(10,6))
        self.kieu.map('Ghost.TButton', background=[('active', '#e6ecf5')], foreground=[('!disabled', self.van_ban)])
        self.kieu.configure('Mode.TButton', font=('Segoe UI', 10, 'bold'), padding=(10,6), background='#e9f0ff', foreground=self.van_ban)
        self.kieu.map('Mode.TButton', background=[('!disabled', '#e9f0ff'), ('active', '#d7e7ff')], foreground=[('!disabled', self.van_ban)])
        self.kieu.configure('ModeActive.TButton', font=('Segoe UI', 10, 'bold'), padding=(10,6), background=self.chinh, foreground='white')
        self.kieu.map('ModeActive.TButton', background=[('!disabled', self.chinh), ('active', '#1553b2')], foreground=[('!disabled', 'white')])
        self.kieu.configure('Form.TLabel', background=self.be_mat, foreground=self.van_ban, font=('Segoe UI', 10))
        self.kieu.configure('FormValue.TEntry', font=('Segoe UI', 10))
        self.kieu.configure('Card.TLabelframe', background=self.be_mat, foreground=self.van_ban, font=('Segoe UI', 11, 'bold'))
        self.kieu.configure('Card.TLabelframe.Label', background=self.be_mat, foreground=self.van_ban)
        self.ap_dung_treeview()

    def ap_dung_treeview(self):
        self.kieu.configure('Treeview', font=('Segoe UI', 10), rowheight=26, background='#fdfdfd', fieldbackground='#fdfdfd', bordercolor='#dfe3e8')
        self.kieu.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background=self.chinh, foreground='white')
        self.kieu.map('Treeview', background=[('selected', self.nhan_manh)], foreground=[('selected', 'white')])

    def trung_tam(self, win, width, height):
        try:
            win.update_idletasks()
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = int((sw - width) / 2)
            y = int((sh - height) / 3)
            win.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass

    def khung_the(self, parent, padding=16):
        frm = ttk.Frame(parent, style='Card.TFrame', padding=padding)
        frm.pack_propagate(False)
        return frm


class GoiY:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwin = None
        widget.bind('<Enter>', self.show)
        widget.bind('<Leave>', self.hide)

    def show(self, event=None):
        if self.tipwin:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tipwin = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(tw, text=self.text, bg='#ffffe0', relief='solid', borderwidth=1)
        lbl.pack()

    def hide(self, event=None):
        if self.tipwin:
            try:
                self.tipwin.destroy()
            except Exception:
                pass
            self.tipwin = None

class GiaoDienCoSo:
    def __init__(self, root, ql: QuanLiDuLich):
        self.root = root
        self.ql = ql
        self.root.title('Quản lý tour du lịch')
        self.theme = ChuDeHienDai(self.root)
        self.font_title = ('Segoe UI', 12, 'bold')
        self.font_body = ('Segoe UI', 10)
        self.font_small = ('Segoe UI', 9)
        self.modal_geometry = (580, 420)
        self.search_var = tk.StringVar()
        self.frame = None
        self.build_dang_nhap()

    def build_dang_nhap(self):
        if self.frame:
            self.frame.destroy()
        self.frame = tk.Frame(self.root, bg=self.theme.nen)
        self.frame.pack(fill='both', expand=True)
        self.theme.trung_tam(self.root, 460, 260)
        card = self.theme.khung_the(self.frame, padding=24)
        card.place(relx=0.5, rely=0.5, anchor='c', width=380, height=200)
        title = ttk.Label(card, text='Đăng nhập hệ thống', style='Title.TLabel')
        title.pack(anchor='center', pady=(0,12))
        form = ttk.Frame(card, padding=4)
        form.pack(fill='both', expand=True)
        ttk.Label(form, text='Tên đăng nhập', style='Form.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(form, text='Mật khẩu', style='Form.TLabel').grid(row=1, column=0, sticky='w', pady=(8,0))
        self.e_ten_dang_nhap = ttk.Entry(form, font=self.font_body)
        self.e_mat_khau = ttk.Entry(form, font=self.font_body, show='*')
        self.e_ten_dang_nhap.grid(row=0, column=1, padx=8, sticky='ew')
        self.e_mat_khau.grid(row=1, column=1, padx=8, sticky='ew', pady=(8,0))
        form.columnconfigure(1, weight=1)
        buttons = ttk.Frame(card)
        buttons.pack(fill='x', pady=(12,0))
        ttk.Button(buttons, text='Đăng nhập', style='App.TButton', command=self.dang_nhap).pack(side='left')
        ttk.Button(buttons, text='Đăng ký guest', style='Accent.TButton', command=self.dang_ky_guest).pack(side='left', padx=8)
        ttk.Button(buttons, text='Thoát', style='Danger.TButton', command=self.root.quit).pack(side='right')

    def create_modal(self, title, size=None, maximize=True):
        top = tk.Toplevel(self.root)
        top.title(title)
        top.configure(bg=self.theme.nen)
        top.transient(self.root)
        top.grab_set()
        width, height = size if size else self.modal_geometry
        if maximize:
            try:
                sw = self.root.winfo_screenwidth()
                sh = self.root.winfo_screenheight()
                top.geometry(f"{sw}x{sh}+0+0")
                try:
                    top.state('zoomed')
                except Exception:
                    pass
            except Exception:
                self.theme.trung_tam(top, width, height)
        else:
            self.theme.trung_tam(top, width, height)
        container = ttk.Frame(top, style='App.TFrame', padding=20)
        container.pack(fill='both', expand=True)
        return top, container

    def build_form_fields(self, parent, fields):
        entries = {}
        for idx, field in enumerate(fields):
            ttk.Label(parent, text=field['label'], style='Form.TLabel').grid(row=idx, column=0, sticky='w', pady=4)
            widget_type = field.get('widget', 'entry')
            if widget_type == 'combo':
                widget = ttk.Combobox(parent, values=field.get('values', []), state='readonly', font=self.font_body)
                if field.get('default'):
                    widget.set(field['default'])
            elif widget_type == 'text':
                widget = tk.Text(parent, height=field.get('height', 4), font=self.font_body, wrap='word')
            else:
                widget = ttk.Entry(parent, font=self.font_body, show=field.get('show'))
                if field.get('default'):
                    widget.insert(0, field['default'])
            widget.grid(row=idx, column=1, sticky='ew', padx=(12,0), pady=4)
            entries[field['name']] = widget
        parent.columnconfigure(1, weight=1)
        return entries

    def modal_buttons(self, parent, actions):
        wrap = ttk.Frame(parent)
        wrap.pack(fill='x', pady=(12,0))
        for action in actions:
            ttk.Button(wrap, text=action['text'], style=action.get('style', 'App.TButton'), command=action['command']).pack(side='left', padx=4)

    def clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def apply_zebra(self, tree):
        try:
            tree.tag_configure('odd', background='#ffffff')
            tree.tag_configure('even', background='#f4f6fb')
            for idx, iid in enumerate(tree.get_children()):
                tag = 'even' if idx % 2 == 0 else 'odd'
                tree.item(iid, tags=(tag,))
        except Exception:
            pass

    def format_money(self, value):
        try:
            return f"{int(float(value)):,} VND"
        except Exception:
            return str(value)

    def format_weather_text(self, weather):
        if not weather:
            return '—'
        if isinstance(weather, dict):
            if 'min' in weather and 'max' in weather:
                return f"{weather.get('min')}°C - {weather.get('max')}°C"
            if 'current' in weather:
                return f"{weather.get('current')}°C"
        return '—'

    def get_selected_tour(self):
        sel = self.tv_tour.selection()
        if not sel:
            return None
        values = self.tv_tour.item(sel[0], 'values')
        return self.ql.tim_tour(values[0])

    def _start_loading(self, container):
        try:
            if getattr(container, '_loading_label', None):
                return
            lbl = tk.Label(container, text='Đang tải...', fg='#666')
            lbl.pack(anchor='center', pady=6)
            container._loading_label = lbl
        except Exception:
            pass

    def _stop_loading(self, container):
        try:
            lbl = getattr(container, '_loading_label', None)
            if lbl:
                lbl.destroy()
                container._loading_label = None
        except Exception:
            pass

    def render_place_preview(self, container, place_name, info):
        if container is None:
            return
        try:
            if not container.winfo_exists():
                return
        except Exception:
            return
        try:
            for w in container.winfo_children():
                w.destroy()
        except Exception:
            return
        title = place_name or 'Địa điểm'
        if not info or (isinstance(info, dict) and info.get('error')):
            ttk.Label(container, text=f'Không tải được dữ liệu cho {title}', style='Body.TLabel').pack(anchor='w')
            return
        map_bytes = info.get('map_image_bytes')
        map_url = info.get('map_url')
        photo_bytes = info.get('photo_bytes')
        photo_url = info.get('photo_url')
        display = info.get('display_name') or title
        short = info.get('short_name') or title
        lat = info.get('lat')
        lon = info.get('lon')
        wrapper = ttk.Frame(container, style='Context.TFrame')
        wrapper.pack(fill='both', expand=True)
        media_holder = ttk.Frame(wrapper, style='Context.TFrame')
        media_holder.pack(fill='x')
        previews = []

        def render_image(bytes_data, caption):
            if not (bytes_data and PIL_AVAILABLE):
                return False
            try:
                img = Image.open(io.BytesIO(bytes_data))
                img.thumbnail((320, 220))
                photo = ImageTk.PhotoImage(img)
                block = ttk.Frame(media_holder, style='Context.TFrame')
                block.pack(side='left', padx=(0,12), pady=(0,8))
                ttk.Label(block, text=caption, style='BodyBold.TLabel').pack(anchor='w')
                lbl = ttk.Label(block, image=photo)
                lbl.image = photo
                lbl.pack(anchor='w', pady=(4,0))
                previews.append(photo)
                return True
            except Exception:
                return False

        map_rendered = render_image(map_bytes, 'Ảnh vệ tinh Bing')
        if not map_rendered and map_url:
            link = ttk.Label(media_holder, text='Mở ảnh vệ tinh trên Bing Maps', foreground=self.theme.primary, cursor='hand2')
            link.pack(side='left', pady=(0,8))
            link.bind('<Button-1>', lambda e, u=map_url: webbrowser.open(u))

        photo_rendered = render_image(photo_bytes, 'Ảnh địa điểm')
        if not photo_rendered and photo_url:
            link = ttk.Label(media_holder, text='Mở ảnh địa điểm', foreground=self.theme.primary, cursor='hand2')
            link.pack(side='left', pady=(0,8))
            link.bind('<Button-1>', lambda e, u=photo_url: webbrowser.open(u))

        container._preview_images = previews
        info_block = ttk.Frame(wrapper, style='Context.TFrame')
        info_block.pack(fill='both', expand=True)
        ttk.Label(info_block, text=short, style='BodyBold.TLabel').pack(anchor='w')
        ttk.Label(info_block, text=f'Địa chỉ: {display}', style='Body.TLabel').pack(anchor='w', pady=(4,0))
        if lat and lon:
            ttk.Label(info_block, text=f'Tọa độ: {lat}, {lon}', style='Body.TLabel').pack(anchor='w', pady=(4,0))
            osm_link = ttk.Label(info_block, text='Mở trên OpenStreetMap', foreground=self.theme.chinh, cursor='hand2', style='Body.TLabel')
            osm_link.pack(anchor='w', pady=(2,0))
            osm_link.bind('<Button-1>', lambda e, lat=lat, lon=lon: webbrowser.open(f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=12/{lat}/{lon}"))
            if map_url:
                bing_link = ttk.Label(info_block, text='Mở trên Bing Maps (vệ tinh)', foreground=self.theme.chinh, cursor='hand2', style='Body.TLabel')
                bing_link.pack(anchor='w', pady=(2,0))
                bing_link.bind('<Button-1>', lambda e, u=map_url: webbrowser.open(u))
        weather = info.get('weather')
        ttk.Label(info_block, text=f'Nhiệt độ: {self.format_weather_text(weather)}', style='Body.TLabel').pack(anchor='w', pady=(6,0))

    def dang_nhap(self):
        u = self.e_ten_dang_nhap.get()
        p = self.e_mat_khau.get()
        if self.ql.dang_nhap(u, p):
            name = self.ql.lay_ten_hien_thi(self.ql.nguoi_dung_hien_tai)
            role = self.ql.nguoi_dung_hien_tai.vai_tro.upper()
            messagebox.showinfo('Thông báo', f'Đăng nhập thành công: {name} ({role})')
            self.build_giao_dien_chinh()
        else:
            messagebox.showerror('Lỗi', 'Sai tài khoản hoặc mật khẩu')

    def build_giao_dien_chinh(self):
        if self.frame:
            self.frame.destroy()
        if self.ql.nguoi_dung_hien_tai and self.ql.nguoi_dung_hien_tai.vai_tro == 'root':
            self.build_root_console()
            return
        self.frame = ttk.Frame(self.root, style='App.TFrame')
        self.frame.pack(fill='both', expand=True)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        width = int(sw * 0.9)
        height = int(sh * 0.85)
        self.root.minsize(1200, 800)
        self.theme.trung_tam(self.root, width, height)
        self.root.bind('<Configure>', self.on_resize)
        header = ttk.Frame(self.frame, padding=(24,18))
        header.pack(fill='x')
        ttk.Label(header, text='Quản lý Tour du lịch', style='Title.TLabel').pack(side='left')
        summary_bar = ttk.Frame(self.frame, padding=(24,0))
        summary_bar.pack(fill='x')
        role_text = self.ql.nguoi_dung_hien_tai.vai_tro.upper() if self.ql.nguoi_dung_hien_tai else ''
        display_name = self.ql.lay_ten_hien_thi(self.ql.nguoi_dung_hien_tai) if self.ql.nguoi_dung_hien_tai else ''
        user_label = ttk.Label(summary_bar, text=f"Tài khoản: {display_name} ({role_text})", style='Body.TLabel')
        user_label.pack(side='left')
        ttk.Button(summary_bar, text='Đăng xuất', style='Danger.TButton', command=self.dang_xuat).pack(side='right')
        def _run_async(func, callback=None, *a, **kw):
            def worker():
                try:
                    res = func(*a, **kw)
                except Exception as e:
                    res = e
                if callback:
                    try:
                        self.root.after(1, lambda: callback(res))
                    except Exception:
                        pass
            threading.Thread(target=worker, daemon=True).start()
        self._run_async = _run_async
        self._place_preview_cache = {}
        role = self.ql.nguoi_dung_hien_tai.vai_tro if self.ql.nguoi_dung_hien_tai else ''
        active = getattr(self, 'active_section', 'Tour') if role == 'admin' else None
        paned = ttk.Panedwindow(self.frame, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=24, pady=18)
        left_panel = ttk.Frame(paned, style='Card.TFrame', padding=16)
        right_panel = ttk.Frame(paned, style='Card.TFrame', padding=16)
        if role == 'admin':
            paned.add(left_panel, weight=1)
        else:
            paned.add(left_panel, weight=3)
            paned.add(right_panel, weight=2)
        left_head = ttk.Frame(left_panel)
        left_head.pack(fill='x', pady=(0,12))
        active = getattr(self, 'active_section', 'Tour') if role == 'admin' else 'Tour'
        title_text = {
            'Tour': 'Danh sách tour',
            'Khách hàng': 'Danh sách khách hàng',
            'Hướng dẫn viên': 'Danh sách hướng dẫn viên',
            'Hệ thống': 'Quản lý hệ thống'
        }.get(active, 'Danh sách tour')
        ttk.Label(left_head, text=title_text, style='Title.TLabel').pack(side='left')
        tour_frame = ttk.Frame(left_panel)
        tour_frame.pack(fill='both', expand=True)
        self.tv_tour = ttk.Treeview(tour_frame, columns=('ma_tour','ten_tour','gia','so_cho','trang_thai','hdv'), show='headings')
        for col, text, w in (
            ('ma_tour','Mã Tour',90),
            ('ten_tour','Tên Tour',200),
            ('gia','Giá',120),
            ('so_cho','Số chỗ còn',110),
            ('trang_thai','Trạng thái',130),
            ('hdv','HDV',90)):
            self.tv_tour.heading(col, text=text)
            self.tv_tour.column(col, width=w, anchor='center' if col not in ('ten_tour','trang_thai') else 'w')
        tour_scroll = ttk.Scrollbar(tour_frame, orient='vertical', command=self.tv_tour.yview)
        self.tv_tour.configure(yscrollcommand=tour_scroll.set)
        self.tv_tour.pack(side='left', fill='both', expand=True)
        self.tour_scroll = tour_scroll
        self.tv_tour.bind('<<TreeviewSelect>>', self.on_tour_select)
        context_text = {
            'Tour': 'Chọn tour để xem thông tin',
            'Khách hàng': 'Chọn khách hàng để xem chi tiết',
            'Hướng dẫn viên': 'Chọn hướng dẫn viên để xem chi tiết',
            'Hệ thống': 'Quản lý đặt tour và thống kê'
        }.get(active, 'Chọn tour để xem thông tin')
        self.tour_context = ttk.Label(left_panel, text=context_text, style='Body.TLabel')
        self.tour_context.pack(fill='x', pady=(12,0))
        self.right_panel = right_panel
        role = self.ql.nguoi_dung_hien_tai.vai_tro if self.ql.nguoi_dung_hien_tai else ''
        self.tv_hdv = None
        self.tv_kh = None
        self.tv_dat = None
        self.stats_tv_tour = None
        self.stats_tv_customer = None
        if role == 'admin':
            self.kh_search_var = tk.StringVar()
            self.hdv_search_var = tk.StringVar()
            active = getattr(self, 'active_section', 'Tour')
            if active == 'Tour':
                self.tv_kh = None
                self.tv_hdv = None
                self.tv_dat = None
                try:
                    if getattr(self, 'tv_tour', None):
                        self.tv_tour.pack(side='left', fill='both', expand=True)
                        self.tour_scroll.pack(side='right', fill='y')
                except Exception:
                    pass
            else:
                try:
                    if getattr(self, 'tv_tour', None):
                        self.tv_tour.pack_forget()
                except Exception:
                    pass
                if active == 'Khách hàng':
                    kh_tools = ttk.Frame(tour_frame, padding=(0,0,0,8))
                    kh_tools.pack(fill='x')
                    ttk.Entry(kh_tools, textvariable=self.kh_search_var, font=self.font_body).pack(side='left', fill='x', expand=True, padx=(0,8))
                    ttk.Button(kh_tools, text='Tìm', style='Accent.TButton', command=self.search_khach).pack(side='left')
                    ttk.Button(kh_tools, text='Hiển thị tất cả', style='Ghost.TButton', command=self.hien_thi_khach).pack(side='left', padx=(6,0))
                    kh_body = ttk.Frame(tour_frame)
                    kh_body.pack(fill='both', expand=True)
                    self.tv_kh = ttk.Treeview(kh_body, columns=('ma_khach_hang','ten','so_dien_thoai'), show='headings')
                    for col, text, width in (('ma_khach_hang','Mã KH',110),('ten','Tên',200),('so_dien_thoai','SĐT',130)):
                        self.tv_kh.heading(col, text=text)
                        self.tv_kh.column(col, width=width, anchor='center' if col != 'ten' else 'w')
                    kh_scroll = ttk.Scrollbar(kh_body, orient='vertical', command=self.tv_kh.yview)
                    self.tv_kh.configure(yscrollcommand=kh_scroll.set)
                    self.tv_kh.pack(side='left', fill='both', expand=True)
                    kh_scroll.pack(side='right', fill='y')
                elif active == 'Hướng dẫn viên':
                    hdv_tools = ttk.Frame(tour_frame, padding=(0,0,0,8))
                    hdv_tools.pack(fill='x')
                    ttk.Entry(hdv_tools, textvariable=self.hdv_search_var, font=self.font_body).pack(side='left', fill='x', expand=True, padx=(0,8))
                    ttk.Button(hdv_tools, text='Tìm', style='Accent.TButton', command=self.search_hdv).pack(side='left')
                    ttk.Button(hdv_tools, text='Hiển thị tất cả', style='Ghost.TButton', command=self.hien_thi_hdv).pack(side='left', padx=(6,0))
                    hdv_body = ttk.Frame(tour_frame)
                    hdv_body.pack(fill='both', expand=True)
                    self.tv_hdv = ttk.Treeview(hdv_body, columns=('ma_hdv','ten_hdv','sdt','kinh_nghiem'), show='headings')
                    for col, text, width in (('ma_hdv','Mã HDV',110),('ten_hdv','Tên',200),('sdt','SĐT',140),('kinh_nghiem','Kinh nghiệm',120)):
                        self.tv_hdv.heading(col, text=text)
                        self.tv_hdv.column(col, width=width, anchor='center' if col != 'ten_hdv' else 'w')
                    hdv_scroll = ttk.Scrollbar(hdv_body, orient='vertical', command=self.tv_hdv.yview)
                    self.tv_hdv.configure(yscrollcommand=hdv_scroll.set)
                    self.tv_hdv.pack(side='left', fill='both', expand=True)
                    hdv_scroll.pack(side='right', fill='y')
                else:
                    dat_tools = ttk.Frame(tour_frame, padding=(0,0,0,8))
                    dat_tools.pack(fill='x')
                    dat_body = ttk.Frame(tour_frame)
                    dat_body.pack(fill='both', expand=True)
                    self.tv_dat = ttk.Treeview(dat_body, columns=('ma_dat','ma_tour','ma_khach_hang','so_nguoi','trang_thai','tong'), show='headings')
                    for col, text, width in (('ma_dat','Mã Đặt',110),('ma_tour','Mã Tour',110),('ma_khach_hang','Mã KH',110),('so_nguoi','Số người',90),('trang_thai','Trạng thái',120),('tong','Tổng tiền',140)):
                        self.tv_dat.heading(col, text=text)
                        self.tv_dat.column(col, width=width, anchor='center')
                    dat_scroll = ttk.Scrollbar(dat_body, orient='vertical', command=self.tv_dat.yview)
                    self.tv_dat.configure(yscrollcommand=dat_scroll.set)
                    self.tv_dat.pack(side='left', fill='both', expand=True)
                    dat_scroll.pack(side='right', fill='y')
        else:
            self.context_hdr = ttk.Frame(right_panel)
            self.context_hdr.pack(fill='x', pady=(0,12))
            self.context_body = ttk.Frame(right_panel)
            self.context_body.pack(fill='both', expand=True)
            if role == 'user':
                self.greet_label = ttk.Label(self.context_hdr, text='', style='Title.TLabel')
                self.greet_label.pack(anchor='w')
                self.balance_label = ttk.Label(self.context_hdr, text='', style='Body.TLabel')
                self.balance_label.pack(anchor='w', pady=(4,0))
                ttk.Button(self.context_hdr, text='Thanh toán & đặt tour', style='Accent.TButton', command=self.book_selected_tour_for_user).pack(anchor='e', pady=(6,0))
            else:
                self.hdv_title = ttk.Label(self.context_hdr, text='Chọn tour để xem hành trình và khách', style='Body.TLabel')
                self.hdv_title.pack(anchor='w')
        toolbar = ttk.Frame(self.frame, padding=(24,0,24,16))
        toolbar.pack(fill='x', side='bottom')
        def build_toolbar_section(parent, title, buttons):
            card = ttk.Frame(parent, style='Card.TFrame', padding=10)
            card.pack(side='left', fill='x', expand=True, padx=6)
            ttk.Label(card, text=title, style='BodyBold.TLabel').pack(anchor='w')
            row = ttk.Frame(card)
            row.pack(fill='x', pady=(8,0))
            for text, cmd, style_name in buttons:
                ttk.Button(row, text=text, style=style_name, command=cmd).pack(side='left', padx=4)
            return card
        if role == 'admin':
            mode_bar = ttk.Frame(toolbar, style='App.TFrame')
            mode_bar.pack(fill='x', pady=(0,6))
            modes = [
                ('Tour', 'Tour'),
                ('Khách hàng', 'Khách hàng'),
                ('Hướng dẫn viên', 'Hướng dẫn viên'),
                ('Hệ thống', 'Hệ thống')
            ]
            if not hasattr(self, 'active_section'):
                self.active_section = 'Tour'
            self.mode_buttons = {}
            for key, label in modes:
                style_name = 'ModeActive.TButton' if getattr(self, 'active_section', 'Tour') == key else 'Mode.TButton'
                btn = ttk.Button(mode_bar, text=label, style=style_name, command=lambda k=key: (setattr(self, 'active_section', k), self.build_giao_dien_chinh()))
                btn.pack(side='left', padx=6)
                self.mode_buttons[key] = btn

            wrap = ttk.Frame(toolbar, style='App.TFrame')
            wrap.pack(fill='x')
            if getattr(self, 'active_section', 'Tour') == 'Tour':
                build_toolbar_section(wrap, 'Tour', [
                    ('Thêm', self.them_tour, 'Toolbar.TButton'),
                    ('Sửa', self.sua_tour, 'App.TButton'),
                    ('Xóa', self.xoa_tour, 'Danger.TButton'),
                    ('Tìm', lambda: self.prompt_search('Tour'), 'Ghost.TButton')
                ])
            elif getattr(self, 'active_section', '') == 'Khách hàng':
                build_toolbar_section(wrap, 'Khách hàng', [
                    ('Thêm', self.them_khach, 'Toolbar.TButton'),
                    ('Sửa', self.sua_khach, 'App.TButton'),
                    ('Xóa', self.xoa_khach, 'Danger.TButton'),
                    ('Tìm', lambda: self.prompt_search('Khách hàng'), 'Ghost.TButton')
                ])
            elif getattr(self, 'active_section', '') == 'Hướng dẫn viên':
                build_toolbar_section(wrap, 'Hướng dẫn viên', [
                    ('Thêm', self.them_hdv, 'Toolbar.TButton'),
                    ('Sửa', self.sua_hdv, 'App.TButton'),
                    ('Xóa', self.xoa_hdv, 'Danger.TButton'),
                    ('Tìm', lambda: self.prompt_search('Hướng dẫn viên'), 'Ghost.TButton')
                ])
            else:
                build_toolbar_section(wrap, 'Hệ thống', [
                    ('Đặt tour', self.dat_tour, 'Accent.TButton'),
                    ('Hủy đặt', self.huy_dat, 'App.TButton'),
                    ('Thống kê', self.thong_ke, 'Accent.TButton'),
                    ('Làm mới', self.refresh_lists, 'App.TButton'),
                ])
        elif role == 'hdv':
            ttk.Button(toolbar, text='Làm mới', style='App.TButton', command=self.refresh_lists).pack(side='right', padx=(0,8))
            ttk.Button(toolbar, text='Đăng xuất', style='Danger.TButton', command=self.dang_xuat).pack(side='right')
            self.hien_thi_tour_hdv()
        else:
            wrap = ttk.Frame(toolbar, style='App.TFrame')
            wrap.pack(fill='x')
            build_toolbar_section(wrap, 'Ví & thanh toán', [
                ('Hiện QR nạp tiền', self.nap_tien, 'Accent.TButton'),
                ('Thanh toán & đặt tour', self.book_selected_tour_for_user, 'Toolbar.TButton'),
                ('Đơn của tôi', self.xem_don_user, 'App.TButton'),
                ('Đăng xuất', self.dang_xuat, 'Danger.TButton')
            ])
            self.hien_thi_tour()
            self.hien_thi_khach_user()
        if role == 'admin':
            self.hien_thi_tour()
            self.hien_thi_khach()
            self.hien_thi_hdv()
            self.hien_thi_dat_admin()
        if role == 'user':
            try:
                self.start_balance_updater()
            except Exception:
                pass
        if role in ('admin', 'user', 'hdv'):
            self.tv_tour.bind('<Double-Button-1>', self.show_tour_details)
        if getattr(self, 'tv_kh', None):
            self.tv_kh.bind('<Double-Button-1>', self.hien_thi_chi_tiet_kh)
        if getattr(self, 'tv_hdv', None):
            self.tv_hdv.bind('<Double-Button-1>', self.hien_thi_chi_tiet_hdv)

    def build_root_console(self):
        self.frame = ttk.Frame(self.root, style='App.TFrame')
        self.frame.pack(fill='both', expand=True)
        try:
            self.root.state('zoomed')
        except Exception:
            pass
        header = ttk.Frame(self.frame, padding=(24,18))
        header.pack(fill='x')
        ttk.Label(header, text='Điều hành tài khoản Admin', style='Title.TLabel').pack(side='left')
        ttk.Button(header, text='Đăng xuất', style='Danger.TButton', command=self.dang_xuat).pack(side='right')
        ttk.Button(header, text='Kiểm tra Data', style='App.TButton', command=self.show_data_status).pack(side='right', padx=(0,8))
        ttk.Label(self.frame, text='Tài khoản root chỉ được thao tác với Admin', style='Body.TLabel').pack(anchor='w', padx=24, pady=(0,12))
        controls = ttk.Frame(self.frame, padding=(24,0,24,12))
        controls.pack(fill='x')
        self.root_search_var = tk.StringVar()
        ttk.Entry(controls, textvariable=self.root_search_var, font=self.font_body, width=32).pack(side='left')
        ttk.Button(controls, text='Tìm', style='Accent.TButton', command=self.root_refresh_admins).pack(side='left', padx=6)
        ttk.Button(controls, text='Làm mới', style='App.TButton', command=self.root_clear_search).pack(side='left')
        table_wrap = ttk.Frame(self.frame, padding=(24,0,24,12))
        table_wrap.pack(fill='both', expand=True)
        self.root_admin_tree = ttk.Treeview(table_wrap, columns=('ten_dang_nhap','ho_ten_hien_thi'), show='headings')
        self.root_admin_tree.heading('ten_dang_nhap', text='Tên đăng nhập')
        self.root_admin_tree.heading('ho_ten_hien_thi', text='Họ tên hiển thị')
        self.root_admin_tree.column('ten_dang_nhap', width=220, anchor='center')
        self.root_admin_tree.column('ho_ten_hien_thi', width=320, anchor='w')
        scroll = ttk.Scrollbar(table_wrap, orient='vertical', command=self.root_admin_tree.yview)
        self.root_admin_tree.configure(yscrollcommand=scroll.set)
        self.root_admin_tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        action = ttk.Frame(self.frame, padding=(24,0,24,18))
        action.pack(fill='x')
        ttk.Button(action, text='Tạo admin', style='Toolbar.TButton', command=lambda: self.root_open_admin_form('create')).pack(side='left', padx=4)
        ttk.Button(action, text='Sửa admin', style='App.TButton', command=lambda: self.root_open_admin_form('edit')).pack(side='left', padx=4)
        ttk.Button(action, text='Xóa admin', style='Danger.TButton', command=self.root_delete_admin).pack(side='left', padx=4)
        ttk.Button(action, text='Reset mật khẩu về 123', style='Accent.TButton', command=self.root_reset_admin_password).pack(side='left', padx=4)
        self.root_refresh_admins()

    def show_data_status(self):
        top, container = self.create_modal('Trạng thái Data', size=(640, 520), maximize=False)
        tree = ttk.Treeview(container, columns=('status',), show='tree')
        tree.pack(fill='both', expand=True)
        prog = tree.insert('', 'end', text='Chương trình đang chạy')
        tree.insert(prog, 'end', text='ID tiến trình: %s' % (os.getpid(),))
        data_root = tree.insert('', 'end', text='Dữ liệu')
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Data'))
        try:
            files = sorted(os.listdir(base)) if os.path.isdir(base) else []
        except Exception:
            files = []
        if not files:
            tree.insert(data_root, 'end', text='(không tìm thấy thư mục Data)')
        else:
            for f in files:
                p = os.path.join(base, f)
                status = 'Tốt' if os.path.isfile(p) else 'Không hợp lệ'
                tree.insert(data_root, 'end', text=f + ' — ' + status)
        self.apply_zebra(tree)

    def start_balance_updater(self, interval=2000):
        try:
            self.stop_balance_updater()
        except Exception:
            pass
        def _tick():
            try:
                if not self.ql.nguoi_dung_hien_tai or self.ql.nguoi_dung_hien_tai.vai_tro != 'user':
                    return
                kh = self.ql.tim_khach_hang(self.ql.nguoi_dung_hien_tai.ma_khach_hang)
                bal = kh.so_du if kh else 0
                if hasattr(self, 'balance_label'):
                    self.balance_label.config(text=f"Số dư: {self.format_money(bal)}")
            except Exception:
                pass
            try:
                self._balance_job = self.root.after(interval, _tick)
            except Exception:
                pass
        _tick()

    def stop_balance_updater(self):
        job = getattr(self, '_balance_job', None)
        if job:
            try:
                self.root.after_cancel(job)
            except Exception:
                pass
            self._balance_job = None

    def root_clear_search(self):
        if hasattr(self, 'root_search_var'):
            self.root_search_var.set('')
        self.root_refresh_admins()

    def root_refresh_admins(self):
        if not hasattr(self, 'root_admin_tree'):
            return
        for item in self.root_admin_tree.get_children():
            self.root_admin_tree.delete(item)
        keyword = (getattr(self, 'root_search_var', tk.StringVar()).get() or '').strip().lower()
        admins = self.ql.lay_danh_sach_admin()
        if keyword:
            admins = [a for a in admins if keyword in a.ten_dang_nhap.lower() or keyword in (a.ten_hien_thi or '').lower()]
        for admin in admins:
            self.root_admin_tree.insert('', tk.END, values=(admin.ten_dang_nhap, admin.ten_hien_thi))
        self.apply_zebra(self.root_admin_tree)

    def root_get_selected_admin(self):
        if not hasattr(self, 'root_admin_tree'):
            return None
        sel = self.root_admin_tree.selection()
        if not sel:
            messagebox.showwarning('Chú ý', 'Chọn một tài khoản admin')
            return None
        return self.root_admin_tree.item(sel[0], 'values')[0]

    def root_open_admin_form(self, mode):
        target = None
        if mode == 'edit':
            username = self.root_get_selected_admin()
            if not username:
                return
            target = self.ql.tim_nguoi_dung(username)
            if not target:
                messagebox.showerror('Lỗi', 'Không tìm thấy tài khoản')
                return
        title = 'Tạo admin mới' if mode == 'create' else f'Cập nhật admin: {target.ten_dang_nhap}'
        top, container = self.create_modal(title, size=(480, 320))
        form = ttk.Frame(container, padding=12)
        form.pack(fill='both', expand=True)
        ttk.Label(form, text='Tên đăng nhập', style='Form.TLabel').grid(row=0, column=0, sticky='w', pady=4)
        username_entry = ttk.Entry(form, font=self.font_body)
        username_entry.grid(row=0, column=1, sticky='ew', padx=(10,0), pady=4)
        if target:
            username_entry.insert(0, target.ten_dang_nhap)
            username_entry.configure(state='disabled')
        ttk.Label(form, text='Họ tên hiển thị', style='Form.TLabel').grid(row=1, column=0, sticky='w', pady=4)
        fullname_entry = ttk.Entry(form, font=self.font_body)
        fullname_entry.grid(row=1, column=1, sticky='ew', padx=(10,0), pady=4)
        if target:
            fullname_entry.insert(0, target.ten_hien_thi)
        ttk.Label(form, text='Mật khẩu', style='Form.TLabel').grid(row=2, column=0, sticky='w', pady=4)
        password_entry = ttk.Entry(form, font=self.font_body, show='*')
        password_entry.grid(row=2, column=1, sticky='ew', padx=(10,0), pady=4)
        ttk.Label(form, text='Để trống nếu giữ nguyên', style='Body.TLabel').grid(row=3, column=0, columnspan=2, sticky='w', pady=(4,0))
        form.columnconfigure(1, weight=1)

        def save_admin():
            uname = username_entry.get().strip()
            fname = fullname_entry.get().strip()
            pwd = password_entry.get().strip()
            if mode == 'create':
                if not uname or not fname or not pwd:
                    messagebox.showerror('Lỗi', 'Vui lòng nhập đầy đủ thông tin')
                    return
                success, msg = self.ql.dang_ky_nguoi_dung(uname, pwd, vai_tro='admin', ten_hien_thi=fname)
            else:
                if not fname:
                    messagebox.showerror('Lỗi', 'Họ tên không được bỏ trống')
                    return
                success, msg = self.ql.cap_nhat_admin(target.ten_dang_nhap, ten_hien_thi=fname, mat_khau=pwd or None)
            if success:
                luu_tat_ca(self.ql)
                self.root_refresh_admins()
                top.destroy()
                messagebox.showinfo('Thông báo', msg)
            else:
                messagebox.showerror('Lỗi', msg)

        self.modal_buttons(container, [
            {'text':'Lưu', 'style':'Accent.TButton', 'command':save_admin},
            {'text':'Đóng', 'style':'Danger.TButton', 'command':top.destroy}
        ])

    def root_delete_admin(self):
        username = self.root_get_selected_admin()
        if not username:
            return
        if not messagebox.askyesno('Xác nhận', f'Xóa tài khoản {username}?'):
            return
        success, msg = self.ql.xoa_admin(username)
        if success:
            luu_tat_ca(self.ql)
            self.root_refresh_admins()
            messagebox.showinfo('Thông báo', msg)
        else:
            messagebox.showerror('Lỗi', msg)

    def root_reset_admin_password(self):
        username = self.root_get_selected_admin()
        if not username:
            return
        success, msg = self.ql.dat_lai_mat_khau(username, '123')
        if success:
            luu_tat_ca(self.ql)
            messagebox.showinfo('Thông báo', 'Đã đặt lại mật khẩu về 123')
        else:
            messagebox.showerror('Lỗi', msg)

    def refresh_lists(self):
        role = self.ql.nguoi_dung_hien_tai.vai_tro if self.ql.nguoi_dung_hien_tai else ''
        if role == 'hdv':
            self.hien_thi_tour_hdv()
            return
        if role == 'admin':
            active = getattr(self, 'active_section', 'Tour')
            if active == 'Tour':
                self.hien_thi_tour()
            elif active == 'Khách hàng':
                self.hien_thi_khach()
            elif active == 'Hướng dẫn viên':
                self.hien_thi_hdv()
            else:
                self.hien_thi_dat_admin()
            self.refresh_stats_tab()
            return
        self.hien_thi_tour()
        if role == 'user':
            self.hien_thi_khach_user()

    def search_tour(self, event=None):
        keyword = (self.search_var.get() or '').strip().lower()
        base = self.ql.danh_sach_tour
        if keyword:
            base = [t for t in base if keyword in (t.ten_tour or '').lower() or keyword in (t.ma_tour or '').lower()]
        if self.ql.nguoi_dung_hien_tai and self.ql.nguoi_dung_hien_tai.vai_tro == 'hdv':
            base = [t for t in base if str(t.huong_dan_vien) == str(self.ql.nguoi_dung_hien_tai.ma_khach_hang)]
        self.hien_thi_tour(dataset=base)

    def prompt_search(self, entity):
        top = tk.Toplevel(self.root)
        top.title('🔍 Tìm kiếm')
        top.geometry('500x200')
        top.transient(self.root)
        top.grab_set()
        self.theme.trung_tam(top, 500, 200)
        
        container = ttk.Frame(top, style='Card.TFrame', padding=20)
        container.pack(fill='both', expand=True)
        
        ttk.Label(container, text=f'🔎 Tìm kiếm {entity}', style='Title.TLabel').pack(anchor='w', pady=(0, 12))
        ttk.Label(container, text='Nhập từ khóa tìm kiếm', style='Body.TLabel').pack(anchor='w', pady=(0, 8))
        
        keyword_var = tk.StringVar()
        entry = ttk.Entry(container, textvariable=keyword_var, font=('Segoe UI', 11))
        entry.pack(fill='x', pady=(0, 16))
        entry.focus()
        
        def do_search():
            keyword = keyword_var.get().strip()
            if not keyword:
                messagebox.showwarning('Chú ý', 'Vui lòng nhập từ khóa tìm kiếm', parent=top)
                return
            if entity == 'Tour':
                self.search_var.set(keyword)
                self.search_tour()
            elif entity == 'Khách hàng':
                if hasattr(self, 'kh_search_var'):
                    self.kh_search_var.set(keyword)
                self.search_khach()
            elif entity == 'Hướng dẫn viên':
                if hasattr(self, 'hdv_search_var'):
                    self.hdv_search_var.set(keyword)
                self.search_hdv()
            top.destroy()
        
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text='🔍 Tìm kiếm', style='Accent.TButton', command=do_search).pack(side='left', padx=(0, 8))
        ttk.Button(btn_frame, text='✖ Hủy', style='Danger.TButton', command=top.destroy).pack(side='left')
        
        entry.bind('<Return>', lambda e: do_search())

    def search_khach(self):
        if not getattr(self, 'tv_kh', None):
            return
        keyword = (getattr(self, 'kh_search_var', tk.StringVar()).get() or '').strip().lower()
        rows = self.ql.danh_sach_khach_hang
        if keyword:
            rows = [k for k in rows if keyword in (k.ma_khach_hang or '').lower() or keyword in (k.ten_khach_hang or '').lower() or keyword in (k.so_dien_thoai or '').lower()]
        self.hien_thi_khach(rows)

    def search_hdv(self):
        if not getattr(self, 'tv_hdv', None):
            return
        keyword = (getattr(self, 'hdv_search_var', tk.StringVar()).get() or '').strip().lower()
        rows = getattr(self.ql, 'danh_sach_hdv', [])
        if keyword:
            rows = [h for h in rows if keyword in str(h.get('maHDV','')).lower() or keyword in str(h.get('tenHDV','')).lower() or keyword in str(h.get('sdt','')).lower()]
        self.hien_thi_hdv(rows)

    def build_stats_tab(self, parent):
        self.stats_header = ttk.Label(parent, text='Đang thống kê...', style='Body.TLabel')
        self.stats_header.pack(anchor='w')
        holder = ttk.Frame(parent, style='App.TFrame')
        holder.pack(fill='both', expand=True, pady=(8,0))
        left = ttk.Frame(holder, padding=4)
        left.pack(side='left', fill='both', expand=True)
        right = ttk.Frame(holder, padding=4)
        right.pack(side='left', fill='both', expand=True)
        self.stats_tv_tour = ttk.Treeview(left, columns=('ma_tour','so_dat','doanh_thu'), show='headings')
        for col, text, w in (('ma_tour','Mã Tour',140),('so_dat','Lượt đặt',100),('doanh_thu','Doanh thu',160)):
            self.stats_tv_tour.heading(col, text=text)
            self.stats_tv_tour.column(col, width=w, anchor='center')
        tour_scroll = ttk.Scrollbar(left, orient='vertical', command=self.stats_tv_tour.yview)
        self.stats_tv_tour.configure(yscrollcommand=tour_scroll.set)
        self.stats_tv_tour.pack(side='left', fill='both', expand=True)
        tour_scroll.pack(side='right', fill='y')
        self.stats_tv_customer = ttk.Treeview(right, columns=('ma_khach_hang','ten','tong_chi'), show='headings')
        for col, text, w in (('ma_khach_hang','Mã KH',120),('ten','Tên khách',200),('tong_chi','Tổng chi',160)):
            self.stats_tv_customer.heading(col, text=text)
            self.stats_tv_customer.column(col, width=w, anchor='center' if col != 'ten' else 'w')
        cus_scroll = ttk.Scrollbar(right, orient='vertical', command=self.stats_tv_customer.yview)
        self.stats_tv_customer.configure(yscrollcommand=cus_scroll.set)
        self.stats_tv_customer.pack(side='left', fill='both', expand=True)
        cus_scroll.pack(side='right', fill='y')

    def refresh_stats_tab(self):
        if not getattr(self, 'stats_tv_tour', None):
            return
        self.clear_tree(self.stats_tv_tour)
        self.clear_tree(self.stats_tv_customer)
        tong = sum(d.tong_tien for d in self.ql.danh_sach_dat_tour if d.trang_thai == 'da_thanh_toan')
        if getattr(self, 'stats_header', None):
            self.stats_header.config(text=f'Tổng doanh thu: {self.format_money(tong)}')
        counts = {}
        revenue_per_tour = {}
        for d in self.ql.danh_sach_dat_tour:
            counts[d.ma_tour] = counts.get(d.ma_tour, 0) + 1
            if d.trang_thai == 'da_thanh_toan':
                revenue_per_tour[d.ma_tour] = revenue_per_tour.get(d.ma_tour, 0) + d.tong_tien
        tour_stats = []
        for ma, c in counts.items():
            tour_stats.append((ma, revenue_per_tour.get(ma, 0), c))
        tour_stats.sort(key=lambda item: (-item[1], item[2], item[0]))
        for ma, revenue, count in tour_stats:
            self.stats_tv_tour.insert('', tk.END, values=(ma, count, self.format_money(revenue)))
        topcus = {}
        for d in self.ql.danh_sach_dat_tour:
            if d.trang_thai == 'da_thanh_toan':
                topcus[d.ma_khach_hang] = topcus.get(d.ma_khach_hang, 0) + d.tong_tien
        for ma, s in sorted(topcus.items(), key=lambda x: x[1], reverse=True):
            kh = self.ql.tim_khach_hang(ma)
            self.stats_tv_customer.insert('', tk.END, values=(ma, kh.ten_khach_hang if kh else ma, self.format_money(s)))

    def hien_thi_dat_admin(self):
        if not self.tv_dat:
            return
        self.clear_tree(self.tv_dat)
        for d in self.ql.danh_sach_dat_tour:
            trang_thai_formatted = d.trang_thai.replace('_', ' ').title() if d.trang_thai else ''
            tong_formatted = self.format_money(d.tong_tien)
            self.tv_dat.insert('', tk.END, values=(d.ma_dat_tour, d.ma_tour, d.ma_khach_hang, d.so_nguoi, trang_thai_formatted, tong_formatted))
        self.apply_zebra(self.tv_dat)

    def hien_thi_tour(self, dataset=None):
        if not hasattr(self, 'tv_tour') or not self.tv_tour:
            return
        rows = dataset if dataset is not None else self.ql.danh_sach_tour
        self.clear_tree(self.tv_tour)
        for t in rows:
            try:
                capacity = int(t.so_cho)
            except Exception:
                capacity = t.so_cho if isinstance(t.so_cho, int) else 0
            booked = sum(d.so_nguoi for d in self.ql.danh_sach_dat_tour if d.ma_tour == t.ma_tour and d.trang_thai == 'da_thanh_toan')
            remaining = max(0, capacity - booked)
            trang_thai = self.ql.dien_giai_trang_thai_tour(t)
            self.tv_tour.insert('', tk.END, values=(t.ma_tour, t.ten_tour, self.format_money(t.gia_tour), remaining, trang_thai, t.huong_dan_vien))
        self.apply_zebra(self.tv_tour)

    def hien_thi_tour_hdv(self):
        if not hasattr(self, 'tv_tour') or not self.tv_tour:
            return
        hdv_id = self.ql.nguoi_dung_hien_tai.ma_khach_hang if self.ql.nguoi_dung_hien_tai else ''
        rows = [t for t in self.ql.danh_sach_tour if str(t.huong_dan_vien) == str(hdv_id)]
        self.hien_thi_tour(dataset=rows)

    def hien_thi_hdv(self, dataset=None):
        if not self.tv_hdv:
            return
        self.clear_tree(self.tv_hdv)
        if not hasattr(self.ql, 'danh_sach_hdv'):
            return
        rows = dataset if dataset is not None else self.ql.danh_sach_hdv
        for h in rows:
            self.tv_hdv.insert('', tk.END, values=(h.get('maHDV',''), h.get('tenHDV',''), h.get('sdt',''), h.get('kinhNghiem','')))
        self.apply_zebra(self.tv_hdv)

    def hien_thi_khach(self, dataset=None):
        if not self.tv_kh:
            return
        rows = dataset if dataset is not None else self.ql.danh_sach_khach_hang
        self.clear_tree(self.tv_kh)
        for k in rows:
            self.tv_kh.insert('', tk.END, values=(k.ma_khach_hang, k.ten_khach_hang, k.so_dien_thoai))
        self.apply_zebra(self.tv_kh)

    def on_resize(self, event=None):
        if event and event.widget != self.root:
            return
        try:
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            if width < 800 or height < 600:
                return
            left_width = int(width * 0.55) 
            if hasattr(self, 'tv_tour') and self.tv_tour:
                col_widths_tour = {
                    'ma_tour': 90,
                    'ten_tour': max(150, int(left_width * 0.35)),
                    'gia': 120,
                    'so_cho': 110,
                    'trang_thai': max(100, int(left_width * 0.25)),
                    'hdv': 90
                }
                for col, w in col_widths_tour.items():
                    self.tv_tour.column(col, width=w)
            right_width = int(width * 0.35)
            if hasattr(self, 'tv_kh') and self.tv_kh:
                col_widths_kh = {
                    'ma_khach_hang': 110,
                    'ten': max(150, int(right_width * 0.5)),
                    'so_dien_thoai': 130
                }
                for col, w in col_widths_kh.items():
                    self.tv_kh.column(col, width=w)
            if hasattr(self, 'tv_hdv') and self.tv_hdv:
                col_widths_hdv = {
                    'ma_hdv': 110,
                    'ten_hdv': max(150, int(right_width * 0.4)),
                    'sdt': 140,
                    'kinh_nghiem': 120
                }
                for col, w in col_widths_hdv.items():
                    self.tv_hdv.column(col, width=w)
            if hasattr(self, 'tv_dat') and self.tv_dat:
                col_widths_dat = {
                    'ma_dat': 110,
                    'ma_tour': 110,
                    'ma_khach_hang': 110,
                    'so_nguoi': 90,
                    'trang_thai': 120,
                    'tong': 140
                }
                for col, w in col_widths_dat.items():
                    self.tv_dat.column(col, width=w)
        except Exception:
            pass

    def hien_thi_khach_user(self):
        if not hasattr(self, 'tv_kh') or not self.tv_kh:
            return
        if not self.ql.nguoi_dung_hien_tai:
            return
        self.clear_tree(self.tv_kh)
        rows = [k for k in self.ql.danh_sach_khach_hang if k.ma_khach_hang == self.ql.nguoi_dung_hien_tai.ma_khach_hang]
        for k in rows:
            self.tv_kh.insert('', tk.END, values=(k.ma_khach_hang, k.ten_khach_hang, k.so_dien_thoai, k.email, self.format_money(k.so_du)))
        self.apply_zebra(self.tv_kh)

    def get_selected_customer(self):
        if not getattr(self, 'tv_kh', None):
            return None
        sel = self.tv_kh.selection()
        if not sel:
            messagebox.showwarning('Chú ý', 'Chọn một khách hàng trước')
            return None
        values = self.tv_kh.item(sel[0], 'values')
        ma = values[0]
        return self.ql.tim_khach_hang(ma)

