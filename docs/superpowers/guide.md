# Syner Cortex - Superpowers Development Guide

## 1. Nixpacks & Railway Setup
Syner Cortex is designed to be built in a single Railway service using Nixpacks:
- **Build Phase:** Nixpacks compiles the Node project in the `/frontend` subdirectory.
- **Serving static files:** FastAPI mounts the static build folder from `/frontend/dist` and handles fallback HTML5 routing, routing all non-API queries back to the SPA index page.
- **Port mapping:** The server reads `$PORT` dynamically from the environment.

## 2. Environment Variables Checklist
Make sure to configure the following keys inside your `.env` file or Railway dashboard:
- `DATABASE_URL`: PostgreSQL database link (falls back to local SQLite if empty).
- `JWT_SECRET`: Random seed for JWT signing.
- `GEMINI_API_KEY`: API key for Gemini models.
- `OPENAI_API_KEY`: API key for OpenAI models.

## 3. Code Standards & Database Migrations
- Keep models defined inside `app/models/models.py`.
- Ensure all business models register under `Base.metadata` to support automated generation on server startup.
- Validate request inputs using Pydantic schemas in `app/schemas/schemas.py`.
