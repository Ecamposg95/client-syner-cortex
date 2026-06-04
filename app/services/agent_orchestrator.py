import importlib
from typing import Callable, Dict, Any

from fastapi import HTTPException

# Registry mapping agent identifiers to handler callables
# Each handler should be a function accepting (organization_id: int, message: str) and returning a response dict

_agent_registry: Dict[str, Callable[[int, str], Any]] = {}


def register_agent(agent_id: str, handler: Callable[[int, str], Any]):
    """Register a new agent handler.
    Args:
        agent_id: Unique identifier for the agent (e.g., 'strategy', 'founder').
        handler: Callable that takes organization_id and message, returns response.
    """
    if agent_id in _agent_registry:
        raise ValueError(f"Agent '{agent_id}' is already registered")
    _agent_registry[agent_id] = handler


def get_agent_handler(agent_id: str) -> Callable[[int, str], Any]:
    """Retrieve a handler for the given agent identifier.
    Raises HTTPException(404) if not found.
    """
    handler = _agent_registry.get(agent_id)
    if not handler:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return handler


def orchestrate(agent_id: str, organization_id: int, message: str) -> Any:
    """Route the user message to the appropriate agent handler.
    This is a thin wrapper that resolves the handler and invokes it.
    """
    handler = get_agent_handler(agent_id)
    return handler(organization_id, message)

# Example placeholder agent implementations – these would be replaced with real logic later
def _dummy_strategy_agent(org_id: int, msg: str):
    return {"agent": "strategy", "org_id": org_id, "reply": f"Strategy insight for '{msg}'"}

def _dummy_founder_agent(org_id: int, msg: str):
    return {"agent": "founder", "org_id": org_id, "reply": f"Founder perspective on '{msg}'"}

# Register example agents on import
register_agent("strategy", _dummy_strategy_agent)
register_agent("founder", _dummy_founder_agent)
