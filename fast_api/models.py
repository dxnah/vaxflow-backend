from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Date, ForeignKey, Numeric
from .database import Base


# ── Vaccine ───────────────────────────────────────────────────────────────────
class Vaccine(Base):
    __tablename__ = "api_vaccine"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(100))
    available      = Column(Integer, default=0)
    status         = Column(String(20), default='in_stock')
    ml_recommended = Column(Integer, default=0)
    min_stock      = Column(Integer, default=0)
    created_at     = Column(DateTime, nullable=True)


# ── VaccineBatch ──────────────────────────────────────────────────────────────
class VaccineBatch(Base):
    __tablename__ = "api_vaccinebatch"

    id             = Column(Integer, primary_key=True, index=True)
    vaccine_id     = Column(Integer, ForeignKey("api_vaccine.id"))
    batch_number   = Column(String(100))
    expiry_date    = Column(Date, nullable=True)
    available      = Column(Integer, default=0)
    used           = Column(Integer, default=0)
    date_purchased = Column(Date, nullable=True)
    supplier       = Column(String(200), nullable=True)
    ml_recommended = Column(Integer, default=0)
    created_at     = Column(DateTime, nullable=True)


# ── Supplier ──────────────────────────────────────────────────────────────────
class Supplier(Base):
    __tablename__ = "api_supplier"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(200))
    contact        = Column(String(200), nullable=True)
    phone          = Column(String(50), nullable=True)
    address        = Column(Text, nullable=True)
    vaccines       = Column(Text, nullable=True)
    status         = Column(String(20), default='Active')
    lead_time_days = Column(Integer, default=0)
    notes          = Column(Text, nullable=True)
    created_at     = Column(DateTime, nullable=True)


# ── Notification ──────────────────────────────────────────────────────────────
class Notification(Base):
    __tablename__ = "api_notification"

    id         = Column(Integer, primary_key=True, index=True)
    title      = Column(String(200))
    message    = Column(Text)
    type       = Column(String(20), default='info')
    read       = Column(Boolean, default=False)
    vaccine_id = Column(Integer, ForeignKey("api_vaccine.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)


# ── Patient ───────────────────────────────────────────────────────────────────
class Patient(Base):
    __tablename__ = "api_patient"

    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(100), unique=True)
    password   = Column(String(100))
    name       = Column(String(200))
    role       = Column(String(20), default='patient')
    email      = Column(String(200), nullable=True)
    phone      = Column(String(20), nullable=True)
    status     = Column(String(20), default='Active')
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)


# ── Admin ─────────────────────────────────────────────────────────────────────
class AdminUser(Base):
    __tablename__ = "auth_user"

    id           = Column(Integer, primary_key=True, index=True)
    username     = Column(String(150), unique=True)
    email        = Column(String(254))
    is_staff     = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    last_login   = Column(DateTime, nullable=True)


# ── VaccineUsageReport ────────────────────────────────────────────────────────
class VaccineUsageReport(Base):
    __tablename__ = "api_vaccineusagereport"

    id           = Column(Integer, primary_key=True, index=True)
    vaccine_id   = Column(Integer, ForeignKey("api_vaccine.id"), nullable=True)
    administered = Column(Integer, default=0)
    wasted       = Column(Integer, default=0)
    remaining    = Column(Integer, default=0)
    period       = Column(String(50), default='monthly')
    report_date  = Column(Date, nullable=True)
    created_at   = Column(DateTime, nullable=True)


# ── StockLevelReport ──────────────────────────────────────────────────────────
class StockLevelReport(Base):
    __tablename__ = "api_stocklevelreport"

    id           = Column(Integer, primary_key=True, index=True)
    date         = Column(Date, nullable=True)
    period_label = Column(String(50), nullable=True)
    in_stock     = Column(Integer, default=0)
    low_stock    = Column(Integer, default=0)
    out_stock    = Column(Integer, default=0)
    created_at   = Column(DateTime, nullable=True)


# ── VaccinationHistory ────────────────────────────────────────────────────────
class VaccinationHistory(Base):
    __tablename__ = "api_vaccinationhistory"

    id              = Column(Integer, primary_key=True, index=True)
    patient_id      = Column(Integer, ForeignKey("api_patient.id"))
    vaccine_id      = Column(Integer, ForeignKey("api_vaccine.id"), nullable=True)
    dose            = Column(String(50))
    date            = Column(Date, nullable=True)
    facility        = Column(String(200))
    administered_by = Column(String(100))


# ── VaccineOrder ──────────────────────────────────────────────────────────────
class VaccineOrder(Base):
    __tablename__ = "api_vaccineorder"

    id              = Column(Integer, primary_key=True, index=True)
    vaccine         = Column(String(100), nullable=True)
    supplier        = Column(String(200), nullable=True)
    amount          = Column(Integer, default=0)
    price_per_piece = Column(Numeric(10, 2), default=0)
    total           = Column(Numeric(12, 2), default=0)
    status          = Column(String(20), default='Pending')
    ordered_at      = Column(DateTime, nullable=True)


# ── Announcement ──────────────────────────────────────────────────────────────
class Announcement(Base):
    __tablename__ = "api_announcement"

    id         = Column(Integer, primary_key=True, index=True)
    title      = Column(String(200))
    message    = Column(Text)
    created_at = Column(DateTime, nullable=True)


# ── DoseSchedule ──────────────────────────────────────────────────────────────
class DoseSchedule(Base):
    __tablename__ = "api_doseschedule"

    id          = Column(Integer, primary_key=True, index=True)
    patient_id  = Column(Integer, ForeignKey("api_patient.id"), nullable=True)
    dose_name   = Column(String(50))
    dose_date   = Column(Date, nullable=True)
    completed   = Column(Boolean, default=False)
    is_optional = Column(Boolean, default=False)


# ── Registration ──────────────────────────────────────────────────────────────
class Registration(Base):
    __tablename__ = "api_registration"

    id                = Column(Integer, primary_key=True, index=True)
    patient_id        = Column(Integer, ForeignKey("api_patient.id"), nullable=True)
    full_name         = Column(String(200))
    age               = Column(String(10))
    birthdate         = Column(Date, nullable=True)
    address           = Column(Text)
    contact           = Column(String(20))
    incident_date     = Column(Date, nullable=True)
    injury_type       = Column(String(50))
    animal_type       = Column(String(50))
    animal_owner      = Column(String(100))
    animal_vaccinated = Column(String(20))
    body_part         = Column(Text)
    queue_number      = Column(String(10), nullable=True)
    created_at        = Column(DateTime, nullable=True)