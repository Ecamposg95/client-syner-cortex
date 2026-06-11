import importlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from app.dependencies import get_current_org_id
from app.models.kpi import KPI
from app.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class KPIBase(BaseModel):
    name: str
    value: float

class KPICreate(KPIBase):
    pass

class KPIResponse(KPIBase):
    id: int
    organization_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

@router.get("/kpi", response_model=List[KPIResponse], tags=["kpi"])
def list_kpis(organization_id: int = Depends(get_current_org_id), db: SessionLocal = Depends(get_db)):
    return db.query(KPI).filter(KPI.organization_id == organization_id).all()

@router.post("/kpi", response_model=KPIResponse, tags=["kpi"])
def create_kpi(kpi: KPICreate, organization_id: int = Depends(get_current_org_id), db: SessionLocal = Depends(get_db)):
    db_kpi = KPI(**kpi.dict(), organization_id=organization_id)
    db.add(db_kpi)
    db.commit()
    db.refresh(db_kpi)
    return db_kpi

@router.put("/kpi/{kpi_id}", response_model=KPIResponse, tags=["kpi"])
def update_kpi(kpi_id: int, kpi: KPICreate, organization_id: int = Depends(get_current_org_id), db: SessionLocal = Depends(get_db)):
    db_kpi = db.query(KPI).filter(KPI.id == kpi_id, KPI.organization_id == organization_id).first()
    if not db_kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    for field, value in kpi.dict().items():
        setattr(db_kpi, field, value)
    db.commit()
    db.refresh(db_kpi)
    return db_kpi

@router.delete("/kpi/{kpi_id}", tags=["kpi"])
def delete_kpi(kpi_id: int, organization_id: int = Depends(get_current_org_id), db: SessionLocal = Depends(get_db)):
    db_kpi = db.query(KPI).filter(KPI.id == kpi_id, KPI.organization_id == organization_id).first()
    if not db_kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    db.delete(db_kpi)
    db.commit()
    return {"detail": "KPI deleted"}
