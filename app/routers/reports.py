from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Diagnosis, Roadmap, Workspace, OrganizationUser
from app.dependencies import get_organization_context

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/executive-brief")
def get_executive_brief(
    workspace_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context)
):
    """
    Generate and retrieve a consolidated executive consulting brief containing
    the latest SWOT, recommendations, and active roadmap items.
    """
    # Verify workspace belongs to organization
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_ctx.organization_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    latest_diag = db.query(Diagnosis).filter(
        Diagnosis.workspace_id == workspace_id
    ).order_by(Diagnosis.created_at.desc()).first()

    latest_roadmap = db.query(Roadmap).filter(
        Roadmap.workspace_id == workspace_id
    ).order_by(Roadmap.created_at.desc()).first()

    if not latest_diag:
        raise HTTPException(
            status_code=400,
            detail="No business diagnosis has been run for this workspace yet."
        )

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
                for item in latest_roadmap.items
            ] if latest_roadmap else []
        }
    }

    return report_data

import datetime
