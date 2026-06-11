import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine
from app.routers import auth, organizations, workspaces, documents, chat, diagnoses, roadmaps, reports, audit, agents, kpi, clevel, toolkit, surveys, public_surveys, admin, portal

# Schema is managed by Alembic (`alembic upgrade head`), not create_all.
# Reference data + the initial crew admin are provisioned explicitly via
# `python -m app.scripts.bootstrap_admin` (env-driven), never auto-seeded here.

app = FastAPI(
    title="Syner Cortex API",
    description="Enterprise AI Consulting Operating System & RAG SaaS Platform",
    version="1.0.0"
)

# CORS configuration — restricted to configured origins (env CORS_ORIGINS)
from app.config import CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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
app.include_router(agents.router, prefix="/api")
app.include_router(kpi.router, prefix="/api")
app.include_router(clevel.router, prefix="/api")
app.include_router(toolkit.router, prefix="/api")
app.include_router(surveys.router, prefix="/api")
app.include_router(public_surveys.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(portal.router, prefix="/api")

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
