from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from .database import Base

# ── Vaccine (needed for FK reference) ────────────────────────────────────────
class Vaccine(Base):
    __tablename__ = "api_vaccine"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(100))
    available      = Column(Integer, default=0)
    status         = Column(String(20), default='in_stock')
    ml_recommended = Column(Integer, default=0)
    min_stock      = Column(Integer, default=0)
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
    vaccine_id = Column(Integer, ForeignKey("vaccines_vaccine.id"), nullable=True)
    created_at = Column(DateTime, nullable=True)

