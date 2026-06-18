from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import datetime

from app.database import get_db
from app.dependencies import get_current_org_id, RoleChecker
from app.models.models import OrganizationUser
from app.models.raci import RaciMatrix, RaciRole, RaciProcess, RaciAssignment, RaciValue

router = APIRouter()

# Crew/management plus the client's own leadership may edit a matrix; any member
# of the org can read it.
_EDIT_ROLES = [
    "SYNER_PARTNER", "SYNER_CONSULTANT",
    "CLIENT_OWNER", "CLIENT_EXECUTIVE", "CLIENT_MANAGER",
]


# --- Pydantic Schemas ---

class RoleIn(BaseModel):
    name: str
    order: int | None = None
    charter_decides: str | None = None
    charter_blocks: str | None = None
    charter_escalates: str | None = None


class RoleOut(BaseModel):
    id: int
    name: str
    order: int
    charter_decides: str | None
    charter_blocks: str | None
    charter_escalates: str | None


class ProcessIn(BaseModel):
    name: str
    order: int | None = None
    evidence_min: str | None = None
    handoff_owner: str | None = None


class ProcessOut(BaseModel):
    id: int
    name: str
    order: int
    evidence_min: str | None
    handoff_owner: str | None


class MatrixCreate(BaseModel):
    name: str
    description: str | None = None
    version: str = "1.0"


class CellSet(BaseModel):
    process_id: int
    role_id: int
    value: str          # R | A | C | I
    present: bool = True  # True = ensure the value exists, False = remove it


class ProcessValidation(BaseModel):
    process_id: int
    accountable_count: int
    responsible_count: int
    # Golden rule: exactly one Accountable per process.
    golden_rule_ok: bool
    missing_responsible: bool
    issues: List[str]


class MatrixSummary(BaseModel):
    id: int
    name: str
    description: str | None
    version: str
    role_count: int
    process_count: int
    violations: int
    created_at: datetime.datetime


class MatrixDetail(BaseModel):
    id: int
    name: str
    description: str | None
    version: str
    roles: List[RoleOut]
    processes: List[ProcessOut]
    # cells keyed "<process_id>:<role_id>" -> list of values e.g. ["R","A"]
    cells: dict
    validation: List[ProcessValidation]
    valid: bool


# --- Helpers ---

def _parse_value(value: str) -> RaciValue:
    try:
        return RaciValue(value.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="value must be one of R, A, C, I")


def _role_out(r: RaciRole) -> dict:
    return {
        "id": r.id, "name": r.name, "order": r.order,
        "charter_decides": r.charter_decides,
        "charter_blocks": r.charter_blocks,
        "charter_escalates": r.charter_escalates,
    }


def _process_out(p: RaciProcess) -> dict:
    return {
        "id": p.id, "name": p.name, "order": p.order,
        "evidence_min": p.evidence_min, "handoff_owner": p.handoff_owner,
    }


def _validate(matrix: RaciMatrix) -> tuple[list, bool]:
    """Per-process RACI health: exactly one Accountable, at least one Responsible."""
    by_process: dict[int, list[RaciAssignment]] = {p.id: [] for p in matrix.processes}
    for a in matrix.assignments:
        by_process.setdefault(a.process_id, []).append(a)

    name_of = {p.id: p.name for p in matrix.processes}
    report = []
    all_ok = True
    for pid, assigns in by_process.items():
        a_count = sum(1 for x in assigns if x.value == RaciValue.A)
        r_count = sum(1 for x in assigns if x.value == RaciValue.R)
        golden = a_count == 1
        missing_r = r_count == 0
        issues = []
        if a_count == 0:
            issues.append(f"'{name_of.get(pid, pid)}' no tiene Accountable (A).")
        elif a_count > 1:
            issues.append(f"'{name_of.get(pid, pid)}' tiene {a_count} Accountables — debe haber solo uno.")
        if missing_r:
            issues.append(f"'{name_of.get(pid, pid)}' no tiene Responsible (R).")
        if issues:
            all_ok = False
        report.append({
            "process_id": pid,
            "accountable_count": a_count,
            "responsible_count": r_count,
            "golden_rule_ok": golden,
            "missing_responsible": missing_r,
            "issues": issues,
        })
    return report, all_ok


def _get_owned_matrix(db: Session, matrix_id: int, org_id: int) -> RaciMatrix:
    matrix = db.query(RaciMatrix).filter(
        RaciMatrix.id == matrix_id, RaciMatrix.organization_id == org_id,
    ).first()
    if not matrix:
        raise HTTPException(status_code=404, detail="RACI matrix not found")
    return matrix


def _detail(matrix: RaciMatrix) -> dict:
    cells: dict[str, list[str]] = {}
    for a in matrix.assignments:
        cells.setdefault(f"{a.process_id}:{a.role_id}", []).append(a.value.value)
    # Keep cell values in canonical R,A,C,I order for stable rendering.
    order = {"R": 0, "A": 1, "C": 2, "I": 3}
    for key in cells:
        cells[key].sort(key=lambda v: order.get(v, 9))
    report, valid = _validate(matrix)
    return {
        "id": matrix.id,
        "name": matrix.name,
        "description": matrix.description,
        "version": matrix.version,
        "roles": [_role_out(r) for r in matrix.roles],
        "processes": [_process_out(p) for p in matrix.processes],
        "cells": cells,
        "validation": report,
        "valid": valid,
    }


# --- Endpoints ---

@router.get("/raci/matrices", response_model=List[MatrixSummary], tags=["raci"])
def list_matrices(
    org_id: int = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    matrices = (
        db.query(RaciMatrix)
        .filter(RaciMatrix.organization_id == org_id)
        .order_by(RaciMatrix.id.desc())
        .all()
    )
    out = []
    for m in matrices:
        report, _ = _validate(m)
        violations = sum(1 for r in report if r["issues"])
        out.append({
            "id": m.id, "name": m.name, "description": m.description, "version": m.version,
            "role_count": len(m.roles), "process_count": len(m.processes),
            "violations": violations, "created_at": m.created_at,
        })
    return out


@router.get("/raci/matrices/{matrix_id}", response_model=MatrixDetail, tags=["raci"])
def get_matrix(
    matrix_id: int,
    org_id: int = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    return _detail(_get_owned_matrix(db, matrix_id, org_id))


@router.post("/raci/matrices", response_model=MatrixDetail, tags=["raci"])
def create_matrix(
    payload: MatrixCreate,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(_EDIT_ROLES)),
):
    matrix = RaciMatrix(
        organization_id=org_ctx.organization_id,
        name=payload.name, description=payload.description, version=payload.version,
    )
    db.add(matrix)
    db.commit()
    db.refresh(matrix)
    return _detail(matrix)


@router.delete("/raci/matrices/{matrix_id}", tags=["raci"])
def delete_matrix(
    matrix_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(_EDIT_ROLES)),
):
    matrix = _get_owned_matrix(db, matrix_id, org_ctx.organization_id)
    db.delete(matrix)
    db.commit()
    return {"deleted": matrix_id}


@router.post("/raci/matrices/{matrix_id}/roles", response_model=RoleOut, tags=["raci"])
def add_role(
    matrix_id: int,
    payload: RoleIn,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(_EDIT_ROLES)),
):
    matrix = _get_owned_matrix(db, matrix_id, org_ctx.organization_id)
    order = payload.order if payload.order is not None else len(matrix.roles)
    role = RaciRole(
        matrix_id=matrix.id, name=payload.name, order=order,
        charter_decides=payload.charter_decides,
        charter_blocks=payload.charter_blocks,
        charter_escalates=payload.charter_escalates,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return _role_out(role)


@router.post("/raci/matrices/{matrix_id}/processes", response_model=ProcessOut, tags=["raci"])
def add_process(
    matrix_id: int,
    payload: ProcessIn,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(_EDIT_ROLES)),
):
    matrix = _get_owned_matrix(db, matrix_id, org_ctx.organization_id)
    order = payload.order if payload.order is not None else len(matrix.processes)
    process = RaciProcess(
        matrix_id=matrix.id, name=payload.name, order=order,
        evidence_min=payload.evidence_min, handoff_owner=payload.handoff_owner,
    )
    db.add(process)
    db.commit()
    db.refresh(process)
    return _process_out(process)


@router.delete("/raci/roles/{role_id}", tags=["raci"])
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(_EDIT_ROLES)),
):
    role = (
        db.query(RaciRole)
        .join(RaciMatrix, RaciRole.matrix_id == RaciMatrix.id)
        .filter(RaciRole.id == role_id, RaciMatrix.organization_id == org_ctx.organization_id)
        .first()
    )
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()
    return {"deleted": role_id}


@router.delete("/raci/processes/{process_id}", tags=["raci"])
def delete_process(
    process_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(_EDIT_ROLES)),
):
    process = (
        db.query(RaciProcess)
        .join(RaciMatrix, RaciProcess.matrix_id == RaciMatrix.id)
        .filter(RaciProcess.id == process_id, RaciMatrix.organization_id == org_ctx.organization_id)
        .first()
    )
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    db.delete(process)
    db.commit()
    return {"deleted": process_id}


@router.patch("/raci/matrices/{matrix_id}/cell", response_model=MatrixDetail, tags=["raci"])
def set_cell(
    matrix_id: int,
    payload: CellSet,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(_EDIT_ROLES)),
):
    """Add (present=True) or remove (present=False) one RACI value in a cell.
    A cell can hold several values (e.g. R and A), so this toggles a single one."""
    matrix = _get_owned_matrix(db, matrix_id, org_ctx.organization_id)
    value = _parse_value(payload.value)

    # The process and role must belong to this matrix.
    role = db.query(RaciRole).filter(
        RaciRole.id == payload.role_id, RaciRole.matrix_id == matrix.id).first()
    process = db.query(RaciProcess).filter(
        RaciProcess.id == payload.process_id, RaciProcess.matrix_id == matrix.id).first()
    if not role or not process:
        raise HTTPException(status_code=404, detail="Process or role not in this matrix")

    existing = db.query(RaciAssignment).filter(
        RaciAssignment.process_id == payload.process_id,
        RaciAssignment.role_id == payload.role_id,
        RaciAssignment.value == value,
    ).first()

    if payload.present and not existing:
        db.add(RaciAssignment(
            matrix_id=matrix.id, process_id=payload.process_id,
            role_id=payload.role_id, value=value,
        ))
    elif not payload.present and existing:
        db.delete(existing)
    db.commit()
    db.refresh(matrix)
    return _detail(matrix)
