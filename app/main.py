import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
from app.routers import auth, organizations, workspaces, documents, chat, diagnoses, roadmaps, reports, audit

# Initialize database tables on startup (especially useful for SQLite out-of-the-box setup)
Base.metadata.create_all(bind=engine)

# Auto-seed initial modules and mock user
from app.models.models import Module, User, Organization, OrganizationUser
from app.security.auth import get_password_hash
from app.database import SessionLocal

db = SessionLocal()
try:
    # Seed modules if empty
    if db.query(Module).count() == 0:
        modules = [
            Module(name="Cortex Vault", code="cortex_vault", description="RAG enterprise knowledge vault"),
            Module(name="Cortex Chat", code="cortex_chat", description="Context-aware AI consultant chat"),
            Module(name="Cortex Diagnose", code="cortex_diagnose", description="360-degree business diagnostics"),
            Module(name="Cortex Agents", code="cortex_agents", description="Specialized AI consulting agents"),
            Module(name="Cortex Insights", code="cortex_insights", description="Business metrics analysis & alarms"),
            Module(name="Cortex Reports", code="cortex_reports", description="Boardroom executive briefings compiler"),
            Module(name="Cortex Roadmap", code="cortex_roadmap", description="30/60/90 execution roadmap backlog"),
            Module(name="Cortex Boardroom", code="cortex_boardroom", description="C-Suite executive boardroom KPI dashboard")
        ]
        db.add_all(modules)
        db.commit()

    # Seed mock admin user if empty
    if db.query(User).filter(User.email == "admin@cortex.com").count() == 0:
        admin_user = User(
            email="admin@cortex.com",
            hashed_password=get_password_hash("password123"),
            full_name="Arturo Villanueva",
            is_active=True,
            is_superadmin=True
        )
        db.add(admin_user)
        db.flush()

        # Seed default org for admin
        admin_org = Organization(name="Syner Consulting Org", slug="syner-consulting")
        db.add(admin_org)
        db.flush()

        # Link admin user
        link = OrganizationUser(
            organization_id=admin_org.id,
            user_id=admin_user.id,
            role="SUPERADMIN"
        )
        db.add(link)
        db.commit()
finally:
    db.close()

app = FastAPI(
    title="Syner Cortex API",
    description="Enterprise AI Consulting Operating System & RAG SaaS Platform",
    version="1.0.0"
)

# CORS configuration to allow local development connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock this down to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(organizations.router, prefix="/api")
app.include_router(workspaces.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(diagnoses.router, prefix="/api")
app.include_router(roadmaps.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(audit.router, prefix="/api")

@app.get("/api/health", tags=["health"])
def health_check():
    """
    Service availability health check.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "database": str(engine.url.drivername)
    }

import datetime

# Serve React SPA build files in production environment
FRONTEND_DIST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend",
    "dist"
)

# Catch-all handler for HTML5 client-side routing fallback (SPA catch-all)
@app.get("/{catchall:path}")
def read_index(catchall: str):
    # Exclude API endpoints from routing catch-all
    if catchall.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
        
    index_path = os.path.join(FRONTEND_DIST_DIR, "index.html")
    
    # If the file exists, return the index.html to let React Router handle routing
    if os.path.exists(index_path):
        # Serve static assets directly if they exist
        asset_path = os.path.join(FRONTEND_DIST_DIR, catchall)
        if os.path.exists(asset_path) and os.path.isfile(asset_path):
            return FileResponse(asset_path)
        return FileResponse(index_path)
        
    return {
        "message": "Syner Cortex API is online.",
        "note": "Frontend React assets not found. Run 'npm run build' inside the frontend workspace."
    }
