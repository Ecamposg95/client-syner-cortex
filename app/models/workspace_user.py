from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, func, UniqueConstraint,
)
from app.database import Base


class WorkspaceUser(Base):
    """Membership row linking a user to a workspace (Task Pack §6).

    Each row records that `user_id` belongs to `workspace_id` with a
    workspace-local role (`workspace_role`) and an optional visibility scope
    (`visibility_scope`) that narrows what the member can see inside the
    workspace. The (workspace_id, user_id) pair is unique so a user cannot be
    enrolled twice in the same workspace.
    """
    __tablename__ = "workspace_users"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Role the member holds *within* this workspace (e.g. OWNER, MEMBER, VIEWER).
    workspace_role = Column(String, nullable=False)
    # Optional visibility scope narrowing what this member sees in the workspace.
    visibility_scope = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
