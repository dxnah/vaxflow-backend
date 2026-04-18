from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Suppliers ─────────────────────────────────────────────────────────────────
@app.get("/api/suppliers/", response_model=list[schemas.SupplierOut])
def get_suppliers(db: Session = Depends(get_db)):
    return db.query(models.Supplier).all()

@app.post("/api/suppliers/", response_model=schemas.SupplierOut)
def create_supplier(supplier: schemas.SupplierCreate, db: Session = Depends(get_db)):
    new_supplier = models.Supplier(**supplier.model_dump())
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    return new_supplier

@app.put("/api/suppliers/{supplier_id}/", response_model=schemas.SupplierOut)
def update_supplier(supplier_id: int, supplier: schemas.SupplierCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Supplier not found")
    for key, value in supplier.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.delete("/api/suppliers/{supplier_id}/")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    db.delete(supplier)
    db.commit()
    return {"message": "Supplier deleted"}


# ── Notifications ─────────────────────────────────────────────────────────────
@app.get("/api/notifications/", response_model=list[schemas.NotificationOut])
def get_notifications(db: Session = Depends(get_db)):
    return db.query(models.Notification).all()

@app.post("/api/notifications/", response_model=schemas.NotificationOut)
def create_notification(notif: schemas.NotificationCreate, db: Session = Depends(get_db)):
    new_notif = models.Notification(**notif.model_dump())
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)
    return new_notif

@app.put("/api/notifications/{notif_id}/", response_model=schemas.NotificationOut)
def update_notification(notif_id: int, notif: schemas.NotificationCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Notification).filter(models.Notification.id == notif_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Notification not found")
    for key, value in notif.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.post("/api/notifications/mark_all_read/")
def mark_all_read(db: Session = Depends(get_db)):
    db.query(models.Notification).filter(models.Notification.read == False).update({"read": True})
    db.commit()
    return {"status": "ok"}

@app.delete("/api/notifications/clear_all/")
def clear_all_notifications(db: Session = Depends(get_db)):
    db.query(models.Notification).delete()
    db.commit()
    return {"message": "All notifications cleared"}

@app.delete("/api/notifications/{notif_id}/")
def delete_notification(notif_id: int, db: Session = Depends(get_db)):
    notif = db.query(models.Notification).filter(models.Notification.id == notif_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(notif)
    db.commit()
    return {"message": "Notification deleted"}


# ── Patients ──────────────────────────────────────────────────────────────────
@app.get("/api/patients/", response_model=list[schemas.PatientOut])
def get_patients(db: Session = Depends(get_db)):
    return db.query(models.Patient).all()

@app.get("/api/patients/{patient_id}/", response_model=schemas.PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.put("/api/patients/{patient_id}/", response_model=schemas.PatientOut)
def update_patient(patient_id: int, patient: schemas.PatientOut, db: Session = Depends(get_db)):
    existing = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Patient not found")
    for key, value in patient.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.delete("/api/patients/{patient_id}/")
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"message": "Patient deleted"}


# ── Admins ────────────────────────────────────────────────────────────────────
@app.get("/api/admins/", response_model=list[schemas.AdminOut])
def get_admins(db: Session = Depends(get_db)):
    return db.query(models.AdminUser).filter(models.AdminUser.is_staff == True).all()


# ── VaccineBatches ────────────────────────────────────────────────────────────
@app.get("/api/batches/", response_model=list[schemas.VaccineBatchOut])
def get_batches(db: Session = Depends(get_db)):
    return db.query(models.VaccineBatch).all()

@app.post("/api/batches/", response_model=schemas.VaccineBatchOut)
def create_batch(batch: schemas.VaccineBatchCreate, db: Session = Depends(get_db)):
    new_batch = models.VaccineBatch(**batch.model_dump())
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    return new_batch

@app.put("/api/batches/{batch_id}/", response_model=schemas.VaccineBatchOut)
def update_batch(batch_id: int, batch: schemas.VaccineBatchCreate, db: Session = Depends(get_db)):
    existing = db.query(models.VaccineBatch).filter(models.VaccineBatch.id == batch_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Batch not found")
    for key, value in batch.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.delete("/api/batches/{batch_id}/")
def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(models.VaccineBatch).filter(models.VaccineBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    db.delete(batch)
    db.commit()
    return {"message": "Batch deleted"}


# ── VaccineUsageReports ───────────────────────────────────────────────────────
@app.get("/api/usage-reports/", response_model=list[schemas.VaccineUsageReportOut])
def get_usage_reports(db: Session = Depends(get_db)):
    return db.query(models.VaccineUsageReport).all()

@app.post("/api/usage-reports/", response_model=schemas.VaccineUsageReportOut)
def create_usage_report(report: schemas.VaccineUsageReportCreate, db: Session = Depends(get_db)):
    new_report = models.VaccineUsageReport(**report.model_dump())
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

@app.put("/api/usage-reports/{report_id}/", response_model=schemas.VaccineUsageReportOut)
def update_usage_report(report_id: int, report: schemas.VaccineUsageReportCreate, db: Session = Depends(get_db)):
    existing = db.query(models.VaccineUsageReport).filter(models.VaccineUsageReport.id == report_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Usage report not found")
    for key, value in report.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.delete("/api/usage-reports/{report_id}/")
def delete_usage_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(models.VaccineUsageReport).filter(models.VaccineUsageReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Usage report not found")
    db.delete(report)
    db.commit()
    return {"message": "Usage report deleted"}


# ── StockLevelReports ─────────────────────────────────────────────────────────
@app.get("/api/stock-reports/", response_model=list[schemas.StockLevelReportOut])
def get_stock_reports(db: Session = Depends(get_db)):
    return db.query(models.StockLevelReport).all()

@app.post("/api/stock-reports/", response_model=schemas.StockLevelReportOut)
def create_stock_report(report: schemas.StockLevelReportCreate, db: Session = Depends(get_db)):
    new_report = models.StockLevelReport(**report.model_dump())
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

@app.put("/api/stock-reports/{report_id}/", response_model=schemas.StockLevelReportOut)
def update_stock_report(report_id: int, report: schemas.StockLevelReportCreate, db: Session = Depends(get_db)):
    existing = db.query(models.StockLevelReport).filter(models.StockLevelReport.id == report_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Stock report not found")
    for key, value in report.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.delete("/api/stock-reports/{report_id}/")
def delete_stock_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(models.StockLevelReport).filter(models.StockLevelReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Stock report not found")
    db.delete(report)
    db.commit()
    return {"message": "Stock report deleted"}


# ── VaccinationHistory ────────────────────────────────────────────────────────
@app.get("/api/vaccination-history/", response_model=list[schemas.VaccinationHistoryOut])
def get_vaccination_history(db: Session = Depends(get_db)):
    return db.query(models.VaccinationHistory).all()

@app.post("/api/vaccination-history/", response_model=schemas.VaccinationHistoryOut)
def create_vaccination_history(record: schemas.VaccinationHistoryCreate, db: Session = Depends(get_db)):
    new_record = models.VaccinationHistory(**record.model_dump())
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

@app.put("/api/vaccination-history/{record_id}/", response_model=schemas.VaccinationHistoryOut)
def update_vaccination_history(record_id: int, record: schemas.VaccinationHistoryCreate, db: Session = Depends(get_db)):
    existing = db.query(models.VaccinationHistory).filter(models.VaccinationHistory.id == record_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Vaccination record not found")
    for key, value in record.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.delete("/api/vaccination-history/{record_id}/")
def delete_vaccination_history(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.VaccinationHistory).filter(models.VaccinationHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Vaccination record not found")
    db.delete(record)
    db.commit()
    return {"message": "Vaccination record deleted"}


# ── VaccineOrders ─────────────────────────────────────────────────────────────
@app.get("/api/orders/", response_model=list[schemas.VaccineOrderOut])
def get_orders(db: Session = Depends(get_db)):
    return db.query(models.VaccineOrder).all()

@app.post("/api/orders/", response_model=schemas.VaccineOrderOut)
def create_order(order: schemas.VaccineOrderCreate, db: Session = Depends(get_db)):
    new_order = models.VaccineOrder(**order.model_dump())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

@app.put("/api/orders/{order_id}/", response_model=schemas.VaccineOrderOut)
def update_order(order_id: int, order: schemas.VaccineOrderCreate, db: Session = Depends(get_db)):
    existing = db.query(models.VaccineOrder).filter(models.VaccineOrder.id == order_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")
    for key, value in order.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.delete("/api/orders/{order_id}/")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.VaccineOrder).filter(models.VaccineOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
    return {"message": "Order deleted"}

# ── Announcements ─────────────────────────────────────────────────────────────
@app.get("/api/announcements/", response_model=list[schemas.AnnouncementOut])
def get_announcements(db: Session = Depends(get_db)):
    return db.query(models.Announcement).all()

@app.post("/api/announcements/", response_model=schemas.AnnouncementOut)
def create_announcement(announcement: schemas.AnnouncementCreate, db: Session = Depends(get_db)):
    new_announcement = models.Announcement(**announcement.model_dump())
    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)
    return new_announcement

@app.put("/api/announcements/{announcement_id}/", response_model=schemas.AnnouncementOut)
def update_announcement(announcement_id: int, announcement: schemas.AnnouncementCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Announcement).filter(models.Announcement.id == announcement_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")
    for key, value in announcement.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.delete("/api/announcements/{announcement_id}/")
def delete_announcement(announcement_id: int, db: Session = Depends(get_db)):
    announcement = db.query(models.Announcement).filter(models.Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    db.delete(announcement)
    db.commit()
    return {"message": "Announcement deleted"}


# ── DoseSchedules ─────────────────────────────────────────────────────────────
@app.get("/api/dose-schedules/", response_model=list[schemas.DoseScheduleOut])
def get_dose_schedules(db: Session = Depends(get_db)):
    return db.query(models.DoseSchedule).all()

@app.post("/api/dose-schedules/", response_model=schemas.DoseScheduleOut)
def create_dose_schedule(schedule: schemas.DoseScheduleCreate, db: Session = Depends(get_db)):
    new_schedule = models.DoseSchedule(**schedule.model_dump())
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    return new_schedule

@app.put("/api/dose-schedules/{schedule_id}/", response_model=schemas.DoseScheduleOut)
def update_dose_schedule(schedule_id: int, schedule: schemas.DoseScheduleCreate, db: Session = Depends(get_db)):
    existing = db.query(models.DoseSchedule).filter(models.DoseSchedule.id == schedule_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Dose schedule not found")
    for key, value in schedule.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.delete("/api/dose-schedules/{schedule_id}/")
def delete_dose_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(models.DoseSchedule).filter(models.DoseSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Dose schedule not found")
    db.delete(schedule)
    db.commit()
    return {"message": "Dose schedule deleted"}


# ── Registrations ─────────────────────────────────────────────────────────────
@app.get("/api/registrations/", response_model=list[schemas.RegistrationOut])
def get_registrations(db: Session = Depends(get_db)):
    return db.query(models.Registration).all()

@app.post("/api/registrations/", response_model=schemas.RegistrationOut)
def create_registration(registration: schemas.RegistrationCreate, db: Session = Depends(get_db)):
    new_registration = models.Registration(**registration.model_dump())
    db.add(new_registration)
    db.commit()
    db.refresh(new_registration)
    return new_registration

@app.put("/api/registrations/{registration_id}/", response_model=schemas.RegistrationOut)
def update_registration(registration_id: int, registration: schemas.RegistrationCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Registration).filter(models.Registration.id == registration_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Registration not found")
    for key, value in registration.model_dump().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.delete("/api/registrations/{registration_id}/")
def delete_registration(registration_id: int, db: Session = Depends(get_db)):
    registration = db.query(models.Registration).filter(models.Registration.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    db.delete(registration)
    db.commit()
    return {"message": "Registration deleted"}