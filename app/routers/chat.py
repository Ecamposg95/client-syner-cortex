from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import ChatSession, ChatMessage, OrganizationUser, Workspace
from app.schemas.schemas import ChatSessionCreate, ChatSessionOut, ChatMessageCreate, ChatMessageOut
from app.dependencies import get_organization_context
from app.policy.deps import get_principal, require_action
from app.policy.principal import Principal
from app.policy import Action
from app.services.ai_engine import search_workspace_knowledge, generate_ai_response

router = APIRouter(prefix="/chat", tags=["chat"])

# ---------------------------------------------------------------------------
# POLICY NOTE (Fase 3 wiring)
# ---------------------------------------------------------------------------
# ChatSession / ChatMessage are, BY DESIGN, an internal crew tool. Both rows
# default to visibility="INTERNAL_ONLY" and the RAG retrieval reaches into the
# workspace knowledge base (internal docs included). There is therefore NO safe
# client-facing surface here today, so every endpoint is gated on the crew-only
# action Action.USE_INTERNAL_RAG (ejes 1+2: org-scope + role). A CLIENT_USER is
# rejected with 403 before reaching any data.
#
# Org-scope is ALSO enforced object-by-object: each handler loads the session
# (or its workspace) and verifies organization_id == X-Organization-ID, raising
# 404 (not 403) so we never confirm the existence of another org's sessions.
#
# TODO(service): a "client limited chat" mode (Action.CLIENT_LIMITED_CHAT) would
# require search_workspace_knowledge() to filter KnowledgeChunk by the source
# document's visibility (only CLIENT_SHARED / CLIENT_UPLOAD). Today
# app/services/ai_engine.py::search_workspace_knowledge retrieves EVERY chunk of
# the workspace with no visibility filter, so exposing chat to clients would leak
# INTERNAL_ONLY document content. Until that service filters by shared docs,
# client chat stays disabled (crew-only gate above).


@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_chat_session(
    session_in: ChatSessionCreate,
    workspace_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context),
    principal: Principal = Depends(require_action(Action.USE_INTERNAL_RAG)),
):
    """
    Start a new chat session in the specified workspace (internal crew tool).
    """
    # Verify workspace belongs to organization
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_ctx.organization_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    session = ChatSession(
        workspace_id=workspace_id,
        organization_id=org_ctx.organization_id,
        user_id=org_ctx.user_id,
        title=session_in.title,
        visibility="INTERNAL_ONLY",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionOut])
def list_chat_sessions(
    workspace_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context),
    principal: Principal = Depends(require_action(Action.USE_INTERNAL_RAG)),
):
    """
    List all chat sessions in the workspace (internal crew tool).
    """
    # Verify workspace belongs to organization
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_ctx.organization_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    sessions = db.query(ChatSession).filter(
        ChatSession.workspace_id == workspace_id,
        ChatSession.organization_id == org_ctx.organization_id,
    ).order_by(ChatSession.updated_at.desc()).all()
    return sessions

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageOut])
def list_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context),
    principal: Principal = Depends(require_action(Action.USE_INTERNAL_RAG)),
):
    """
    List all messages in a specific chat session (internal crew tool).
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.organization_id == org_ctx.organization_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    return messages

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
def send_chat_message(
    session_id: int,
    message_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context),
    principal: Principal = Depends(require_action(Action.USE_INTERNAL_RAG)),
):
    """
    Send a message to the AI assistant (internal crew tool). Performs vector
    lookup over the workspace knowledge and generates a cited response.
    """
    # Validate session belongs to the org in scope
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.organization_id == org_ctx.organization_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # 1. Save user message to database
    user_msg = ChatMessage(
        session_id=session_id,
        sender="user",
        content=message_in.content,
        visibility="INTERNAL_ONLY",
    )
    db.add(user_msg)

    # 2. Retrieve context from workspace knowledge.
    # TODO(service): search_workspace_knowledge does NOT filter chunks by the
    # source document visibility. It is safe here because this endpoint is
    # crew-only (USE_INTERNAL_RAG); it MUST gain a shared-docs filter before any
    # CLIENT_LIMITED_CHAT mode is exposed. The org-scope is preserved because the
    # workspace is reached through `session` (already org-validated above).
    context_chunks_scores = search_workspace_knowledge(
        db,
        session.workspace_id,
        message_in.content,
        top_k=4
    )
    context_chunks = [chunk for chunk, score in context_chunks_scores]

    # 3. Generate cited AI response
    ai_text, citations = generate_ai_response(
        db,
        session.workspace_id,
        message_in.content,
        context_chunks
    )

    # 4. Save AI reply to database
    ai_msg = ChatMessage(
        session_id=session_id,
        sender="assistant",
        content=ai_text,
        sources=citations,
        visibility="INTERNAL_ONLY",
    )
    db.add(ai_msg)

    # Update session updated_at timestamp
    import datetime
    session.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(ai_msg)

    return ai_msg
