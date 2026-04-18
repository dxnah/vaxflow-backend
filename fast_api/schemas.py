from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ── Supplier ──────────────────────────────────────────────────────────────────
class SupplierOut(BaseModel):
    id:             int
    name:           str
    contact:        Optional[str] = None
    phone:          Optional[str] = None
    address:        Optional[str] = None
    vaccines:       Optional[str] = None
    status:         str
    lead_time_days: int
    notes:          Optional[str] = None
    created_at:     Optional[datetime] = None

    class Config:
        from_attributes = True

class SupplierCreate(BaseModel):
    name:           str
    contact:        Optional[str] = None
    phone:          Optional[str] = None
    address:        Optional[str] = None
    vaccines:       Optional[str] = None
    status:         str = 'Active'
    lead_time_days: int = 0
    notes:          Optional[str] = None


# ── Notification ──────────────────────────────────────────────────────────────
class NotificationOut(BaseModel):
    id:         int
    title:      str
    message:    str
    type:       str
    read:       bool
    vaccine_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationCreate(BaseModel):
    title:      str
    message:    str
    type:       str = 'info'
    vaccine_id: Optional[int] = None


