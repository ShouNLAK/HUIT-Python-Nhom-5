from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class NapTienRequest:
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELED = "canceled"

    def __init__(
        self,
        maGD: str,
        maKH: str,
        soTien: float,
        trangThai: str = STATUS_PENDING,
        token: Optional[str] = None,
        qrContent: Optional[str] = None,
        qrFile: Optional[str] = None,
        qrDataUri: Optional[str] = None,
        createdAt: Optional[str] = None,
        updatedAt: Optional[str] = None,
        expiresAt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = datetime.utcnow().replace(microsecond=0).isoformat()
        self.maGD = maGD
        self.maKH = maKH
        self.soTien = float(soTien)
        self.trangThai = trangThai
        self.token = token
        self.qrContent = qrContent
        self.qrFile = qrFile
        self.qrDataUri = qrDataUri
        self.createdAt = createdAt or now
        self.updatedAt = updatedAt or now
        self.expiresAt = expiresAt
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "maGD": self.maGD,
            "maKH": self.maKH,
            "soTien": self.soTien,
            "trangThai": self.trangThai,
            "token": self.token,
            "qrContent": self.qrContent,
            "qrFile": self.qrFile,
            "qrDataUri": self.qrDataUri,
            "createdAt": self.createdAt,
            "updatedAt": self.updatedAt,
            "expiresAt": self.expiresAt,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NapTienRequest":
        return cls(
            maGD=data.get("maGD", ""),
            maKH=data.get("maKH", ""),
            soTien=data.get("soTien", 0),
            trangThai=data.get("trangThai", cls.STATUS_PENDING),
            token=data.get("token"),
            qrContent=data.get("qrContent"),
            qrFile=data.get("qrFile"),
            qrDataUri=data.get("qrDataUri"),
            createdAt=data.get("createdAt"),
            updatedAt=data.get("updatedAt"),
            expiresAt=data.get("expiresAt"),
            metadata=data.get("metadata"),
        )

    def mark_confirmed(self) -> None:
        self.trangThai = self.STATUS_CONFIRMED
        self.updatedAt = datetime.utcnow().replace(microsecond=0).isoformat()

    def mark_expired(self) -> None:
        self.trangThai = self.STATUS_EXPIRED
        self.updatedAt = datetime.utcnow().replace(microsecond=0).isoformat()

    def is_expired(self) -> bool:
        if not self.expiresAt:
            return False
        try:
            expire_at = datetime.fromisoformat(self.expiresAt)
        except Exception:
            return False
        return datetime.utcnow() > expire_at

    def extend_expiration(self, minutes: int) -> None:
        expire_at = datetime.utcnow() + timedelta(minutes=minutes)
        self.expiresAt = expire_at.replace(microsecond=0).isoformat()
        self.updatedAt = self.expiresAt
