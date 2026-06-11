from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app.dependencies import get_current_org_id, get_current_user
from app.models.toolkit import (
    ConsultingToolkit, ConsultingTool, ToolTemplate, ToolRun, ToolInput,
    ToolOutput, ToolRecommendation, ToolExport, ToolRunStatus, Visibility
)
from app.schemas.toolkit import (
    ConsultingToolkitResponse, ConsultingToolkitCreate,
    ConsultingToolResponse, ConsultingToolCreate,
    ToolRunResponse, ToolRunCreate, ToolRunUpdateStatus,
    ToolInputCreate, ToolInputResponse,
    ToolOutputResponse,
    ToolRecommendationCreate, ToolRecommendationResponse,
)
from app.services.toolkit.base_services import ConsultingToolkitService, ToolExecutionService

router = APIRouter()

# ─── TOOLKITS ──────────────────────────────────────────────────────

@router.get("/toolkits", response_model=List[ConsultingToolkitResponse], tags=["toolkit"])
def get_toolkits(db: Session = Depends(get_db)):
    return ConsultingToolkitService.get_all_toolkits(db)

@router.post("/toolkits", response_model=ConsultingToolkitResponse, tags=["toolkit"])
def create_toolkit(data: ConsultingToolkitCreate, db: Session = Depends(get_db)):
    return ConsultingToolkitService.create_toolkit(db, data)

# ─── TOOLS (by toolkit) ───────────────────────────────────────────

@router.get("/toolkits/{toolkit_id}/tools", response_model=List[ConsultingToolResponse], tags=["toolkit"])
def get_tools_by_toolkit(toolkit_id: int, db: Session = Depends(get_db)):
    tools = db.query(ConsultingTool).filter(
        ConsultingTool.toolkit_id == toolkit_id,
        ConsultingTool.is_active == True
    ).all()
    return tools

@router.get("/tools/{tool_id}", tags=["toolkit"])
def get_tool_detail(tool_id: int, db: Session = Depends(get_db)):
    tool = db.query(ConsultingTool).options(
        joinedload(ConsultingTool.toolkit),
        joinedload(ConsultingTool.templates)
    ).filter(ConsultingTool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    template = tool.templates[0] if tool.templates else None
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "toolkit_id": tool.toolkit_id,
        "toolkit_name": tool.toolkit.name if tool.toolkit else "",
        "has_template": template is not None,
        "template": {
            "id": template.id,
            "system_prompt": template.system_prompt,
            "user_prompt_template": template.user_prompt_template,
            "json_schema_output": template.json_schema_output,
        } if template else None,
    }

# ─── TOOL RUNS ─────────────────────────────────────────────────────

@router.post("/tool-runs", response_model=ToolRunResponse, tags=["toolkit"])
def create_tool_run(
    data: ToolRunCreate,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    user=Depends(get_current_user)
):
    return ToolExecutionService.create_run(
        db=db,
        tool_id=data.tool_id,
        org_id=org_id,
        user_id=user.id,
        workspace_id=data.workspace_id
    )

@router.post("/tool-runs/{run_id}/execute", tags=["toolkit"])
def execute_tool_run(run_id: int, db: Session = Depends(get_db)):
    run = ToolExecutionService.execute_tool(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="ToolRun not found")
    return {"id": run.id, "status": run.status.value}

@router.get("/tool-runs/{run_id}", tags=["toolkit"])
def get_tool_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(ToolRun).options(
        joinedload(ToolRun.inputs),
        joinedload(ToolRun.outputs),
        joinedload(ToolRun.recommendations),
        joinedload(ToolRun.tool)
    ).filter(ToolRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="ToolRun not found")
    return {
        "id": run.id,
        "tool_id": run.tool_id,
        "tool_name": run.tool.name if run.tool else "",
        "status": run.status.value if run.status else "DRAFT",
        "visibility": run.visibility.value if run.visibility else "INTERNAL_ONLY",
        "created_at": run.created_at,
        "inputs": [{"id": i.id, "key": i.key, "value": i.value} for i in run.inputs],
        "outputs": [{
            "id": o.id,
            "content_json": o.content_json,
            "content_markdown": o.content_markdown,
            "generated_at": o.generated_at,
        } for o in run.outputs],
        "recommendations": [{
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "is_converted_to_roadmap": r.is_converted_to_roadmap
        } for r in run.recommendations],
    }

@router.patch("/tool-runs/{run_id}/status", tags=["toolkit"])
def update_run_status(run_id: int, data: ToolRunUpdateStatus, db: Session = Depends(get_db)):
    run = db.query(ToolRun).filter(ToolRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="ToolRun not found")
    run.status = data.status
    db.commit()
    db.refresh(run)
    return {"id": run.id, "status": run.status.value}

# ─── TOOL INPUTS ───────────────────────────────────────────────────

@router.post("/tool-runs/{run_id}/inputs", response_model=ToolInputResponse, tags=["toolkit"])
def add_input(run_id: int, data: ToolInputCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    run = db.query(ToolRun).filter(ToolRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="ToolRun not found")
    inp = ToolInput(run_id=run_id, key=data.key, value=data.value, uploaded_by=user.id)
    db.add(inp)
    db.commit()
    db.refresh(inp)
    return inp

# ─── TOOL OUTPUTS (manual save for consultant edits) ───────────────

@router.post("/tool-runs/{run_id}/outputs", tags=["toolkit"])
def save_output(run_id: int, content_json: dict = None, content_markdown: str = None, db: Session = Depends(get_db)):
    run = db.query(ToolRun).filter(ToolRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="ToolRun not found")
    output = ToolOutput(run_id=run_id, content_json=content_json, content_markdown=content_markdown)
    db.add(output)
    run.status = ToolRunStatus.AI_GENERATED
    db.commit()
    db.refresh(output)
    return {"id": output.id, "content_json": output.content_json}

# ─── RECOMMENDATIONS ───────────────────────────────────────────────

@router.post("/tool-runs/{run_id}/recommendations", response_model=ToolRecommendationResponse, tags=["toolkit"])
def add_recommendation(run_id: int, data: ToolRecommendationCreate, db: Session = Depends(get_db)):
    rec = ToolRecommendation(run_id=run_id, title=data.title, description=data.description)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

@router.get("/tool-runs/{run_id}/recommendations", response_model=List[ToolRecommendationResponse], tags=["toolkit"])
def get_recommendations(run_id: int, db: Session = Depends(get_db)):
    return db.query(ToolRecommendation).filter(ToolRecommendation.run_id == run_id).all()

# ─── EXPORTS ───────────────────────────────────────────────────────

@router.post("/tool-runs/{run_id}/export-markdown", tags=["toolkit"])
def export_markdown(run_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    run = db.query(ToolRun).options(
        joinedload(ToolRun.outputs),
        joinedload(ToolRun.tool)
    ).filter(ToolRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="ToolRun not found")

    md_parts = [f"# {run.tool.name}\n"]
    for output in run.outputs:
        if output.content_markdown:
            md_parts.append(output.content_markdown)
        elif output.content_json:
            import json
            md_parts.append(f"```json\n{json.dumps(output.content_json, indent=2, ensure_ascii=False)}\n```")

    markdown_content = "\n\n".join(md_parts)

    export = ToolExport(run_id=run_id, format="MARKDOWN", file_url=None, exported_by=user.id)
    db.add(export)
    db.commit()

    return {"markdown": markdown_content, "export_id": export.id}
