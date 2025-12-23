from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
import urllib.parse
import urllib.request
import json
import io
import webbrowser
import re
import html as html_module
import math
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple
try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except Exception:
    Image = None
    ImageTk = None
    ImageDraw = None
    PIL_AVAILABLE = False
from .base import GiaoDienCoSo, GoiY

BING_USER_AGENT = "HUIT-BingMap/2.0"
BING_GEOCODE_URL = "https://nominatim.openstreetmap.org/search?format=json&limit=1&q={query}"
BING_TILE_URL_TEMPLATE = "https://ecn.t{server}.tiles.virtualearth.net/tiles/a{quadkey}.jpeg?g=1"
BING_MAP_URL_TEMPLATE = "https://www.bing.com/maps?cp={lat:.7f}~{lon:.7f}&sty=a&lvl={zoom}"


class BingMapImageError(RuntimeError):
    """Raised when preview generation fails."""


@dataclass
class MapSnapshot:
    place: str
    display_name: str
    latitude: float
    longitude: float
    zoom: int
    tiles: int
    image: "Image.Image"
    map_url: str

    def to_png_bytes(self) -> bytes:
        buffer = io.BytesIO()
        self.image.save(buffer, format="PNG")
        return buffer.getvalue()


class BingMapImageAPI:
    tile_size: int = 256
    tile_servers: Tuple[str, ...] = tuple(str(i) for i in range(0, 8))

    def __init__(
        self,
        *,
        default_zoom: int = 16,
        default_tiles: int = 3,
        timeout: int = 12,
    ) -> None:
        if not PIL_AVAILABLE or Image is None or ImageDraw is None:
            raise ImportError("Pillow với ImageDraw là bắt buộc để tạo ảnh Bing Map")
        if default_tiles % 2 == 0 or default_tiles < 1:
            raise ValueError("default_tiles must be an odd positive integer")
        self.default_zoom = default_zoom
        self.default_tiles = default_tiles
        self.timeout = timeout
        self._tile_cache: Dict[str, Image.Image] = {}

    def create_map_snapshot(
        self,
        place: str,
        *,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        zoom: Optional[int] = None,
        tiles: Optional[int] = None,
    ) -> MapSnapshot:
        if not place:
            raise BingMapImageError("Địa điểm không được để trống")
        zoom = zoom or self.default_zoom
        tiles = tiles or self.default_tiles
        if tiles % 2 == 0 or tiles < 1:
            raise BingMapImageError("Số lượng tile phải là số lẻ")
        display_name, lat, lon = self._ensure_coordinates(place, latitude, longitude)
        composed = self._compose_tile_grid(lat, lon, zoom, tiles)
        self._draw_marker(composed)
        map_url = BING_MAP_URL_TEMPLATE.format(lat=lat, lon=lon, zoom=zoom)
        return MapSnapshot(
            place=place,
            display_name=display_name,
            latitude=lat,
            longitude=lon,
            zoom=zoom,
            tiles=tiles,
            image=composed,
            map_url=map_url,
        )

    def _ensure_coordinates(
        self,
        place: str,
        latitude: Optional[float],
        longitude: Optional[float],
    ) -> Tuple[str, float, float]:
        if latitude is not None and longitude is not None:
            try:
                return place, float(latitude), float(longitude)
            except (TypeError, ValueError) as exc:
                raise BingMapImageError("Tọa độ không hợp lệ") from exc
        return self._geocode(place)

    def _geocode(self, query: str) -> Tuple[str, float, float]:
        encoded = urllib.parse.quote_plus(query)
        url = BING_GEOCODE_URL.format(query=encoded)
        req = urllib.request.Request(url, headers={"User-Agent": BING_USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.load(resp)
        if not data:
            raise BingMapImageError("Không tìm thấy tọa độ phù hợp")
        entry = data[0]
        return (
            entry.get("display_name", query),
            float(entry["lat"]),
            float(entry["lon"]),
        )

    def _compose_tile_grid(self, lat: float, lon: float, zoom: int, tiles: int) -> "Image.Image":
        center_x, center_y = self._latlon_to_tile(lat, lon, zoom)
        half = tiles // 2
        dim = tiles * self.tile_size
        canvas = Image.new("RGB", (dim, dim))
        start_x = math.floor(center_x) - half
        start_y = math.floor(center_y) - half
        n = 2 ** zoom
        for row in range(tiles):
            for col in range(tiles):
                tile_x = (start_x + col) % n
                tile_y = min(max(start_y + row, 0), n - 1)
                quadkey = self._tile_to_quadkey(tile_x, tile_y, zoom)
                tile_img = self._get_tile_image(quadkey)
                box = (col * self.tile_size, row * self.tile_size)
                canvas.paste(tile_img, box)
        return canvas

    def _draw_marker(self, image: "Image.Image") -> None:
        radius = max(8, self.tile_size // 16)
        center = (image.width // 2, image.height // 2)
        draw = ImageDraw.Draw(image)
        draw.ellipse(
            [
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ],
            fill=(220, 40, 60),
            outline=(255, 255, 255),
            width=3,
        )

    def _get_tile_image(self, quadkey: str) -> "Image.Image":
        if quadkey in self._tile_cache:
            return self._tile_cache[quadkey]
        last_error: Optional[Exception] = None
        for server in random.sample(self.tile_servers, len(self.tile_servers)):
            url = BING_TILE_URL_TEMPLATE.format(server=server, quadkey=quadkey)
            req = urllib.request.Request(url, headers={"User-Agent": BING_USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    payload = resp.read()
                img = Image.open(io.BytesIO(payload)).convert("RGB")
                self._tile_cache[quadkey] = img
                return img
            except Exception as exc:
                last_error = exc
                time.sleep(0.2)
                continue
        placeholder = Image.new("RGB", (self.tile_size, self.tile_size), color=(230, 230, 230))
        draw = ImageDraw.Draw(placeholder)
        draw.line((0, 0, self.tile_size, self.tile_size), fill=(180, 180, 180), width=3)
        draw.line((0, self.tile_size, self.tile_size, 0), fill=(180, 180, 180), width=3)
        if last_error:
            sys.stderr.write(f"[bing-map] Warning: tile fetch failed ({last_error})\n")
        self._tile_cache[quadkey] = placeholder
        return placeholder

    def _latlon_to_tile(self, lat: float, lon: float, zoom: int) -> Tuple[float, float]:
        lat = max(min(lat, 85.05112878), -85.05112878)
        lon = ((lon + 180.0) % 360.0) - 180.0
        sin_lat = math.sin(math.radians(lat))
        map_size = 256 << zoom
        pixel_x = ((lon + 180.0) / 360.0) * map_size
        pixel_y = (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)) * map_size
        return pixel_x / 256.0, pixel_y / 256.0

    def _tile_to_quadkey(self, tile_x: int, tile_y: int, level: int) -> str:
        quadkey = []
        for i in range(level, 0, -1):
            digit = 0
            mask = 1 << (i - 1)
            if tile_x & mask:
                digit += 1
            if tile_y & mask:
                digit += 2
            quadkey.append(str(digit))
        return "".join(quadkey)


try:
    _BING_MAP_CLIENT = BingMapImageAPI()
except Exception:
    _BING_MAP_CLIENT = None

def search_place_photo(self, place):
    try:
        if not place:
            return None
        query = urllib.parse.quote_plus(f"{place} địa điểm du lịch")
        url = f"https://www.google.com/search?tbm=isch&ijn=0&q={query}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            page = resp.read().decode('utf-8', errors='ignore')
        url_matches = re.findall(r'\[\"(https://[^\"]+)\",\d+,\d+\]', page)
        def _normalize(raw_url):
            candidate = html_module.unescape(raw_url)
            try:
                candidate = bytes(candidate, 'utf-8').decode('unicode_escape')
            except Exception:
                pass
            return candidate.replace('\\u003d', '=').replace('\\u0026', '&')

        for raw in url_matches:
            candidate = _normalize(raw)
            if candidate.startswith('http') and 'encrypted-tbn' not in candidate:
                return candidate
        for raw in url_matches:
            candidate = _normalize(raw)
            if candidate.startswith('http'):
                return candidate
    except Exception:
        return None
    return None

def download_image_bytes(self, url):
    try:
        if not url:
            return None
        req = urllib.request.Request(url, headers={'User-Agent': 'HUIT-App'})
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.read()
    except Exception:
        return None

def _fetch_place_preview(self, place, date_str=None):
    key = f"{place}||{date_str or ''}"
    try:
        if getattr(self, '_place_preview_cache', None) is not None and key in self._place_preview_cache:
            return self._place_preview_cache[key]
        display_name, lat, lon = self.geocode(place)
        map_bytes = None
        map_url = None
        if _BING_MAP_CLIENT and lat and lon:
            try:
                snapshot = _BING_MAP_CLIENT.create_map_snapshot(
                    place,
                    latitude=float(lat),
                    longitude=float(lon),
                )
                map_bytes = snapshot.to_png_bytes()
                map_url = snapshot.map_url
            except Exception:
                map_bytes = None
        photo_url = None
        if place:
            try:
                photo_url = self.search_place_photo(place)
            except Exception:
                photo_url = None
        photo_bytes = None
        if photo_url:
            photo_bytes = self.download_image_bytes(photo_url)
        weather = None
        if lat and lon:
            try:
                if date_str:
                    weather = self.get_weather_for_date(lat, lon, date_str)
                if not weather:
                    cur, ttime = self.get_weather(lat, lon)
                    if cur is not None:
                        weather = {'current': cur, 'time': ttime}
            except Exception:
                weather = None
        short = None
        if display_name:
            try:
                short = display_name.split(',')[0]
            except Exception:
                short = display_name
        result = {
            'display_name': display_name,
            'short_name': short,
            'lat': lat,
            'lon': lon,
            'map_image_bytes': map_bytes,
            'map_url': map_url,
            'photo_url': photo_url,
            'photo_bytes': photo_bytes,
            'weather': weather
        }
        try:
            if getattr(self, '_place_preview_cache', None) is not None:
                self._place_preview_cache[key] = result
        except Exception:
            pass
        return result
    except Exception as e:
        return {'error': str(e)}

def get_weather_for_date(self, lat, lon, date_str):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min&timezone=auto&start_date={date_str}&end_date={date_str}"
        req = urllib.request.Request(url, headers={'User-Agent': 'HUIT-App'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            daily = data.get('daily', {})
            temps_max = daily.get('temperature_2m_max', [])
            temps_min = daily.get('temperature_2m_min', [])
            if temps_max and temps_min:
                return {'max': temps_max[0], 'min': temps_min[0]}
    except Exception:
        return None
    return None

def geocode(self, place):
    try:
        q = urllib.parse.quote(place)
        url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'HUIT-App'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            if data:
                return data[0].get('display_name'), data[0].get('lat'), data[0].get('lon')
    except Exception:
        return None, None, None

def get_weather(self, lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.load(resp)
            cw = data.get('current_weather', {})
            return cw.get('temperature'), cw.get('time')
    except Exception:
        return None, None

def show_tour_details(self, event=None):
    sel = self.tv_tour.selection()
    if not sel:
        return
    item = sel[0]
    values = self.tv_tour.item(item, 'values')
    ma = values[0]
    t = self.ql.tim_tour(ma)
    if not t:
        messagebox.showerror('Lỗi', 'Không tìm thấy tour')
        return
    booked = sum(d.so_nguoi for d in self.ql.danh_sach_dat_tour if d.ma_tour == t.ma_tour and d.trang_thai == 'da_thanh_toan')
    try:
        total = booked + int(t.so_cho)
    except Exception:
        total = booked + (t.so_cho if isinstance(t.so_cho, int) else booked)
    hdv_name = ''
    if hasattr(self.ql, 'danh_sach_hdv'):
        for h in self.ql.danh_sach_hdv:
            if str(h.get('maHDV')) == str(t.huong_dan_vien):
                hdv_name = h.get('tenHDV','')
                break
    top, container = self.create_modal(f'Chi tiết tour: {t.ten_tour}', size=(980, 620))
    hdr = ttk.Frame(container)
    hdr.pack(fill='x')
    ttk.Label(hdr, text=t.ten_tour, style='Title.TLabel').pack(side='left')
    meta = ttk.Frame(container)
    meta.pack(fill='x', pady=(6,12))
    ttk.Label(meta, text=f"Mã Tour: {t.ma_tour}", style='Body.TLabel').grid(row=0, column=0, sticky='w')
    ttk.Label(meta, text=f"Hướng dẫn viên: {hdv_name}", style='Body.TLabel').grid(row=0, column=1, sticky='w', padx=18)
    ttk.Label(meta, text=f"Chỗ đã đặt: {booked}/{total}", style='Body.TLabel').grid(row=0, column=2, sticky='w', padx=18)
    content = ttk.Frame(container)
    content.pack(fill='both', expand=True)
    left = ttk.Frame(content)
    left.pack(side='left', fill='both', expand=True, padx=(0,10))
    right = ttk.Frame(content, width=320)
    right.pack(side='right', fill='y')

    cols = ("NgayThu", "Ngay", "DiaDiem", "DiaChi", "NhietDo", "PhuongTien")
    tv_it = ttk.Treeview(left, columns=cols, show='headings')
    tv_it.heading('NgayThu', text='Ngày thứ')
    tv_it.heading('Ngay', text='Ngày')
    tv_it.heading('DiaDiem', text='Địa điểm')
    tv_it.heading('DiaChi', text='Địa chỉ')
    tv_it.heading('NhietDo', text='Nhiệt độ')
    tv_it.heading('PhuongTien', text='Phương tiện')
    tv_it.column('NgayThu', width=80, anchor='center')
    tv_it.column('Ngay', width=100, anchor='center')
    tv_it.column('DiaDiem', width=180)
    tv_it.column('DiaChi', width=260)
    tv_it.column('NhietDo', width=120, anchor='center')
    tv_it.column('PhuongTien', width=100, anchor='center')
    scr = ttk.Scrollbar(left, orient=tk.VERTICAL, command=tv_it.yview)
    tv_it.configure(yscrollcommand=scr.set)
    tv_it.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')

    preview = ttk.Frame(right, style='Card.TFrame', padding=10)
    preview.pack(fill='both', expand=True)

    def clear_preview():
        try:
            for w in preview.winfo_children():
                w.destroy()
        except Exception:
            pass

    def apply_preview_to_row(iid, info):
        if not info or (isinstance(info, dict) and info.get('error')):
            return
        try:
            current = list(tv_it.item(iid, 'values'))
            current[3] = info.get('display_name', current[3])
            current[4] = self.format_weather_text(info.get('weather'))
            tv_it.item(iid, values=tuple(current))
        except Exception:
            pass

    def update_preview_for_row(item_id):
        clear_preview()
        if not item_id:
            ttk.Label(preview, text='Chưa chọn lịch trình', style='Body.TLabel').pack()
            return
        vals = tv_it.item(item_id, 'values')
        ngay = vals[1]
        diadiem = vals[2]
        try:
            self._start_loading(preview)
        except Exception:
            pass

        def _on_result(res):
            clear_preview()
            if not res or (isinstance(res, dict) and res.get('error')):
                ttk.Label(preview, text='Không có dữ liệu địa điểm', style='Body.TLabel').pack(anchor='w')
                return
            apply_preview_to_row(item_id, res)
            self.render_place_preview(preview, diadiem, res)

        self._run_async(self._fetch_place_preview, lambda r: _on_result(r), diadiem, ngay)

    i = 1
    for l in t.lich_trinh:
        ngaythu = f"{i}"
        ngay = l.get('ngay','')
        diadiem = l.get('diaDiem', l.get('dia_diem','')) or ''
        phuongtien = l.get('phuongTien', l.get('phuong_tien','')) or ''
        diachi = ''
        nhietdo = '—'
        tv_it.insert('', tk.END, values=(ngaythu, ngay, diadiem, diachi, nhietdo, phuongtien))
        i += 1

    def _on_prefetch(iid, res):
        apply_preview_to_row(iid, res)

    for iid in tv_it.get_children():
        try:
            vals = tv_it.item(iid, 'values')
            place = vals[2]
            datev = vals[1]
            if place:
                self._run_async(self._fetch_place_preview, lambda r, _iid=iid: _on_prefetch(_iid, r), place, datev)
        except Exception:
            pass

    def on_select(e):
        sel = tv_it.selection()
        if not sel:
            return
        try:
            self._start_loading(preview)
        except Exception:
            pass
        update_preview_for_row(sel[0])

    tv_it.bind('<<TreeviewSelect>>', on_select)
    children = tv_it.get_children()
    if children:
        tv_it.selection_set(children[0])
        update_preview_for_row(children[0])

def open_lich_trinh_editor(self, initial=None):
    result = {'data': None}
    top = tk.Toplevel(self.root)
    top.title('Chỉnh sửa Lịch trình')
    try:
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        top.geometry(f"{sw}x{sh}+0+0")
        try:
            top.state('zoomed')
        except Exception:
            pass
    except Exception:
        top.geometry('700x420')
    frm = tk.Frame(top)
    frm.pack(fill='both', expand=True, padx=8, pady=8)
    cols = ('Ngay','DiaDiem','MoTa','PhuongTien')
    tv = ttk.Treeview(frm, columns=cols, show='headings')
    for c in cols:
        tv.heading(c, text=c)
    tv.column('Ngay', width=120)
    tv.column('DiaDiem', width=160)
    tv.column('MoTa', width=240)
    tv.column('PhuongTien', width=120)
    tv.pack(fill='both', expand=True, side='left')
    scr = ttk.Scrollbar(frm, orient=tk.VERTICAL, command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    scr.pack(side='left', fill='y')

    try:
        tv.tag_configure('odd', background='#ffffff')
        tv.tag_configure('even', background='#f7f7f7')
    except Exception:
        pass

    edf = tk.Frame(top)
    edf.pack(fill='x', padx=8, pady=6)
    tk.Label(edf, text='Ngày (YYYY-MM-DD)').grid(row=0, column=0)
    tk.Label(edf, text='Địa điểm').grid(row=1, column=0)
    tk.Label(edf, text='Mô tả').grid(row=2, column=0)
    tk.Label(edf, text='Phương tiện').grid(row=3, column=0)
    e_ngay = tk.Entry(edf)
    e_dd = tk.Entry(edf)
    e_mo = tk.Entry(edf)
    e_pt = tk.Entry(edf)
    e_ngay.grid(row=0, column=1, sticky='we')
    e_dd.grid(row=1, column=1, sticky='we')
    e_mo.grid(row=2, column=1, sticky='we')
    e_pt.grid(row=3, column=1, sticky='we')

    def add_row():
        ng = e_ngay.get().strip()
        dd = e_dd.get().strip()
        mo = e_mo.get().strip()
        pt = e_pt.get().strip()
        if ng:
            try:
                datetime.strptime(ng, '%Y-%m-%d')
            except Exception:
                messagebox.showerror('Lỗi', 'Ngày không hợp lệ (YYYY-MM-DD)')
                return
        tv.insert('', tk.END, values=(ng, dd, mo, pt))
        e_ngay.delete(0, tk.END); e_dd.delete(0, tk.END); e_mo.delete(0, tk.END); e_pt.delete(0, tk.END)

    def edit_row():
        sel = tv.selection()
        if not sel:
            return
        item = sel[0]
        vals = tv.item(item, 'values')
        e_ngay.delete(0, tk.END); e_ngay.insert(0, vals[0])
        e_dd.delete(0, tk.END); e_dd.insert(0, vals[1])
        e_mo.delete(0, tk.END); e_mo.insert(0, vals[2])
        e_pt.delete(0, tk.END); e_pt.insert(0, vals[3])
        tv.delete(item)

    def remove_row():
        sel = tv.selection()
        if not sel:
            return
        for s in sel:
            tv.delete(s)

    btnf = tk.Frame(top)
    btnf.pack(fill='x', padx=8, pady=6)
    tk.Button(btnf, text='Thêm', command=add_row).pack(side='left', padx=6)
    tk.Button(btnf, text='Sửa', command=edit_row).pack(side='left', padx=6)
    tk.Button(btnf, text='Xóa', command=remove_row).pack(side='left', padx=6)

    def on_ok():
        items = []
        for it in tv.get_children():
            v = tv.item(it, 'values')
            items.append({'ngay': v[0], 'diaDiem': v[1], 'moTa': v[2], 'phuongTien': v[3]})
        result['data'] = items
        top.destroy()

    def on_cancel():
        result['data'] = None
        top.destroy()

    bottom = tk.Frame(top)
    bottom.pack(fill='x', padx=8, pady=6)
    tk.Button(bottom, text='OK', command=on_ok).pack(side='left', padx=6)
    tk.Button(bottom, text='Hủy', command=on_cancel).pack(side='left', padx=6)

    if initial:
        for idx, l in enumerate(initial):
            ng = l.get('ngay','')
            dd = l.get('diaDiem', l.get('dia_diem','')) or ''
            mo = l.get('moTa', l.get('mo_ta','')) or ''
            pt = l.get('phuongTien', l.get('phuong_tien','')) or ''
            tag = 'even' if idx % 2 == 0 else 'odd'
            tv.insert('', tk.END, values=(ng, dd, mo, pt), tags=(tag,))

    top.transient(self.root)
    top.grab_set()
    self.root.wait_window(top)
    return result['data']

def build_inline_lich_editor(self, parent, initial=None):
    frame = tk.Frame(parent, bd=1, relief='groove')
    left = tk.Frame(frame)
    left.pack(side='left', fill='both', expand=True)
    cols = ('Ngay','DiaDiem','MoTa','PhuongTien')
    tv = ttk.Treeview(left, columns=cols, show='headings', height=6)
    for c in cols:
        tv.heading(c, text=c)
    tv.column('Ngay', width=100)
    tv.column('DiaDiem', width=160)
    tv.column('MoTa', width=220)
    tv.column('PhuongTien', width=120)
    scr = ttk.Scrollbar(left, orient=tk.VERTICAL, command=tv.yview)
    tv.configure(yscrollcommand=scr.set)
    tv.pack(side='left', fill='both', expand=True)
    scr.pack(side='right', fill='y')

    try:
        tv.tag_configure('odd', background='#ffffff')
        tv.tag_configure('even', background='#f7f7f7')
    except Exception:
        pass

    right = tk.Frame(frame)
    right.pack(side='right', fill='both', expand=True, padx=6, pady=4)
    
    form_section = tk.Frame(right)
    form_section.pack(fill='x', pady=(0,12))
    
    tk.Label(form_section, text='Ngày (DD/MM/YYYY)', font=('Segoe UI', 10)).grid(row=0, column=0, sticky='w', pady=4)
    tk.Label(form_section, text='Địa điểm', font=('Segoe UI', 10)).grid(row=1, column=0, sticky='w', pady=4)
    tk.Label(form_section, text='Mô tả', font=('Segoe UI', 10)).grid(row=2, column=0, sticky='w', pady=4)
    tk.Label(form_section, text='Phương tiện', font=('Segoe UI', 10)).grid(row=3, column=0, sticky='w', pady=4)
    e_ngay = tk.Entry(form_section, font=('Segoe UI', 10))
    e_dd = tk.Entry(form_section, font=('Segoe UI', 10))
    e_mo = tk.Entry(form_section, font=('Segoe UI', 10))
    e_pt = tk.Entry(form_section, font=('Segoe UI', 10))
    e_ngay.grid(row=0, column=1, sticky='we', pady=4, padx=(8,0))
    e_dd.grid(row=1, column=1, sticky='we', pady=4, padx=(8,0))
    e_mo.grid(row=2, column=1, sticky='we', pady=4, padx=(8,0))
    e_pt.grid(row=3, column=1, sticky='we', pady=4, padx=(8,0))
    form_section.columnconfigure(1, weight=1)
    
    def auto_format_date_support(event=None):
        content = e_ngay.get().strip()
        if len(content) == 8 and content.isdigit():
            formatted = f"{content[:2]}/{content[2:4]}/{content[4:]}"
            e_ngay.delete(0, tk.END)
            e_ngay.insert(0, formatted)
            e_ngay.icursor(tk.END)
    e_ngay.bind('<KeyRelease>', auto_format_date_support)
    
    preview_container = tk.LabelFrame(right, text='Xem trước địa điểm', font=('Segoe UI', 10, 'bold'), bd=2, relief='groove')
    preview_container.pack(fill='both', expand=True, pady=(0,8))
    
    preview = tk.Frame(preview_container, bg='#f9f9f9')
    preview.pack(fill='both', expand=True, padx=8, pady=8)

    def clear_preview():
        try:
            for w in preview.winfo_children():
                w.destroy()
        except Exception:
            pass

    def _build_preview_ui(result):
        clear_preview()
        if not result:
            tk.Label(preview, text='Nhập địa điểm để xem thông tin và hình ảnh', font=('Segoe UI', 10), fg='#666', bg='#f9f9f9').pack(expand=True)
            return
        if isinstance(result, Exception) or isinstance(result, dict) and result.get('error'):
            tk.Label(preview, text='Lỗi khi tải dữ liệu địa điểm', font=('Segoe UI', 10), fg='#c44536', bg='#f9f9f9').pack(expand=True)
            return
        display = result.get('display_name')
        short = result.get('short_name')
        lat = result.get('lat')
        lon = result.get('lon')
        img_url = result.get('img_url')
        weather = result.get('weather')
        try:
            self._stop_loading(preview)
        except Exception:
            pass
        
        canvas = tk.Canvas(preview, bg='#f9f9f9', highlightthickness=0)
        scrollbar = tk.Scrollbar(preview, orient='vertical', command=canvas.yview)
        content_frame = tk.Frame(canvas, bg='#f9f9f9')
        
        content_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        if img_url:
            img_frame = tk.Frame(content_frame, bg='#ffffff', bd=1, relief='solid')
            img_frame.pack(fill='x', padx=4, pady=4)
            
            if PIL_AVAILABLE:
                try:
                    data = self.download_image_bytes(img_url)
                    if data is None:
                        raise Exception('Không thể tải ảnh')
                    im = Image.open(io.BytesIO(data))
                    im.thumbnail((480, 360))
                    photo = ImageTk.PhotoImage(im)
                    lbl = tk.Label(img_frame, image=photo, bg='#ffffff')
                    lbl.image = photo
                    lbl.pack(padx=8, pady=8)
                except Exception:
                    lk = tk.Label(img_frame, text='Nhấn để xem ảnh trên trình duyệt', fg='#1b6dc1', cursor='hand2', bg='#ffffff', font=('Segoe UI', 10, 'underline'))
                    lk.pack(padx=8, pady=24)
                    lk.bind('<Button-1>', lambda e, u=img_url: webbrowser.open(u))
            else:
                lk = tk.Label(img_frame, text='Nhấn để xem ảnh trên trình duyệt', fg='#1b6dc1', cursor='hand2', bg='#ffffff', font=('Segoe UI', 10, 'underline'))
                lk.pack(padx=8, pady=24)
                lk.bind('<Button-1>', lambda e, u=img_url: webbrowser.open(u))
        
        info_card = tk.Frame(content_frame, bg='#ffffff', bd=1, relief='solid')
        info_card.pack(fill='x', padx=4, pady=(0,4))
        
        if short:
            title_text = short
        elif display:
            title_text = display
        else:
            title_text = 'Địa điểm'
        tk.Label(info_card, text=title_text, font=('Segoe UI', 12, 'bold'), bg='#ffffff', fg='#1f2933', wraplength=460, justify='left').pack(anchor='w', padx=10, pady=(10,4))
        
        if display and display != short:
            tk.Label(info_card, text=f'{display}', font=('Segoe UI', 9), bg='#ffffff', fg='#52606d', wraplength=460, justify='left').pack(anchor='w', padx=10, pady=(0,4))
        
        if lat and lon:
            coord_frame = tk.Frame(info_card, bg='#ffffff')
            coord_frame.pack(fill='x', padx=10, pady=(4,4))
            tk.Label(coord_frame, text=f'🗺 Tọa độ: {lat}, {lon}', font=('Segoe UI', 9), bg='#ffffff', fg='#52606d').pack(side='left')
            osm_link = tk.Label(coord_frame, text='[Xem bản đồ]', fg='#1b6dc1', cursor='hand2', bg='#ffffff', font=('Segoe UI', 9, 'underline'))
            osm_link.pack(side='left', padx=(8,0))
            osm_link.bind('<Button-1>', lambda e, lat=lat, lon=lon: webbrowser.open(f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=12/{lat}/{lon}"))
        
        temp_text = 'Không có dữ liệu'
        if weather:
            if 'min' in weather and 'max' in weather:
                temp_text = f"{weather.get('min')}°C - {weather.get('max')}°C"
            elif 'current' in weather:
                temp_text = f"{weather.get('current')}°C"
        
        weather_frame = tk.Frame(info_card, bg='#e6f2ff', bd=1, relief='solid')
        weather_frame.pack(fill='x', padx=10, pady=(4,10))
        tk.Label(weather_frame, text=f'🌡 Nhiệt độ: {temp_text}', font=('Segoe UI', 10), bg='#e6f2ff', fg='#1f2933').pack(anchor='w', padx=8, pady=6)

    preview_after = {'id': None}
    def schedule_preview(event=None):
        if preview_after['id']:
            try:
                right.after_cancel(preview_after['id'])
            except Exception:
                pass
        self._start_loading(preview)
        def _kick():
            place = e_dd.get().strip()
            datev = e_ngay.get().strip()
            if not place:
                try:
                    self._stop_loading(preview)
                except Exception:
                    pass
                right.after(10, lambda: _build_preview_ui(None))
                return
            self._run_async(self._fetch_place_preview, lambda res: _build_preview_ui(res), place, datev)
        preview_after['id'] = right.after(450, _kick)

    e_dd.bind('<KeyRelease>', schedule_preview)
    e_ngay.bind('<KeyRelease>', schedule_preview)

    def add_row():
        ng = e_ngay.get().strip()
        dd = e_dd.get().strip()
        mo = e_mo.get().strip()
        pt = e_pt.get().strip()
        if ng:
            try:
                datetime.strptime(ng, '%Y-%m-%d')
            except Exception:
                messagebox.showerror('Lỗi', 'Ngày không hợp lệ (YYYY-MM-DD)')
                return
        tv.insert('', tk.END, values=(ng, dd, mo, pt))
        e_ngay.delete(0, tk.END); e_dd.delete(0, tk.END); e_mo.delete(0, tk.END); e_pt.delete(0, tk.END)
        clear_preview()
        try:
            children = tv.get_children()
            for idx, ch in enumerate(children):
                tag = 'even' if idx % 2 == 0 else 'odd'
                tv.item(ch, tags=(tag,))
        except Exception:
            pass

    def edit_row():
        sel = tv.selection()
        if not sel:
            return
        item = sel[0]
        vals = tv.item(item, 'values')
        e_ngay.delete(0, tk.END); e_ngay.insert(0, vals[0])
        e_dd.delete(0, tk.END); e_dd.insert(0, vals[1])
        e_mo.delete(0, tk.END); e_mo.insert(0, vals[2])
        e_pt.delete(0, tk.END); e_pt.insert(0, vals[3])
        tv.delete(item)
        try:
            children = tv.get_children()
            for idx, ch in enumerate(children):
                tag = 'even' if idx % 2 == 0 else 'odd'
                tv.item(ch, tags=(tag,))
        except Exception:
            pass
        schedule_preview()

    def remove_row():
        sel = tv.selection()
        if not sel:
            return
        for s in sel:
            tv.delete(s)
        clear_preview()
        try:
            children = tv.get_children()
            for idx, ch in enumerate(children):
                tag = 'even' if idx % 2 == 0 else 'odd'
                tv.item(ch, tags=(tag,))
        except Exception:
            pass

    btnf = tk.Frame(right, bg='#ffffff', bd=1, relief='solid')
    btnf.pack(fill='x', pady=(0,0))
    tk.Label(btnf, text='Thao tác:', font=('Segoe UI', 9, 'bold'), bg='#ffffff').pack(side='left', padx=8, pady=8)
    tk.Button(btnf, text='➕ Thêm', command=add_row, bg='#1b6dc1', fg='white', font=('Segoe UI', 9, 'bold'), bd=0, padx=12, pady=6, cursor='hand2').pack(side='left', padx=4)
    tk.Button(btnf, text='✏ Sửa', command=edit_row, bg='#1aa5a5', fg='white', font=('Segoe UI', 9, 'bold'), bd=0, padx=12, pady=6, cursor='hand2').pack(side='left', padx=4)
    tk.Button(btnf, text='🗑 Xóa', command=remove_row, bg='#c44536', fg='white', font=('Segoe UI', 9, 'bold'), bd=0, padx=12, pady=6, cursor='hand2').pack(side='left', padx=4)

    if initial:
        for idx, l in enumerate(initial):
            ng = l.get('ngay','')
            dd = l.get('diaDiem', l.get('dia_diem','')) or ''
            mo = l.get('moTa', l.get('mo_ta','')) or ''
            pt = l.get('phuongTien', l.get('phuong_tien','')) or ''
            tag = 'even' if idx % 2 == 0 else 'odd'
            tv.insert('', tk.END, values=(ng, dd, mo, pt), tags=(tag,))

    def get_items():
        items = []
        for it in tv.get_children():
            v = tv.item(it, 'values')
            items.append({'ngay': v[0], 'diaDiem': v[1], 'moTa': v[2], 'phuongTien': v[3]})
        return items

    return {'frame': frame, 'get_items': get_items}

def on_tour_select(self, event=None):
    sel = self.tv_tour.selection()
    if not sel:
        return
    item = sel[0]
    ma = self.tv_tour.item(item, 'values')[0]
    tour = self.ql.tim_tour(ma)
    if getattr(self, 'tour_context', None) and tour:
        self.tour_context.config(text=f"{tour.ten_tour} • {self.format_money(tour.gia_tour)}")
    role = self.ql.nguoi_dung_hien_tai.vai_tro if self.ql.nguoi_dung_hien_tai else ''
    if role == 'hdv':
        self.update_hdv_right_panel(ma)
    elif role == 'user':
        self.update_user_right_panel(ma)

GiaoDienCoSo.search_place_photo = search_place_photo
GiaoDienCoSo.download_image_bytes = download_image_bytes
GiaoDienCoSo._fetch_place_preview = _fetch_place_preview
GiaoDienCoSo.get_weather_for_date = get_weather_for_date
GiaoDienCoSo.geocode = geocode
GiaoDienCoSo.get_weather = get_weather
GiaoDienCoSo.show_tour_details = show_tour_details
GiaoDienCoSo.open_lich_trinh_editor = open_lich_trinh_editor
GiaoDienCoSo.build_inline_lich_editor = build_inline_lich_editor
GiaoDienCoSo.on_tour_select = on_tour_select
