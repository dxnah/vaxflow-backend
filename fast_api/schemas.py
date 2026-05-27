from pydantic import BaseModel, Field
from datetime import datetime, date as date_type
from typing import Optional, List
from decimal import Decimal


# ── Auth ──────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str


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


# ── Patient ───────────────────────────────────────────────────────────────────
class PatientOut(BaseModel):
    id:         int
    username:   str
    name:       str
    role:       str
    email:      Optional[str] = None
    phone:      Optional[str] = None
    status:     str
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PatientCreate(BaseModel):
    username: str
    password: str
    name:     str
    role:     str = 'patient'
    email:    Optional[str] = None
    phone:    Optional[str] = None
    status:   str = 'Active'

# For Settings screen — partial update only (no role/status overwrite)
class PatientUpdate(BaseModel):
    name:     Optional[str] = None
    email:    Optional[str] = None
    phone:    Optional[str] = None
    password: Optional[str] = None

    class Config:
        from_attributes = True


# ── Vaccine ───────────────────────────────────────────────────────────────────
class VaccineOut(BaseModel):
    id:             int
    name:           str
    available:      int
    status:         str
    ml_recommended: int
    min_stock:      int
    created_at:     Optional[datetime] = None

    class Config:
        from_attributes = True

class VaccineCreate(BaseModel):
    name:           str
    available:      int = 0
    status:         str = 'in_stock'
    ml_recommended: int = 0
    min_stock:      int = 0


# ── VaccineBatch ──────────────────────────────────────────────────────────────
class VaccineBatchOut(BaseModel):
    id:             int
    vaccine_id:     int
    batch_number:   str
    expiry_date:    Optional[date_type] = None
    available:      int
    used:           int
    date_purchased: Optional[date_type] = None
    supplier:       Optional[str] = None
    ml_recommended: int
    created_at:     Optional[datetime] = None

    class Config:
        from_attributes = True

class VaccineBatchCreate(BaseModel):
    vaccine_id:     int
    batch_number:   str
    expiry_date:    Optional[date_type] = None
    available:      int = 0
    used:           int = 0
    date_purchased: Optional[date_type] = None
    supplier:       Optional[str] = None
    ml_recommended: int = 0


# ── VaccineUsageReport ────────────────────────────────────────────────────────
class VaccineUsageReportOut(BaseModel):
    id:           int
    vaccine_id:   Optional[int] = None
    administered: int
    wasted:       int
    remaining:    int
    period:       str
    report_date:  Optional[date_type] = None
    created_at:   Optional[datetime] = None

    class Config:
        from_attributes = True

class VaccineUsageReportCreate(BaseModel):
    vaccine_id:   Optional[int] = None
    administered: int = 0
    wasted:       int = 0
    remaining:    int = 0
    period:       str = 'monthly'
    report_date:  Optional[date_type] = None


# ── StockLevelReport ──────────────────────────────────────────────────────────
class StockLevelReportOut(BaseModel):
    id:           int
    date:         Optional[date_type] = None
    period_label: Optional[str] = None
    in_stock:     int
    low_stock:    int
    out_stock:    int
    created_at:   Optional[datetime] = None

    class Config:
        from_attributes = True

class StockLevelReportCreate(BaseModel):
    date:         Optional[date_type] = None
    period_label: Optional[str] = None
    in_stock:     int = 0
    low_stock:    int = 0
    out_stock:    int = 0


# ── VaccinationHistory ────────────────────────────────────────────────────────
class VaccinationHistoryOut(BaseModel):
    id:              int
    patient_id:      int
    vaccine_id:      Optional[int] = None
    dose:            str
    date:            Optional[date_type] = None
    facility:        str
    administered_by: str

    class Config:
        from_attributes = True

class VaccinationHistoryCreate(BaseModel):
    patient_id:      int
    vaccine_id:      Optional[int] = None
    dose:            str
    date:            Optional[date_type] = None
    facility:        str
    administered_by: str


# ── VaccineOrder ──────────────────────────────────────────────────────────────
class VaccineOrderOut(BaseModel):
    id:              int
    vaccine:         Optional[str] = None
    supplier:        Optional[str] = None
    amount:          int
    price_per_piece: Decimal
    total:           Decimal
    status:          str
    ordered_at:      Optional[datetime] = None

    class Config:
        from_attributes = True

class VaccineOrderCreate(BaseModel):
    vaccine:         Optional[str] = None
    supplier:        Optional[str] = None
    amount:          int = 0
    price_per_piece: Decimal = Decimal('0')
    total:           Decimal = Decimal('0')
    status:          str = 'Pending'


# ── Announcement ──────────────────────────────────────────────────────────────
class AnnouncementOut(BaseModel):
    id:         int
    title:      Optional[str] = None
    message:    Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AnnouncementCreate(BaseModel):
    title:   Optional[str] = None
    message: Optional[str] = None


# ── DoseSchedule ──────────────────────────────────────────────────────────────
class DoseScheduleOut(BaseModel):
    id:          int
    patient_id:  Optional[int] = None
    dose_name:   str
    dose_date:   Optional[date_type] = None
    completed:   bool
    is_optional: bool

    class Config:
        from_attributes = True

class DoseScheduleCreate(BaseModel):
    patient_id:  Optional[int] = None
    dose_name:   str
    dose_date:   Optional[date_type] = None
    completed:   bool = False
    is_optional: bool = False


# ── Registration ──────────────────────────────────────────────────────────────
class RegistrationOut(BaseModel):
    id:                int
    patient_id:        Optional[int] = None
    full_name:         Optional[str] = None
    age:               Optional[str] = None
    birthdate:         Optional[date_type] = None
    address:           Optional[str] = None
    contact:           Optional[str] = None
    incident_date:     Optional[date_type] = None
    injury_type:       Optional[str] = None
    animal_type:       Optional[str] = None
    animal_owner:      Optional[str] = None
    animal_vaccinated: Optional[str] = None
    body_part:         Optional[str] = None
    queue_number:      Optional[str] = None
    created_at:        Optional[datetime] = None

    class Config:
        from_attributes = True

class RegistrationCreate(BaseModel):
    patient_id:        Optional[int] = None
    full_name:         Optional[str] = None
    age:               Optional[str] = None
    birthdate:         Optional[date_type] = None
    address:           Optional[str] = None
    contact:           Optional[str] = None
    incident_date:     Optional[date_type] = None
    injury_type:       Optional[str] = None
    animal_type:       Optional[str] = None
    animal_owner:      Optional[str] = None
    animal_vaccinated: Optional[str] = None
    body_part:         Optional[str] = None
    queue_number:      Optional[str] = None