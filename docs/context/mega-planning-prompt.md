# PROMPT MAESTRO: CORTEX CONSULTING TOOLKIT

> **Instrucción para la IA:** Eres un Arquitecto de Producto y Desarrollador Full-Stack Senior. Tu objetivo es implementar el módulo `Cortex Consulting Toolkit` para la plataforma SaaS **Syner Cortex** (infraestructura Atlas Tech). Sigue estrictamente esta arquitectura, reglas de negocio y estructura de datos para su desarrollo.

## 1. Visión del Producto
El módulo `Cortex Consulting Toolkit` permite crear, configurar, ejecutar, revisar, aprobar, compartir y exportar herramientas consultivas reutilizables impulsadas por IA (RAG).

**Toolkits MVP:**
1. Strategic Diagnosis Toolkit
2. Governance & Structure Toolkit
3. Process & Operations Toolkit
4. Control & Performance Toolkit
5. Visual Management & Adoption Toolkit
6. Quality, Safety & Compliance Toolkit
7. Culture, Training & Adoption Toolkit
8. Commercial & Client Relationship Toolkit
9. Economic & Financial Toolkit
10. Implementation Toolkit

**Herramientas Iniciales (MVP):**
*   FODA Ejecutivo
*   Matriz de Hallazgos y Oportunidades
*   Matriz RACI
*   Macroflujo Operativo
*   KPI Book
*   Roadmap 30/60/90

## 2. Reglas de Negocio (Core Rules)
1. **RBAC & Multi-tenancy:**
   - Todo pertenece a `organization_id` y `workspace_id`.
   - Solo `SYNER_CREW` puede crear y ejecutar herramientas completas.
   - `CLIENT_USER` solo responde inputs, sube evidencias y ve outputs en estado `APPROVED` o `CLIENT_VISIBLE`.
2. **Ciclo de Vida (ToolRun Status):**
   - `DRAFT` ➡️ `IN_PROGRESS` ➡️ `AI_GENERATED` ➡️ `CONSULTANT_REVIEW` ➡️ `APPROVED` ➡️ `CLIENT_SHARED` ➡️ `ARCHIVED`
3. **Visibilidad (Visibility):**
   - `INTERNAL_ONLY`, `CLIENT_SHARED`, `CLIENT_UPLOAD`, `DRAFT_INTERNAL`, `APPROVED`, `CLIENT_VISIBLE`
4. **Trazabilidad IA:** Toda respuesta generada por IA debe respaldarse obligatoriamente con `ToolEvidence` referenciando documentos de RAG.
5. **Convertibilidad:** Toda recomendación (`ToolRecommendation`) debe ser convertible en un ítem accionable (`RoadmapItem`).
6. **Exportación:** Exportación nativa a Markdown. Estructura modular lista para exportación a PDF/DOCX/PPTX.

---

## 3. Arquitectura y Modelo de Datos (Backend - SQLAlchemy)

La arquitectura debe basarse en modelos dinámicos, **cero hardcodeo** de herramientas.

### 3.1. Entidades de Base de Datos
*   **`ConsultingToolkit`**: Agrupador lógico (ej. "Strategic Diagnosis Toolkit").
*   **`ConsultingTool`**: Definición de la herramienta (ej. "FODA Ejecutivo").
*   **`ToolTemplate`**: Prompt o esquema JSON base de la herramienta.
*   **`ToolRun`**: Instancia de ejecución de la herramienta para un cliente.
    *   *Campos:* `organization_id`, `workspace_id`, `tool_id`, `created_by`, `status`, `visibility`.
*   **`ToolInput`**: Respuestas/Formularios ingresados por Syner o el Cliente.
*   **`ToolOutput`**: Resultado JSON o Markdown generado por la IA o el Consultor.
*   **`ToolEvidence`**: Archivos, links o fragmentos de documentos RAG que justifican el output.
*   **`ToolRecommendation`**: Sugerencias accionables derivadas del output.
*   **`ToolExport`**: Registro de archivos generados y exportados.

---

## 4. Estructura de APIs (FastAPI)

Implementar bajo `/api/` manteniendo el estándar RESTful:

*   `/api/toolkits`: GET, POST, PUT, DELETE
*   `/api/tools`: GET, POST, PUT, DELETE
*   `/api/tool-runs`:
    *   `POST /` (Inicia una ejecución)
    *   `GET /{id}` (Ver ejecución)
    *   `PATCH /{id}/status` (Cambiar de DRAFT a AI_GENERATED a APPROVED)
    *   `POST /{id}/inputs` (Cargar datos del cliente/consultor)
    *   `POST /{id}/execute` (Llama a IA para generar output)
*   `/api/tool-recommendations`:
    *   `POST /` (Crear recomendación)
    *   `POST /{id}/convert-to-roadmap` (Integra con `Cortex Roadmap`)
*   `/api/tool-exports`:
    *   `POST /generate-markdown`

---

## 5. Capa de Servicios (Services)

La lógica de negocio pesada debe vivir en servicios aislados (no en los routers):

*   `ConsultingToolkitService`: CRUD y listado de catálogos.
*   `ToolExecutionService`: Orquesta el paso de Inputs ➡️ Llama IA ➡️ Genera Output.
*   `ToolPromptBuilderService`: Construye el prompt dinámico inyectando `ToolInputs` al `ToolTemplate`.
*   `ToolEvidenceService`: Vincula documentos y referencias del Vault RAG con el resultado.
*   `ToolRecommendationService`: Filtra, califica y extrae recomendaciones.
*   `ToolToRoadmapService`: Toma una recomendación y la inyecta al módulo general de `Roadmap`.
*   `ToolExportService`: Motor de renderizado Markdown (y futuro PDF/DOCX).

---

## 6. Estructura UI (Frontend - React)

Diseño enterprise, sobrio, premium (Syner Theme). Evitar estilo "chat", priorizar estilo "dashboard ejecutivo de análisis".

### 6.1. Pantallas Principales (Pages)
*   `ToolkitsPage`: Catálogo visual de las 10 metodologías disponibles.
*   `ToolsPage`: Listado de herramientas dentro de un Toolkit.
*   `ToolRunPage`: Vista activa donde el cliente sube inputs/respuestas.
*   `ToolRunReviewPage`: Vista exclusiva `SYNER_CREW` para auditar el resultado IA, ajustar el texto y cambiar estado a `APPROVED`.

### 6.2. Componentes UI (Components)
*   `ToolOutputPreview`: Renderizado dinámico (Tablas para RACI, Cajas cuadradas para FODA, Gráficos para KPI Book).
*   `ToolRecommendationList`: Lista de sugerencias con un botón mágico de "+ Añadir a Roadmap".
*   `ToolExportButton`: Dropdown para seleccionar formato de salida (Markdown).
*   `StatusBadge`: Badge semántico para el ciclo de vida (`IN_PROGRESS`, `CONSULTANT_REVIEW`, `CLIENT_SHARED`).

---

## 7. Instrucciones de Implementación Inmediata

1.  Crea `app/models/toolkit.py` con los esquemas SQLAlchemy.
2.  Crea `app/schemas/toolkit.py` con los modelos Pydantic.
3.  Implementa la capa de servicios en `app/services/toolkit/`.
4.  Expón los endpoints en `app/routers/toolkits.py` y `tools.py`.
5.  Inyecta las rutas en `main.py`.
6.  Genera el Frontend base en `frontend/src/components/views/toolkit/`.
