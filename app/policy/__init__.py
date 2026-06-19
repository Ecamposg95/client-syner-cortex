"""Central access-control policy (Task Pack Fase 3).

Three axes — scope (org/workspace), role (capability matrix §8), object
visibility (§4) — evaluated in one place instead of scattered per-endpoint
checks. Import the engine entrypoints from here.
"""
from app.policy.actions import Action
from app.policy.capabilities import Capability, capability, is_allowed, CAPABILITY_MATRIX
from app.policy.principal import Principal, build_principal
from app.policy.visibility import ObjectType, is_visible, client_visible_states
from app.policy.engine import authorize, can_view, can_access

__all__ = [
    "Action", "Capability", "capability", "is_allowed", "CAPABILITY_MATRIX",
    "Principal", "build_principal",
    "ObjectType", "is_visible", "client_visible_states",
    "authorize", "can_view", "can_access",
]
