"""Comments / collaboration router (Task Pack §6).

Polymorphic comment threads attached to any commentable artifact — reports,
tool runs, roadmap items, documents, RACI matrices … — identified by the
(`object_type`, `object_id`) pair rather than a real FK, so a single endpoint
family serves every view.

Authorization model (Eje 1 — org scoping):
  - Comments are ALWAYS org-scoped. Every query filters
    `Comment.organization_id == org_id`, where `org_id` comes from the validated
    `get_current_org_id` dependency (the caller must be a member, or crew/superadmin,
    of the org named in X-Organization-ID). This makes collaboration bidirectional
    *within* an org (crew and client of the same org both read and write) while
    cross-org access simply yields an empty list / 404 — never a 403 that would
    confirm the object exists.
  - Delete is restricted to the comment's author OR Syner crew; any other user
    gets 403.

The router is mounted by the orchestrator under the /api prefix.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user, get_current_org_id
from app.models.comment import Comment
from app.models.models import User

router = APIRouter()


# --------------------------------------------------------------------------- #
# Schemas (local: the Out enriches CommentOut with the author's name/email)
# --------------------------------------------------------------------------- #
class CommentCreateIn(BaseModel):
    object_type: str
    object_id: int
    content: str


class CommentOut(BaseModel):
    id: int
    object_type: str
    object_id: int
    organization_id: int
    author_id: int
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    content: str
    created_at: object  # datetime; pydantic serializes it as ISO string

    class Config:
        arbitrary_types_allowed = True


def _to_out(comment: Comment, author: Optional[User]) -> dict:
    return {
        "id": comment.id,
        "object_type": comment.object_type,
        "object_id": comment.object_id,
        "organization_id": comment.organization_id,
        "author_id": comment.author_id,
        "author_name": author.full_name if author else None,
        "author_email": author.email if author else None,
        "content": comment.content,
        "created_at": comment.created_at,
    }


def _is_crew(user: User) -> bool:
    return user.user_type == "SYNER_CREW" or bool(user.is_superadmin)


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@router.get("/comments", response_model=List[CommentOut], tags=["comments"])
def list_comments(
    object_type: str = Query(..., min_length=1),
    object_id: int = Query(...),
    org_id: int = Depends(get_current_org_id),
    db: Session = Depends(get_db),
):
    """List the comments on ONE object, within the caller's org, oldest first.

    Org-scoped: a caller in org A asking for an object that only has comments in
    org B simply receives an empty list (the org filter never matches), so there
    is no cross-org leak and no 403 that would confirm the object's existence.
    """
    rows = (
        db.query(Comment, User)
        .outerjoin(User, User.id == Comment.author_id)
        .filter(
            Comment.organization_id == org_id,
            Comment.object_type == object_type,
            Comment.object_id == object_id,
        )
        .order_by(Comment.created_at.asc(), Comment.id.asc())
        .all()
    )
    return [_to_out(c, author) for c, author in rows]


@router.post(
    "/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
    tags=["comments"],
)
def create_comment(
    payload: CommentCreateIn,
    org_id: int = Depends(get_current_org_id),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a comment on an object, authored by the caller in the caller's org.

    `author_id` and `organization_id` are taken from the authenticated context —
    never from the request body — so a caller can only ever write into their own
    org under their own identity.
    """
    content = (payload.content or "").strip()
    if not content:
        raise HTTPException(status_code=422, detail="content must not be empty")

    comment = Comment(
        object_type=payload.object_type,
        object_id=payload.object_id,
        organization_id=org_id,
        author_id=user.id,
        content=content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _to_out(comment, user)


@router.delete("/comments/{comment_id}", tags=["comments"])
def delete_comment(
    comment_id: int,
    org_id: int = Depends(get_current_org_id),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a comment. Only its author OR Syner crew may delete it.

    Org-scoped first: a comment in another org is invisible here (404), so the
    403 path only ever fires for a real, visible comment the caller doesn't own.
    """
    comment = (
        db.query(Comment)
        .filter(Comment.id == comment_id, Comment.organization_id == org_id)
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != user.id and not _is_crew(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el autor o el crew pueden borrar este comentario",
        )

    db.delete(comment)
    db.commit()
    return {"deleted": comment_id}
