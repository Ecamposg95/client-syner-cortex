import datetime
import json as _json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Diagnosis, Roadmap, RoadmapItem, Workspace, OrganizationUser
from app.models.report import Report, ReportStatus
from app.models.toolkit import ToolRun, ToolOutput
from app.schemas.report import ReportOut
from app.dependencies import (
    get_organization_context, get_current_org_id, get_current_user,
)
from app.policy.deps import get_principal, require_action, scoped_query
from app.policy.principal import Principal
from app.policy import Action, ObjectType
from app.policy.engine import authorize, can_view

router = APIRouter(prefix="/reports", tags=["reports"])

# States of a Diagnosis/Roadmap that are shareable with a CLIENT_USER. The
# executive brief composes from these two models (which carry their own
# `visibility` string column, distinct from the §8 ObjectType.REPORT whitelist),
# so we match against the project's diagnosis/roadmap state vocabulary directly.
_CLIENT_VISIBLE_REPORT_STATES = frozenset({"APPROVED", "CLIENT_VISIBLE", "CLIENT_SHARED"})


@router.get("/executive-brief")
def get_executive_brief(
    workspace_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context),
    principal: Principal = Depends(require_action(Action.VIEW_APPROVED_REPORTS)),
):
    """
    Generate and retrieve a consolidated executive consulting brief containing
    the latest SWOT, recommendations, and active roadmap items.

    POLICY (Fase 3 wiring): gated on Action.VIEW_APPROVED_REPORTS (ejes 1+2:
    org-scope + role). The brief is composed from Diagnosis + Roadmap, which may
    sit in internal states (INTERNAL_ONLY, DRAFT_INTERNAL). For a CLIENT_USER the
    composition is restricted to client-visible material (eje 3):
      - the latest CLIENT-VISIBLE diagnosis only (an internal latest one yields
        404, never a leak of internal SWOT/findings);
      - a CLIENT-VISIBLE roadmap, with INTERNAL_ONLY items dropped.
    Crew/superadmin compose from the latest diagnosis/roadmap unconditionally.
    """
    # Verify workspace belongs to organization (org-scope, eje 1)
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_ctx.organization_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    org_id = org_ctx.organization_id
    is_client = principal.is_client and not principal.is_superadmin

    # --- Pick the diagnosis the caller is allowed to compose from ---
    diag_q = db.query(Diagnosis).filter(
        Diagnosis.workspace_id == workspace_id,
        Diagnosis.organization_id == org_id,
    )
    if is_client:
        diag_q = diag_q.filter(Diagnosis.visibility.in_(_CLIENT_VISIBLE_REPORT_STATES))
    latest_diag = diag_q.order_by(Diagnosis.created_at.desc()).first()

    if not latest_diag:
        # For a client this is also reached when only internal diagnoses exist:
        # we return the "no diagnosis" response rather than expose internal
        # material — the client-visible query simply found nothing.
        raise HTTPException(
            status_code=400,
            detail="No business diagnosis has been run for this workspace yet."
        )

    # --- Pick the roadmap the caller is allowed to compose from ---
    roadmap_q = db.query(Roadmap).filter(
        Roadmap.workspace_id == workspace_id,
        Roadmap.organization_id == org_id,
    )
    if is_client:
        roadmap_q = roadmap_q.filter(Roadmap.visibility.in_(_CLIENT_VISIBLE_REPORT_STATES))
    latest_roadmap = roadmap_q.order_by(Roadmap.created_at.desc()).first()

    # --- Roadmap items: drop internal items for clients ---
    if latest_roadmap is not None:
        items = latest_roadmap.items
        if is_client:
            visible_item_states = _client_visible_roadmap_item_states()
            items = [it for it in items if it.visibility in visible_item_states]
    else:
        items = []

    # Compile report structure
    report_data = {
        "workspace_name": workspace.name,
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "organization": org_ctx.organization.name,
        "diagnosis_status": latest_diag.status,
        "dimensions": [
            {
                "name": dim.name,
                "rating": dim.rating,
                "findings": dim.findings,
                "recommendations": dim.recommendations,
                "swot": dim.swot_analysis
            }
            for dim in latest_diag.dimensions
        ],
        "roadmap": {
            "created_at": latest_roadmap.created_at.isoformat() if latest_roadmap else None,
            "items": [
                {
                    "title": item.title,
                    "description": item.description,
                    "dimension": item.dimension,
                    "phase": item.phase,
                    "status": item.status,
                    "due_date": item.due_date.isoformat() if item.due_date else None
                }
                for item in items
            ]
        }
    }

    return report_data


def _client_visible_roadmap_item_states() -> frozenset:
    """Roadmap-item states a CLIENT_USER may see, from the policy whitelist."""
    from app.policy.visibility import client_visible_states
    return client_visible_states(ObjectType.ROADMAP_ITEM)


# =========================================================================== #
# REPORT MODULE (§6) — standalone Report records with the DRAFT_INTERNAL →
# CONSULTANT_REVIEW → APPROVED → CLIENT_SHARED lifecycle, optionally composed
# from ToolRun outputs, with markdown export.
#
# Mounted under the same /reports prefix as the executive brief above. The
# executive brief composes Diagnosis+Roadmap; this module manages first-class
# `reports` rows. The two coexist.
# =========================================================================== #

from pydantic import BaseModel  # noqa: E402  (kept local to the report module)


class ReportCreateBody(BaseModel):
    """Body for POST /reports. organization_id/created_by are taken from the
    request context, not the client, so they are not accepted here."""
    title: str
    report_type: Optional[str] = None
    workspace_id: Optional[int] = None
    content: Optional[dict] = None
    # Optionally compose `content` from the outputs of these tool runs.
    tool_run_ids: Optional[List[int]] = None


class ReportPatchBody(BaseModel):
    """Body for PATCH /reports/{id}. All fields optional; the target `status`
    (if present) selects which §8 action gates the edit."""
    title: Optional[str] = None
    report_type: Optional[str] = None
    content: Optional[dict] = None
    status: Optional[ReportStatus] = None


def _owned_report(db: Session, report_id: int, org_id: int) -> Report:
    """Load a Report and enforce Eje 1 (org scope). 404 (never 403) if it does
    not exist or belongs to another organization, so we don't reveal the
    existence of another tenant's report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or report.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def _compose_content_from_runs(
    db: Session, tool_run_ids: List[int], org_id: int
) -> dict:
    """Build a `content` payload from the outputs of the given tool runs.

    Eje 1: every run must belong to `org_id`; a run from another org raises 404
    (never composing across tenants). Returns a dict with a `sections` list, one
    entry per run carrying its outputs' markdown/json."""
    sections = []
    for run_id in tool_run_ids:
        run = db.query(ToolRun).filter(ToolRun.id == run_id).first()
        if not run or run.organization_id != org_id:
            raise HTTPException(
                status_code=404, detail=f"ToolRun {run_id} not found"
            )
        outputs = db.query(ToolOutput).filter(ToolOutput.run_id == run_id).all()
        sections.append({
            "tool_run_id": run_id,
            "tool_name": run.tool.name if run.tool else None,
            "outputs": [
                {
                    "content_markdown": o.content_markdown,
                    "content_json": o.content_json,
                }
                for o in outputs
            ],
        })
    return {"composed_from_tool_runs": tool_run_ids, "sections": sections}


@router.get("", response_model=List[ReportOut], tags=["reports"])
@router.get("/", response_model=List[ReportOut], tags=["reports"])
def list_reports(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    principal: Principal = Depends(get_principal),
):
    """List reports for the active org. Eje 1: org-scoped. Eje 3: a CLIENT_USER
    sees only CLIENT_SHARED reports (via scoped_query's REPORT whitelist); crew
    see all in scope. Optional ?status= narrows the list further."""
    q = scoped_query(db, Report, principal, org_id, object_type=ObjectType.REPORT)
    if status_filter:
        # Accept either the enum name or value; an unknown status yields nothing.
        try:
            target = ReportStatus[status_filter]
        except KeyError:
            target = next(
                (m for m in ReportStatus if m.value == status_filter), None
            )
        if target is None:
            return []
        q = q.filter(Report.status == target)
    return q.order_by(Report.created_at.desc()).all()


@router.get("/{report_id}", response_model=ReportOut, tags=["reports"])
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    principal: Principal = Depends(get_principal),
):
    """Fetch one report. 404 if outside the active org (Eje 1). Eje 3: a client
    only reaches a report whose visibility is CLIENT_SHARED — otherwise 404
    (never 403) so a client can't probe internal-report existence."""
    report = _owned_report(db, report_id, org_id)
    if not can_view(principal, ObjectType.REPORT, report.visibility, org_id=org_id):
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("", response_model=ReportOut, tags=["reports"])
@router.post("/", response_model=ReportOut, tags=["reports"])
def create_report(
    data: ReportCreateBody,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    user=Depends(get_current_user),
    # Eje 2: authoring a report is the EDIT_AI_OUTPUTS action (crew lane).
    principal: Principal = Depends(require_action(Action.EDIT_AI_OUTPUTS)),
):
    """Create a DRAFT_INTERNAL report in the active org. If `tool_run_ids` are
    given, `content` is composed from those runs' outputs (all validated to be
    in the same org); an explicit `content` is used as-is otherwise."""
    content = data.content
    if data.tool_run_ids:
        content = _compose_content_from_runs(db, data.tool_run_ids, org_id)

    report = Report(
        organization_id=org_id,
        workspace_id=data.workspace_id,
        created_by=user.id,
        title=data.title,
        report_type=data.report_type,
        status=ReportStatus.DRAFT_INTERNAL,
        visibility="DRAFT_INTERNAL",
        content=content,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.patch("/{report_id}", response_model=ReportOut, tags=["reports"])
def update_report(
    report_id: int,
    data: ReportPatchBody,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    user=Depends(get_current_user),
    principal: Principal = Depends(get_principal),
):
    """Edit a report's title/type/content and/or transition its status.

    Eje 1: scope the report to the active org. Eje 2: the *target* status decides
    which action gates the edit (same pattern as toolkit.py PATCH /status):
      CLIENT_SHARED → SHARE_WITH_CLIENT  (also sets visibility + shared_at)
      APPROVED      → APPROVE_DELIVERABLES (also records approved_by)
      anything else → EDIT_AI_OUTPUTS
    We resolve the gate in-body because the required action depends on the body.
    """
    report = _owned_report(db, report_id, org_id)

    if data.status == ReportStatus.CLIENT_SHARED:
        required = Action.SHARE_WITH_CLIENT
    elif data.status == ReportStatus.APPROVED:
        required = Action.APPROVE_DELIVERABLES
    else:
        required = Action.EDIT_AI_OUTPUTS
    if not authorize(principal, required, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para esta acción",
        )

    if data.title is not None:
        report.title = data.title
    if data.report_type is not None:
        report.report_type = data.report_type
    if data.content is not None:
        report.content = data.content

    if data.status is not None:
        report.status = data.status
        if data.status == ReportStatus.APPROVED:
            report.approved_by = user.id
        elif data.status == ReportStatus.CLIENT_SHARED:
            report.visibility = "CLIENT_SHARED"
            report.shared_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()
    db.refresh(report)
    return report


@router.post("/{report_id}/export-markdown", tags=["reports"])
def export_report_markdown(
    report_id: int,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    user=Depends(get_current_user),
    # Crew action: producing an export of internal/approved material is gated on
    # EDIT_AI_OUTPUTS (the crew authoring lane), matching the toolkit pattern.
    principal: Principal = Depends(require_action(Action.EDIT_AI_OUTPUTS)),
):
    """Render a report's content as markdown. Eje 1: scope to the active org."""
    report = _owned_report(db, report_id, org_id)

    md_parts = [f"# {report.title}\n"]
    if report.report_type:
        md_parts.append(f"_{report.report_type}_\n")

    content = report.content or {}
    sections = content.get("sections") if isinstance(content, dict) else None
    if sections:
        for sec in sections:
            name = sec.get("tool_name") or f"Tool Run {sec.get('tool_run_id')}"
            md_parts.append(f"## {name}\n")
            for out in sec.get("outputs", []):
                if out.get("content_markdown"):
                    md_parts.append(out["content_markdown"])
                elif out.get("content_json") is not None:
                    md_parts.append(
                        "```json\n"
                        + _json.dumps(out["content_json"], indent=2, ensure_ascii=False)
                        + "\n```"
                    )
    elif content:
        md_parts.append(
            "```json\n" + _json.dumps(content, indent=2, ensure_ascii=False) + "\n```"
        )

    return {"markdown": "\n\n".join(md_parts)}
