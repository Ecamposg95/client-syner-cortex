from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import ChatSession, ChatMessage, OrganizationUser, Workspace
from app.schemas.schemas import ChatSessionCreate, ChatSessionOut, ChatMessageCreate, ChatMessageOut
from app.dependencies import get_organization_context
from app.services.ai_engine import search_workspace_knowledge, generate_ai_response

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_chat_session(
    session_in: ChatSessionCreate,
    workspace_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context)
):
    """
    Start a new chat session in the specified workspace.
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
        title=session_in.title
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionOut])
def list_chat_sessions(
    workspace_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context)
):
    """
    List all chat sessions in the workspace.
    """
    # Verify workspace belongs to organization
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_ctx.organization_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    sessions = db.query(ChatSession).filter(
        ChatSession.workspace_id == workspace_id
    ).order_by(ChatSession.updated_at.desc()).all()
    return sessions

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageOut])
def list_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(get_organization_context)
):
    """
    List all messages in a specific chat session.
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
    org_ctx: OrganizationUser = Depends(get_organization_context)
):
    """
    Send a message to the AI assistant. Performs vector lookup and generates cited response.
    """
    # Validate session
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
        content=message_in.content
    )
    db.add(user_msg)
    
    # 2. Retrieve context from workspace knowledge
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
        sources=citations
    )
    db.add(ai_msg)
    
    # Update session updated_at timestamp
    import datetime
    session.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(ai_msg)
    
    return ai_msg
