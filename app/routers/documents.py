import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Document, KnowledgeChunk, OrganizationUser, Workspace
from app.schemas.schemas import DocumentOut
from app.dependencies import get_current_org_id, RoleChecker
from app.policy import Action, ObjectType
from app.policy.deps import get_principal, require_action, scoped_query
from app.policy.principal import Principal
from app.services.ai_engine import chunk_text, get_embedding
import PyPDF2

router = APIRouter(prefix="/documents", tags=["documents"])

# Root folder for uploads in workspace
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    Extract readable text content from file.
    Supports txt/md natively, pdf via PyPDF2, and fails gracefully.
    """
    if file_type in ["txt", "md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
            
    elif file_type == "pdf":
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            raise ValueError(f"Failed to parse PDF document structure: {str(e)}")
        return text
        
    else:
        # Fallback stub for docx/xlsx/pptx files
        return f"Content of {os.path.basename(file_path)}. Ingested as binary file format. (Mock parsing details)."

def process_document_background(doc_id: int, file_path: str, file_type: str, db_session_maker):
    """
    Background job to extract text, chunk it, generate embeddings,
    and save KnowledgeChunks to database.
    """
    db = db_session_maker()
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        db.close()
        return

    try:
        # Extract text content
        text = extract_text_from_file(file_path, file_type)
        if not text.strip():
            raise ValueError("Document appears to contain no readable text.")

        # Chunk text
        chunks = chunk_text(text)
        
        # Embed and insert chunks
        for c in chunks:
            vector = get_embedding(c)
            db_chunk = KnowledgeChunk(
                document_id=doc.id,
                workspace_id=doc.workspace_id,
                content=c,
                embedding=vector
            )
            db.add(db_chunk)
            
        doc.status = "COMPLETED"
        db.commit()
    except Exception as e:
        db.rollback()
        doc.status = "FAILED"
        doc.error_message = str(e)
        db.commit()
        print(f"Error in background processing of document {doc_id}: {e}")
    finally:
        db.close()

@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    workspace_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    # Eje 2: UPLOAD_CLIENT_DOCS is the matrix action that both Syner crew and the
    # client editing tiers (OWNER/EXECUTIVE/MANAGER/CONTRIBUTOR) hold — the lane
    # used to admit a document into a client workspace. The previous ad-hoc list
    # (CLIENT_OWNER/CLIENT_EXECUTIVE/CONSULTANT) is a subset of this, so allowed
    # callers keep access while the gate now derives from the §8 matrix.
    principal: Principal = Depends(require_action(Action.UPLOAD_CLIENT_DOCS)),
):
    """
    Upload a document into a workspace and queue it for AI chunking/embeddings.
    """
    # Verify workspace belongs to organization (Eje 1 scope check)
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Clean file name and determine type
    filename = file.filename
    file_ext = filename.split(".")[-1].lower() if "." in filename else "txt"
    
    # Save local file
    local_filename = f"{workspace_id}_{int(datetime.datetime.utcnow().timestamp())}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, local_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file locally: {e}")

    # Create document db entry.
    # NOTE: visibility keeps the model default (INTERNAL_ONLY) — behaviour-preserving.
    # TODO(visibility): once Document gains an `uploaded_by` column, a client upload
    # should be stamped CLIENT_UPLOAD with uploaded_by=principal.user_id so the
    # uploader can see it back through scoped_query (own-only state). Without that
    # column, own-only states cannot be matched and client uploads stay invisible
    # to the uploader on read — see list_workspace_documents below.
    document = Document(
        workspace_id=workspace_id,
        organization_id=org_id,
        name=filename,
        file_type=file_ext,
        file_path=file_path,
        status="PROCESSING"
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Queue background task to extract, chunk, and embed
    from app.database import SessionLocal
    background_tasks.add_task(
        process_document_background,
        document.id,
        file_path,
        file_ext,
        SessionLocal
    )

    return document

import datetime

@router.get("", response_model=List[DocumentOut])
def list_workspace_documents(
    workspace_id: int,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    principal: Principal = Depends(get_principal),
):
    """
    List documents inside a workspace.

    Eje 3: routed through scoped_query so a CLIENT_USER only ever sees
    CLIENT_SHARED documents (the whitelisted client-visible state for DOCUMENT);
    internal states (INTERNAL_ONLY, etc.) are filtered out at the query layer.
    Crew/superadmin see everything in scope. Previously this returned every row
    in the workspace regardless of visibility — that leak is now closed.

    TODO(visibility): owner_column=None because Document has no `uploaded_by`
    column today, so the CLIENT_UPLOAD own-only state cannot be matched and a
    client's own uploads are not yet returned here. Add `uploaded_by` and pass
    owner_column=Document.uploaded_by to include them.
    """
    # Verify workspace belongs to org (Eje 1 scope check)
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")

    q = scoped_query(
        db, Document, principal, org_id,
        object_type=ObjectType.DOCUMENT,
        owner_column=None,  # TODO: Document.uploaded_by once it exists
    )
    return q.filter(Document.workspace_id == workspace_id).all()

@router.post("/{document_id}/share", response_model=DocumentOut, status_code=status.HTTP_200_OK)
def share_document_with_client(
    document_id: int,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id),
    # Eje 2: SHARE_WITH_CLIENT is the crew-only lane that exposes an internal
    # artifact to the client. Gating here (instead of a role list) means only the
    # roles the §8 matrix grants this action can flip a document to CLIENT_SHARED.
    principal: Principal = Depends(require_action(Action.SHARE_WITH_CLIENT)),
):
    """
    Mark an internal document as shared with the client (CLIENT_SHARED), so it
    becomes visible to CLIENT_USERs via scoped_query. Crew-only.
    """
    # Eje 1: the document must live in the active organization.
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == org_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.visibility = "CLIENT_SHARED"
    db.commit()
    db.refresh(doc)
    return doc

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    org_ctx: OrganizationUser = Depends(RoleChecker(["CLIENT_OWNER", "CLIENT_EXECUTIVE"]))
):
    """
    Delete document, its embeddings, and the file from disk.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.organization_id == org_ctx.organization_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Remove file from disk
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            print(f"Error removing file from disk: {e}")

    db.delete(doc)
    db.commit()
    return {"message": "Document successfully deleted"}
