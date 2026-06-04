import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import Document, KnowledgeChunk, OrganizationUser, Workspace
from app.schemas.schemas import DocumentOut
from app.dependencies import get_organization_context, RoleChecker
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
    org_ctx: OrganizationUser = Depends(RoleChecker(["CLIENT_OWNER", "CLIENT_EXECUTIVE", "CONSULTANT"]))
):
    """
    Upload a document into a workspace and queue it for AI chunking/embeddings.
    """
    # Verify workspace belongs to organization
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_ctx.organization_id
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

    # Create document db entry
    document = Document(
        workspace_id=workspace_id,
        organization_id=org_ctx.organization_id,
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
    org_ctx: OrganizationUser = Depends(get_organization_context)
):
    """
    List all documents inside a workspace.
    """
    # Verify workspace belongs to org
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == org_ctx.organization_id
    ).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found in this organization")
        
    return db.query(Document).filter(Document.workspace_id == workspace_id).all()

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
