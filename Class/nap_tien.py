from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class YeuCauNapTien:
    TRANG_THAI_CHO = "pending"
    TRANG_THAI_XAC_NHAN = "confirmed"
    TRANG_THAI_HET_HAN = "expired"
    TRANG_THAI_HUY = "canceled"

    def __init__(
        self,
        ma_giao_dich: str,
        ma_khach_hang: str,
        so_tien: float,
        trang_thai: str = TRANG_THAI_CHO,
        token: Optional[str] = None,
        noi_dung_qr: Optional[str] = None,
        file_qr: Optional[str] = None,
        du_lieu_qr: Optional[str] = None,
        thoi_gian_tao: Optional[str] = None,
        thoi_gian_cap_nhat: Optional[str] = None,
        thoi_gian_het_han: Optional[str] = None,
        du_lieu_phu: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = datetime.utcnow().replace(microsecond=0).isoformat()
        self.ma_giao_dich = ma_giao_dich
        self.ma_khach_hang = ma_khach_hang
        self.so_tien = float(so_tien)
        self.trang_thai = trang_thai
        self.token = token
        self.noi_dung_qr = noi_dung_qr
        self.file_qr = file_qr
        self.du_lieu_qr = du_lieu_qr
        self.thoi_gian_tao = thoi_gian_tao or now
        self.thoi_gian_cap_nhat = thoi_gian_cap_nhat or now
        self.thoi_gian_het_han = thoi_gian_het_han
        self.du_lieu_phu = du_lieu_phu or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ma_giao_dich": self.ma_giao_dich,
            "ma_khach_hang": self.ma_khach_hang,
            "so_tien": self.so_tien,
            "trang_thai": self.trang_thai,
            "token": self.token,
            "noi_dung_qr": self.noi_dung_qr,
            "file_qr": self.file_qr,
            "du_lieu_qr": self.du_lieu_qr,
            "thoi_gian_tao": self.thoi_gian_tao,
            "thoi_gian_cap_nhat": self.thoi_gian_cap_nhat,
            "thoi_gian_het_han": self.thoi_gian_het_han,
            "du_lieu_phu": self.du_lieu_phu,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "YeuCauNapTien":
        return cls(
            ma_giao_dich=data.get("ma_giao_dich", ""),
            ma_khach_hang=data.get("ma_khach_hang", ""),
            so_tien=data.get("so_tien", 0),
            trang_thai=data.get("trang_thai", cls.TRANG_THAI_CHO),
            token=data.get("token"),
            noi_dung_qr=data.get("noi_dung_qr"),
            file_qr=data.get("file_qr"),
            du_lieu_qr=data.get("du_lieu_qr"),
            thoi_gian_tao=data.get("thoi_gian_tao"),
            thoi_gian_cap_nhat=data.get("thoi_gian_cap_nhat"),
            thoi_gian_het_han=data.get("thoi_gian_het_han"),
            du_lieu_phu=data.get("du_lieu_phu"),
        )

    def danh_dau_xac_nhan(self) -> None:
        self.trang_thai = self.TRANG_THAI_XAC_NHAN
        self.thoi_gian_cap_nhat = datetime.utcnow().replace(microsecond=0).isoformat()

    def danh_dau_het_han(self) -> None:
        self.trang_thai = self.TRANG_THAI_HET_HAN
        self.thoi_gian_cap_nhat = datetime.utcnow().replace(microsecond=0).isoformat()

    def da_het_han(self) -> bool:
        if not self.thoi_gian_het_han:
            return False
        try:
            expire_at = datetime.fromisoformat(self.thoi_gian_het_han)
        except Exception:
            return False
        return datetime.utcnow() > expire_at

    def extend_expiration(self, minutes: int) -> None:
        expire_at = datetime.utcnow() + timedelta(minutes=minutes)
        self.thoi_gian_het_han = expire_at.replace(microsecond=0).isoformat()
        self.thoi_gian_cap_nhat = self.thoi_gian_het_han
