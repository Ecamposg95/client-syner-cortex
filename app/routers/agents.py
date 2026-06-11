import importlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.dependencies import get_current_org_id
from app.services import agent_orchestrator

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/agents/{agent_id}/chat", tags=["agents"])
def chat_with_agent(agent_id: str, request: ChatRequest, organization_id: int = Depends(get_current_org_id)):
    """Route a chat message to the specified agent.
    Returns the agent's response as JSON.
    """
    try:
        response = agent_orchestrator.orchestrate(agent_id, organization_id, request.message)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
