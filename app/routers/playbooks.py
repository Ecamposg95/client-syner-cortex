"""Internal Playbooks router — Syner's private methodology library.

CREW-ONLY by construction: every endpoint depends on get_current_syner_crew, so
a CLIENT_USER can never list, read, create, edit or delete a playbook (they
receive 403 before any query runs). Playbooks are firm-internal artifacts and
must never leak to a client.

The `/api` prefix is added by the orchestrator when mounting this router.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_syner_crew
from app.models.models import User
from app.models.playbook import Playbook
from app.schemas.playbook import PlaybookCreate, PlaybookUpdate, PlaybookOut

router = APIRouter()


@router.get("/playbooks", response_model=List[PlaybookOut], tags=["playbooks"])
def list_playbooks(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_syner_crew),
):
    """List internal playbooks (crew-only). Optional ?category= filter."""
    q = db.query(Playbook)
    if category:
        q = q.filter(Playbook.category == category)
    return q.order_by(Playbook.created_at.desc(), Playbook.id.desc()).all()


@router.get("/playbooks/{playbook_id}", response_model=PlaybookOut, tags=["playbooks"])
def get_playbook(
    playbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_syner_crew),
):
    playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbook


@router.post("/playbooks", response_model=PlaybookOut, tags=["playbooks"])
def create_playbook(
    payload: PlaybookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_syner_crew),
):
    playbook = Playbook(
        organization_id=payload.organization_id,
        created_by=current_user.id,
        title=payload.title,
        category=payload.category,
        content=payload.content or "",
        tags=payload.tags,
        visibility=payload.visibility or "INTERNAL_ONLY",
    )
    db.add(playbook)
    db.commit()
    db.refresh(playbook)
    return playbook


@router.put("/playbooks/{playbook_id}", response_model=PlaybookOut, tags=["playbooks"])
def update_playbook(
    playbook_id: int,
    payload: PlaybookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_syner_crew),
):
    playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(playbook, field, value)

    db.commit()
    db.refresh(playbook)
    return playbook


@router.delete("/playbooks/{playbook_id}", tags=["playbooks"])
def delete_playbook(
    playbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_syner_crew),
):
    playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    db.delete(playbook)
    db.commit()
    return {"ok": True, "deleted_id": playbook_id}
