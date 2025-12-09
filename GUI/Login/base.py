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
        self.bg = '#f5f6fa'
        self.surface = '#ffffff'
        self.primary = '#1b6dc1'
        self.danger = '#c44536'
        self.accent = '#1aa5a5'
        self.text = '#1f2933'
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass
        self.configure_base()

    def configure_base(self):
        self.root.configure(bg=self.bg)
        self.style.configure('App.TFrame', background=self.bg)
        self.style.configure('Card.TFrame', background=self.surface, relief='flat')
        self.style.configure('Header.TLabel', background=self.primary, foreground='white', font=('Segoe UI', 14, 'bold'))
        self.style.configure('Title.TLabel', background=self.bg, foreground=self.text, font=('Segoe UI', 12, 'bold'))
        self.style.configure('Body.TLabel', background=self.surface, foreground=self.text, font=('Segoe UI', 10))
        self.style.configure('BodyBold.TLabel', background=self.surface, foreground=self.text, font=('Segoe UI', 10, 'bold'))
        self.style.configure('Context.TFrame', background=self.surface)
        self.style.configure('App.TButton', font=('Segoe UI', 10), padding=6)
        self.style.map('App.TButton', background=[('!disabled', self.primary), ('active', '#0f58a6')], foreground=[('!disabled', 'white')])
        self.style.configure('Accent.TButton', font=('Segoe UI', 10), padding=6)
        self.style.map('Accent.TButton', background=[('!disabled', self.accent), ('active', '#168b8b')], foreground=[('!disabled', 'white')])
        self.style.configure('Danger.TButton', font=('Segoe UI', 10), padding=6)
        self.style.map('Danger.TButton', background=[('!disabled', self.danger), ('active', '#a13224')], foreground=[('!disabled', 'white')])
        self.style.configure('Toolbar.TButton', font=('Segoe UI', 10, 'bold'), padding=(14, 8))
        self.style.map('Toolbar.TButton', background=[('!disabled', '#1f6feb'), ('active', '#1553b2')], foreground=[('!disabled', 'white')])
        self.style.configure('Ghost.TButton', font=('Segoe UI', 10), padding=(10,6))
        self.style.map('Ghost.TButton', background=[('active', '#e6ecf5')], foreground=[('!disabled', self.text)])
        self.style.configure('Form.TLabel', background=self.surface, foreground=self.text, font=('Segoe UI', 10))
        self.style.configure('FormValue.TEntry', font=('Segoe UI', 10))
        self.style.configure('Card.TLabelframe', background=self.surface, foreground=self.text, font=('Segoe UI', 11, 'bold'))
        self.style.configure('Card.TLabelframe.Label', background=self.surface, foreground=self.text)
        self.apply_treeview()

    def apply_treeview(self):
        self.style.configure('Treeview', font=('Segoe UI', 10), rowheight=26, background='#fdfdfd', fieldbackground='#fdfdfd', bordercolor='#dfe3e8')
        self.style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background=self.primary, foreground='white')
        self.style.map('Treeview', background=[('selected', self.accent)], foreground=[('selected', 'white')])

    def center(self, win, width, height):
        try:
            win.update_idletasks()
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = int((sw - width) / 2)
            y = int((sh - height) / 3)
            win.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass

    def card_frame(self, parent, padding=16):
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
        self.frame = tk.Frame(self.root, bg=self.theme.bg)
        self.frame.pack(fill='both', expand=True)
        self.theme.center(self.root, 460, 260)
        card = self.theme.card_frame(self.frame, padding=24)
        card.place(relx=0.5, rely=0.5, anchor='c', width=380, height=200)
        title = ttk.Label(card, text='Đăng nhập hệ thống', style='Title.TLabel')
        title.pack(anchor='center', pady=(0,12))
        form = ttk.Frame(card, padding=4)
        form.pack(fill='both', expand=True)
        ttk.Label(form, text='Tên đăng nhập', style='Form.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(form, text='Mật khẩu', style='Form.TLabel').grid(row=1, column=0, sticky='w', pady=(8,0))
        self.e_user = ttk.Entry(form, font=self.font_body)
        self.e_pass = ttk.Entry(form, font=self.font_body, show='*')
        self.e_user.grid(row=0, column=1, padx=8, sticky='ew')
        self.e_pass.grid(row=1, column=1, padx=8, sticky='ew', pady=(8,0))
        form.columnconfigure(1, weight=1)
        buttons = ttk.Frame(card)
        buttons.pack(fill='x', pady=(12,0))
        ttk.Button(buttons, text='Đăng nhập', style='App.TButton', command=self.dang_nhap).pack(side='left')
        ttk.Button(buttons, text='Đăng ký guest', style='Accent.TButton', command=self.dang_ky_guest).pack(side='left', padx=8)
        ttk.Button(buttons, text='Thoát', style='Danger.TButton', command=self.root.quit).pack(side='right')

    def create_modal(self, title, size=None, maximize=True):
        top = tk.Toplevel(self.root)
        top.title(title)
        top.configure(bg=self.theme.bg)
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
                self.theme.center(top, width, height)
        else:
            self.theme.center(top, width, height)
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
        return self.ql.TimTour(values[0])

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

        container._preview_images = previews  # keep references
        info_block = ttk.Frame(wrapper, style='Context.TFrame')
        info_block.pack(fill='both', expand=True)
        ttk.Label(info_block, text=short, style='BodyBold.TLabel').pack(anchor='w')
        ttk.Label(info_block, text=f'Địa chỉ: {display}', style='Body.TLabel').pack(anchor='w', pady=(4,0))
        if lat and lon:
            ttk.Label(info_block, text=f'Tọa độ: {lat}, {lon}', style='Body.TLabel').pack(anchor='w', pady=(4,0))
            osm_link = ttk.Label(info_block, text='Mở trên OpenStreetMap', foreground=self.theme.primary, cursor='hand2', style='Body.TLabel')
            osm_link.pack(anchor='w', pady=(2,0))
            osm_link.bind('<Button-1>', lambda e, lat=lat, lon=lon: webbrowser.open(f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=12/{lat}/{lon}"))
            if map_url:
                bing_link = ttk.Label(info_block, text='Mở trên Bing Maps (vệ tinh)', foreground=self.theme.primary, cursor='hand2', style='Body.TLabel')
                bing_link.pack(anchor='w', pady=(2,0))
                bing_link.bind('<Button-1>', lambda e, u=map_url: webbrowser.open(u))
        weather = info.get('weather')
        ttk.Label(info_block, text=f'Nhiệt độ: {self.format_weather_text(weather)}', style='Body.TLabel').pack(anchor='w', pady=(6,0))

    def dang_nhap(self):
        u = self.e_user.get()
        p = self.e_pass.get()
        if self.ql.Login(u, p):
            name = self.ql.LayTenHienThi(self.ql.currentUser)
            role = self.ql.currentUser.role.upper()
            messagebox.showinfo('Thông báo', f'Đăng nhập thành công: {name} ({role})')
            self.build_giao_dien_chinh()
        else:
            messagebox.showerror('Lỗi', 'Sai tài khoản hoặc mật khẩu')

    def build_giao_dien_chinh(self):
        if self.frame:
            self.frame.destroy()
        if self.ql.currentUser and self.ql.currentUser.role == 'root':
            self.build_root_console()
            return
        self.frame = ttk.Frame(self.root, style='App.TFrame')
        self.frame.pack(fill='both', expand=True)
        try:
            self.root.state('zoomed')
        except Exception:
            pass
        header = ttk.Frame(self.frame, padding=(24,18))
        header.pack(fill='x')
        ttk.Label(header, text='Quản lý Tour du lịch', style='Title.TLabel').pack(side='left')
        summary_bar = ttk.Frame(self.frame, padding=(24,0))
        summary_bar.pack(fill='x')
        role_text = self.ql.currentUser.role.upper() if self.ql.currentUser else ''
        display_name = self.ql.LayTenHienThi(self.ql.currentUser) if self.ql.currentUser else ''
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
        role = self.ql.currentUser.role if self.ql.currentUser else ''
        paned = ttk.Panedwindow(self.frame, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=24, pady=18)
        left_panel = ttk.Frame(paned, style='Card.TFrame', padding=16)
        right_panel = ttk.Frame(paned, style='Card.TFrame', padding=16)
        paned.add(left_panel, weight=3)
        paned.add(right_panel, weight=2)
        left_head = ttk.Frame(left_panel)
        left_head.pack(fill='x', pady=(0,12))
        ttk.Label(left_head, text='Danh sách tour', style='Title.TLabel').pack(side='left')
        tour_frame = ttk.Frame(left_panel)
        tour_frame.pack(fill='both', expand=True)
        self.tv_tour = ttk.Treeview(tour_frame, columns=('MaTour','TenTour','Gia','SoCho','TrangThai','HDV'), show='headings')
        for col, text, w in (
            ('MaTour','Mã Tour',90),
            ('TenTour','Tên Tour',200),
            ('Gia','Giá',120),
            ('SoCho','Số chỗ còn',110),
            ('TrangThai','Trạng thái',130),
            ('HDV','HDV',90)):
            self.tv_tour.heading(col, text=text)
            self.tv_tour.column(col, width=w, anchor='center' if col not in ('TenTour','TrangThai') else 'w')
        tour_scroll = ttk.Scrollbar(tour_frame, orient='vertical', command=self.tv_tour.yview)
        self.tv_tour.configure(yscrollcommand=tour_scroll.set)
        self.tv_tour.pack(side='left', fill='both', expand=True)
        tour_scroll.pack(side='right', fill='y')
        self.tv_tour.bind('<<TreeviewSelect>>', self.on_tour_select)
        self.tour_context = ttk.Label(left_panel, text='Chọn tour để xem thông tin', style='Body.TLabel')
        self.tour_context.pack(fill='x', pady=(12,0))
        self.right_panel = right_panel
        role = self.ql.currentUser.role if self.ql.currentUser else ''
        self.tv_hdv = None
        self.tv_kh = None
        self.tv_dat = None
        self.stats_tv_tour = None
        self.stats_tv_customer = None
        if role == 'admin':
            self.kh_search_var = tk.StringVar()
            self.hdv_search_var = tk.StringVar()
            admin_tabs = ttk.Notebook(right_panel)
            admin_tabs.pack(fill='both', expand=True)
            kh_tab = ttk.Frame(admin_tabs, style='App.TFrame', padding=6)
            hdv_tab = ttk.Frame(admin_tabs, style='App.TFrame', padding=6)
            dat_tab = ttk.Frame(admin_tabs, style='App.TFrame', padding=6)
            admin_tabs.add(kh_tab, text='Khách hàng')
            admin_tabs.add(hdv_tab, text='Hướng dẫn viên')
            admin_tabs.add(dat_tab, text='Đơn đặt')
            kh_tools = ttk.Frame(kh_tab, padding=(0,0,0,8))
            kh_tools.pack(fill='x')
            ttk.Entry(kh_tools, textvariable=self.kh_search_var, font=self.font_body).pack(side='left', fill='x', expand=True, padx=(0,8))
            ttk.Button(kh_tools, text='Tìm', style='Accent.TButton', command=self.search_khach).pack(side='left')
            ttk.Button(kh_tools, text='Hiển thị tất cả', style='Ghost.TButton', command=self.hien_thi_khach).pack(side='left', padx=(6,0))
            kh_body = ttk.Frame(kh_tab)
            kh_body.pack(fill='both', expand=True)
            self.tv_kh = ttk.Treeview(kh_body, columns=('MaKH','Ten','SoDT'), show='headings')
            for col, text, width in (('MaKH','Mã KH',110),('Ten','Tên',200),('SoDT','SĐT',130)):
                self.tv_kh.heading(col, text=text)
                self.tv_kh.column(col, width=width, anchor='center' if col != 'Ten' else 'w')
            kh_scroll = ttk.Scrollbar(kh_body, orient='vertical', command=self.tv_kh.yview)
            self.tv_kh.configure(yscrollcommand=kh_scroll.set)
            self.tv_kh.pack(side='left', fill='both', expand=True)
            kh_scroll.pack(side='right', fill='y')
            hdv_tools = ttk.Frame(hdv_tab, padding=(0,0,0,8))
            hdv_tools.pack(fill='x')
            ttk.Entry(hdv_tools, textvariable=self.hdv_search_var, font=self.font_body).pack(side='left', fill='x', expand=True, padx=(0,8))
            ttk.Button(hdv_tools, text='Tìm', style='Accent.TButton', command=self.search_hdv).pack(side='left')
            ttk.Button(hdv_tools, text='Hiển thị tất cả', style='Ghost.TButton', command=self.hien_thi_hdv).pack(side='left', padx=(6,0))
            hdv_body = ttk.Frame(hdv_tab)
            hdv_body.pack(fill='both', expand=True)
            self.tv_hdv = ttk.Treeview(hdv_body, columns=('MaHDV','TenHDV','SDT','KinhNghiem'), show='headings')
            for col, text, width in (('MaHDV','Mã HDV',110),('TenHDV','Tên',200),('SDT','SĐT',140),('KinhNghiem','Kinh nghiệm',120)):
                self.tv_hdv.heading(col, text=text)
                self.tv_hdv.column(col, width=width, anchor='center' if col != 'TenHDV' else 'w')
            hdv_scroll = ttk.Scrollbar(hdv_body, orient='vertical', command=self.tv_hdv.yview)
            self.tv_hdv.configure(yscrollcommand=hdv_scroll.set)
            self.tv_hdv.pack(side='left', fill='both', expand=True)
            hdv_scroll.pack(side='right', fill='y')
            self.tv_dat = ttk.Treeview(dat_tab, columns=('MaDat','MaTour','MaKH','SoNguoi','TrangThai','Tong'), show='headings')
            for col, text, width in (('MaDat','Mã Đặt',110),('MaTour','Mã Tour',110),('MaKH','Mã KH',110),('SoNguoi','Số người',90),('TrangThai','Trạng thái',120),('Tong','Tổng tiền',140)):
                self.tv_dat.heading(col, text=text)
                self.tv_dat.column(col, width=width, anchor='center')
            dat_scroll = ttk.Scrollbar(dat_tab, orient='vertical', command=self.tv_dat.yview)
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
            wrap = ttk.Frame(toolbar, style='App.TFrame')
            wrap.pack(fill='x')
            build_toolbar_section(wrap, 'Tour', [
                ('Thêm', self.them_tour, 'Toolbar.TButton'),
                ('Sửa', self.sua_tour, 'App.TButton'),
                ('Xóa', self.xoa_tour, 'Danger.TButton'),
                ('Tìm', lambda: self.prompt_search('Tour'), 'Ghost.TButton')
            ])
            build_toolbar_section(wrap, 'Khách hàng', [
                ('Thêm', self.them_khach, 'Toolbar.TButton'),
                ('Sửa', self.sua_khach, 'App.TButton'),
                ('Xóa', self.xoa_khach, 'Danger.TButton'),
                ('Tìm', lambda: self.prompt_search('Khách hàng'), 'Ghost.TButton')
            ])
            build_toolbar_section(wrap, 'Hướng dẫn viên', [
                ('Thêm', self.them_hdv, 'Toolbar.TButton'),
                ('Sửa', self.sua_hdv, 'App.TButton'),
                ('Xóa', self.xoa_hdv, 'Danger.TButton'),
                ('Tìm', lambda: self.prompt_search('Hướng dẫn viên'), 'Ghost.TButton')
            ])
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
        if role != 'hdv':
            self.tv_tour.bind('<Double-Button-1>', self.show_tour_details)
        if getattr(self, 'tv_kh', None):
            self.tv_kh.bind('<Double-Button-1>', self.show_kh_details)
        if getattr(self, 'tv_hdv', None):
            self.tv_hdv.bind('<Double-Button-1>', self.show_hdv_details)

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
        ttk.Label(self.frame, text='Tài khoản root chỉ được thao tác với Admin', style='Body.TLabel').pack(anchor='w', padx=24, pady=(0,12))
        controls = ttk.Frame(self.frame, padding=(24,0,24,12))
        controls.pack(fill='x')
        self.root_search_var = tk.StringVar()
        ttk.Entry(controls, textvariable=self.root_search_var, font=self.font_body, width=32).pack(side='left')
        ttk.Button(controls, text='Tìm', style='Accent.TButton', command=self.root_refresh_admins).pack(side='left', padx=6)
        ttk.Button(controls, text='Làm mới', style='App.TButton', command=self.root_clear_search).pack(side='left')
        table_wrap = ttk.Frame(self.frame, padding=(24,0,24,12))
        table_wrap.pack(fill='both', expand=True)
        self.root_admin_tree = ttk.Treeview(table_wrap, columns=('Username','FullName'), show='headings')
        self.root_admin_tree.heading('Username', text='Tên đăng nhập')
        self.root_admin_tree.heading('FullName', text='Họ tên hiển thị')
        self.root_admin_tree.column('Username', width=220, anchor='center')
        self.root_admin_tree.column('FullName', width=320, anchor='w')
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
        admins = self.ql.LayDanhSachAdmin()
        if keyword:
            admins = [a for a in admins if keyword in a.username.lower() or keyword in (a.fullName or '').lower()]
        for admin in admins:
            self.root_admin_tree.insert('', tk.END, values=(admin.username, admin.fullName))
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
            target = self.ql.TimUser(username)
            if not target:
                messagebox.showerror('Lỗi', 'Không tìm thấy tài khoản')
                return
        title = 'Tạo admin mới' if mode == 'create' else f'Cập nhật admin: {target.username}'
        top, container = self.create_modal(title, size=(480, 320))
        form = ttk.Frame(container, padding=12)
        form.pack(fill='both', expand=True)
        ttk.Label(form, text='Tên đăng nhập', style='Form.TLabel').grid(row=0, column=0, sticky='w', pady=4)
        username_entry = ttk.Entry(form, font=self.font_body)
        username_entry.grid(row=0, column=1, sticky='ew', padx=(10,0), pady=4)
        if target:
            username_entry.insert(0, target.username)
            username_entry.configure(state='disabled')
        ttk.Label(form, text='Họ tên hiển thị', style='Form.TLabel').grid(row=1, column=0, sticky='w', pady=4)
        fullname_entry = ttk.Entry(form, font=self.font_body)
        fullname_entry.grid(row=1, column=1, sticky='ew', padx=(10,0), pady=4)
        if target:
            fullname_entry.insert(0, target.fullName)
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
                success, msg = self.ql.DangKyUser(uname, pwd, role='admin', fullName=fname)
            else:
                if not fname:
                    messagebox.showerror('Lỗi', 'Họ tên không được bỏ trống')
                    return
                success, msg = self.ql.CapNhatAdmin(target.username, fullName=fname, password=pwd or None)
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
        success, msg = self.ql.XoaAdmin(username)
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
        success, msg = self.ql.ResetMatKhau(username, '123')
        if success:
            luu_tat_ca(self.ql)
            messagebox.showinfo('Thông báo', 'Đã đặt lại mật khẩu về 123')
        else:
            messagebox.showerror('Lỗi', msg)

    def refresh_lists(self):
        role = self.ql.currentUser.role if self.ql.currentUser else ''
        if role == 'hdv':
            self.hien_thi_tour_hdv()
        else:
            self.hien_thi_tour()
        if role == 'admin':
            self.hien_thi_khach()
            self.hien_thi_hdv()
            self.hien_thi_dat_admin()
            self.refresh_stats_tab()
        elif role == 'user':
            self.hien_thi_khach_user()

    def search_tour(self, event=None):
        keyword = (self.search_var.get() or '').strip().lower()
        base = self.ql.danhSachTour
        if keyword:
            base = [t for t in base if keyword in (t.tenTour or '').lower() or keyword in (t.maTour or '').lower()]
        if self.ql.currentUser and self.ql.currentUser.role == 'hdv':
            base = [t for t in base if str(t.huongDanVien) == str(self.ql.currentUser.maKH)]
        self.hien_thi_tour(dataset=base)

    def prompt_search(self, entity):
        top = tk.Toplevel(self.root)
        top.title('🔍 Tìm kiếm')
        top.geometry('500x200')
        top.transient(self.root)
        top.grab_set()
        self.theme.center(top, 500, 200)
        
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
        rows = self.ql.danhSachKhachHang
        if keyword:
            rows = [k for k in rows if keyword in (k.maKH or '').lower() or keyword in (k.tenKH or '').lower() or keyword in (k.soDT or '').lower()]
        self.hien_thi_khach(rows)

    def search_hdv(self):
        if not getattr(self, 'tv_hdv', None):
            return
        keyword = (getattr(self, 'hdv_search_var', tk.StringVar()).get() or '').strip().lower()
        rows = getattr(self.ql, 'danhSachHDV', [])
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
        self.stats_tv_tour = ttk.Treeview(left, columns=('MaTour','SoDat','DoanhThu'), show='headings')
        for col, text, w in (('MaTour','Mã Tour',140),('SoDat','Lượt đặt',100),('DoanhThu','Doanh thu',160)):
            self.stats_tv_tour.heading(col, text=text)
            self.stats_tv_tour.column(col, width=w, anchor='center')
        tour_scroll = ttk.Scrollbar(left, orient='vertical', command=self.stats_tv_tour.yview)
        self.stats_tv_tour.configure(yscrollcommand=tour_scroll.set)
        self.stats_tv_tour.pack(side='left', fill='both', expand=True)
        tour_scroll.pack(side='right', fill='y')
        self.stats_tv_customer = ttk.Treeview(right, columns=('MaKH','Ten','TongChi'), show='headings')
        for col, text, w in (('MaKH','Mã KH',120),('Ten','Tên khách',200),('TongChi','Tổng chi',160)):
            self.stats_tv_customer.heading(col, text=text)
            self.stats_tv_customer.column(col, width=w, anchor='center' if col != 'Ten' else 'w')
        cus_scroll = ttk.Scrollbar(right, orient='vertical', command=self.stats_tv_customer.yview)
        self.stats_tv_customer.configure(yscrollcommand=cus_scroll.set)
        self.stats_tv_customer.pack(side='left', fill='both', expand=True)
        cus_scroll.pack(side='right', fill='y')

    def refresh_stats_tab(self):
        if not getattr(self, 'stats_tv_tour', None):
            return
        self.clear_tree(self.stats_tv_tour)
        self.clear_tree(self.stats_tv_customer)
        tong = sum(d.tongTien for d in self.ql.danhSachDatTour if d.trangThai == 'da_thanh_toan')
        if getattr(self, 'stats_header', None):
            self.stats_header.config(text=f'Tổng doanh thu: {self.format_money(tong)}')
        counts = {}
        revenue_per_tour = {}
        for d in self.ql.danhSachDatTour:
            counts[d.maTour] = counts.get(d.maTour, 0) + 1
            if d.trangThai == 'da_thanh_toan':
                revenue_per_tour[d.maTour] = revenue_per_tour.get(d.maTour, 0) + d.tongTien
        tour_stats = []
        for ma, c in counts.items():
            tour_stats.append((ma, revenue_per_tour.get(ma, 0), c))
        tour_stats.sort(key=lambda item: (-item[1], item[2], item[0]))
        for ma, revenue, count in tour_stats:
            self.stats_tv_tour.insert('', tk.END, values=(ma, count, self.format_money(revenue)))
        topcus = {}
        for d in self.ql.danhSachDatTour:
            if d.trangThai == 'da_thanh_toan':
                topcus[d.maKH] = topcus.get(d.maKH, 0) + d.tongTien
        for ma, s in sorted(topcus.items(), key=lambda x: x[1], reverse=True):
            kh = self.ql.TimKhacHang(ma)
            self.stats_tv_customer.insert('', tk.END, values=(ma, kh.tenKH if kh else ma, self.format_money(s)))

    def hien_thi_dat_admin(self):
        if not self.tv_dat:
            return
        self.clear_tree(self.tv_dat)
        for d in self.ql.danhSachDatTour:
            self.tv_dat.insert('', tk.END, values=(d.maDat, d.maTour, d.maKH, d.soNguoi, d.trangThai, d.tongTien))
        self.apply_zebra(self.tv_dat)

    def hien_thi_tour(self, dataset=None):
        if not hasattr(self, 'tv_tour') or not self.tv_tour:
            return
        rows = dataset if dataset is not None else self.ql.danhSachTour
        self.clear_tree(self.tv_tour)
        for t in rows:
            try:
                capacity = int(t.soCho)
            except Exception:
                capacity = t.soCho if isinstance(t.soCho, int) else 0
            booked = sum(d.soNguoi for d in self.ql.danhSachDatTour if d.maTour == t.maTour and d.trangThai == 'da_thanh_toan')
            remaining = max(0, capacity - booked)
            trang_thai = self.ql.dien_giai_trang_thai_tour(t)
            self.tv_tour.insert('', tk.END, values=(t.maTour, t.tenTour, self.format_money(t.gia), remaining, trang_thai, t.huongDanVien))
        self.apply_zebra(self.tv_tour)

    def hien_thi_tour_hdv(self):
        if not hasattr(self, 'tv_tour') or not self.tv_tour:
            return
        hdv_id = self.ql.currentUser.maKH if self.ql.currentUser else ''
        rows = [t for t in self.ql.danhSachTour if str(t.huongDanVien) == str(hdv_id)]
        self.hien_thi_tour(dataset=rows)

    def hien_thi_hdv(self, dataset=None):
        if not self.tv_hdv:
            return
        self.clear_tree(self.tv_hdv)
        if not hasattr(self.ql, 'danhSachHDV'):
            return
        rows = dataset if dataset is not None else self.ql.danhSachHDV
        for h in rows:
            self.tv_hdv.insert('', tk.END, values=(h.get('maHDV',''), h.get('tenHDV',''), h.get('sdt',''), h.get('kinhNghiem','')))
        self.apply_zebra(self.tv_hdv)

    def hien_thi_khach(self, dataset=None):
        if not self.tv_kh:
            return
        rows = dataset if dataset is not None else self.ql.danhSachKhachHang
        self.clear_tree(self.tv_kh)
        for k in rows:
            self.tv_kh.insert('', tk.END, values=(k.maKH, k.tenKH, k.soDT))
        self.apply_zebra(self.tv_kh)

    def hien_thi_khach_user(self):
        if not hasattr(self, 'tv_kh') or not self.tv_kh:
            return
        if not self.ql.currentUser:
            return
        self.clear_tree(self.tv_kh)
        rows = [k for k in self.ql.danhSachKhachHang if k.maKH == self.ql.currentUser.maKH]
        for k in rows:
            self.tv_kh.insert('', tk.END, values=(k.maKH, k.tenKH, k.soDT, k.email, self.format_money(k.soDu)))
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
        return self.ql.TimKhacHang(ma)

