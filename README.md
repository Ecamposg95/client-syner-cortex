# Syner Hub - Transformation Operating System

**Syner Hub** is a multi-tenant SaaS business intelligence and transformation platform designed for clients of Grupo Syner. 

The platform turns unstructured internal documentation, processes, and corporate KPIs into actionable diagnostics, cited semantic answers, and execution plans using enterprise RAG and structured decision matrices.

---

## SaaS Product Modules (Syner Hub Architecture)

Syner Hub is designed around a client-facing portal focusing on real-time transformation visibility:
- **Overview:** Executive boardroom dashboard with real-time strategic alignment.
- **KPIs:** Detailed matrix of operational, financial, and HR metrics.
- **Roadmap:** Visual 30/60/90 days timeline for project phases.
- **Entregables:** Centralized vault for downloading executive reports and files.
- **Bitácora:** Traceable, auditable log of decisions and agreements.

*For a detailed module-by-module breakdown and cases of use, refer to the [Full Modules Registry](file:///home/cto/Devs/syner-cortex/docs/product/modules.md).*

---

## Canonical Technology Stack

- **Backend Architecture:**
  - Python 3.12
  - FastAPI
  - SQLAlchemy 2.0 (compatible with PostgreSQL and SQLite)
  - Pydantic v2
  - python-jose (JWT auth keys)
  - PyPDF2 (document text extraction)
- **Frontend Architecture:**
  - React 18
  - TypeScript
  - Vite
  - Zustand (state management)
  - Axios (HTTP client)
  - Tailwind CSS (premium custom dark theme)
  - Lucide React (vector iconography)

---

## Directory Structure

```text
syner-cortex/
├── app/                  # FastAPI python backend
│   ├── models/           # SQLAlchemy database schemas
│   ├── schemas/          # Pydantic serialization models
│   ├── security/         # Password hashing & JWT helpers
│   ├── services/         # AI RAG & SWOT Diagnosis Engines
│   ├── routers/          # API endpoints
│   ├── database.py       # DB engine connections
│   ├── dependencies.py   # Global RBAC/JWT dependencies
│   └── main.py           # Application entrypoint
│
├── frontend/             # React Vite SPA frontend
│   ├── src/
│   │   ├── api/          # Axios HTTP client interceptors
│   │   ├── store/        # Zustand state stores
│   │   ├── components/   # Layouts & UI primitives
│   │   ├── pages/        # Auth & Dashboard pages
│   │   ├── main.tsx
│   │   └── App.tsx
│   ├── tailwind.config.js
│   └── package.json
│
├── docs/                 # Product and Architecture context
└── requirements.txt      # Python libraries
```

---

## Local Setup & Launch Guide

### 1. Install Dependencies
You can install both backend python virtualenv and frontend npm modules automatically using the root utility:
```bash
npm run install:all
```
*Note: If python-venv is missing on your host system, the script will automatically fallback to installing packages in your virtualenv by bootstrapping pip.*

### 2. Configure Environment variables
Create a `.env` file at the project root:
```env
DATABASE_URL=sqlite:///./syner_cortex.db
JWT_SECRET=super_secret_session_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 3. Start Development Services
- **Backend FastAPI server:**
  ```bash
  .venv/bin/uvicorn app.main:app --reload
  ```
- **Frontend Vite server:**
  ```bash
  npm run dev --prefix frontend
  ```

Open your browser at [http://localhost:5173](http://localhost:5173) and log in using the pre-seeded admin user:
- **Email:** `admin@synerhub.com`
- **Password:** `password123`

---

## Deployment & Builds

Syner Hub is fully prepared for continuous deployment on **Railway** utilizing **Nixpacks**:
- Nixpacks automatically installs Python 3.12 and Node 20.
- Compiles React SPA code into production static assets.
- Runs the FastAPI web application, serving both REST API endpoints and fallback catch-all routes.
