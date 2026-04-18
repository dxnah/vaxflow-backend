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


