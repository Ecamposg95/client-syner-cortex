from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Enum, DateTime, func, UniqueConstraint,
)
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class RaciValue(enum.Enum):
    """The four classic RACI responsibilities. A single (process, role) cell may
    legitimately hold more than one (e.g. "R/A" in the BJX matrix), so a cell is
    modelled as a *set* of assignment rows rather than one combined value."""
    R = "R"  # Responsible — does the work
    A = "A"  # Accountable — the single owner who answers for the outcome
    C = "C"  # Consulted — two-way input before/while doing
    I = "I"  # Informed — kept up to date one-way


class RaciMatrix(Base):
    """An interactive RACI matrix scoped to one client organization. Rows are
    processes, columns are roles, and each cell is the set of RaciAssignment
    values for that (process, role) pair. Roles carry an authority *charter*
    (what they decide / block / escalate) so the UI can surface accountability
    context on hover."""
    __tablename__ = "raci_matrices"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String, nullable=False, default="1.0")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    roles = relationship(
        "RaciRole", back_populates="matrix",
        cascade="all, delete-orphan", order_by="RaciRole.order",
    )
    processes = relationship(
        "RaciProcess", back_populates="matrix",
        cascade="all, delete-orphan", order_by="RaciProcess.order",
    )
    assignments = relationship(
        "RaciAssignment", back_populates="matrix", cascade="all, delete-orphan",
    )


class RaciRole(Base):
    """A column of the matrix (an operating role) plus its authority charter."""
    __tablename__ = "raci_roles"

    id = Column(Integer, primary_key=True, index=True)
    matrix_id = Column(
        Integer, ForeignKey("raci_matrices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    order = Column(Integer, default=0, nullable=False)

    # Authority charter (PPTX slide 5): what this role decides, what it can
    # block/veto, and what it must escalate.
    charter_decides = Column(Text, nullable=True)
    charter_blocks = Column(Text, nullable=True)
    charter_escalates = Column(Text, nullable=True)

    matrix = relationship("RaciMatrix", back_populates="roles")


class RaciProcess(Base):
    """A row of the matrix (a critical process) plus its handoff metadata."""
    __tablename__ = "raci_processes"

    id = Column(Integer, primary_key=True, index=True)
    matrix_id = Column(
        Integer, ForeignKey("raci_matrices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    order = Column(Integer, default=0, nullable=False)

    # Handoff context (PPTX slide 8): minimum evidence required before the
    # process can advance, and the role that owns the handoff gate.
    evidence_min = Column(Text, nullable=True)
    handoff_owner = Column(String, nullable=True)

    matrix = relationship("RaciMatrix", back_populates="processes")


class RaciAssignment(Base):
    """One responsibility a role holds on a process. A (process, role) pair can
    carry several rows (e.g. both R and A). The unique constraint forbids the
    same value twice for the same cell."""
    __tablename__ = "raci_assignments"
    __table_args__ = (
        UniqueConstraint("process_id", "role_id", "value", name="uq_raci_cell_value"),
    )

    id = Column(Integer, primary_key=True, index=True)
    matrix_id = Column(
        Integer, ForeignKey("raci_matrices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    process_id = Column(
        Integer, ForeignKey("raci_processes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id = Column(
        Integer, ForeignKey("raci_roles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value = Column(Enum(RaciValue), nullable=False)

    matrix = relationship("RaciMatrix", back_populates="assignments")
