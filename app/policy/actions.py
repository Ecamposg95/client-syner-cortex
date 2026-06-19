"""The set of authorizable actions — one per row of the permission matrix
(Task Pack §8). Endpoints ask the policy engine "may this principal perform
ACTION?" rather than hardcoding role lists.
"""
import enum


class Action(str, enum.Enum):
    CREATE_CLIENT = "create_client"               # Crear cliente
    CREATE_WORKSPACE = "create_workspace"         # Crear workspace
    UPLOAD_INTERNAL_DOCS = "upload_internal_docs" # Subir docs internos
    UPLOAD_CLIENT_DOCS = "upload_client_docs"     # Subir docs cliente
    USE_INTERNAL_RAG = "use_internal_rag"         # Usar RAG interno
    CLIENT_LIMITED_CHAT = "client_limited_chat"   # Chat cliente limitado
    RUN_TOOLS = "run_tools"                        # Ejecutar herramientas
    EDIT_AI_OUTPUTS = "edit_ai_outputs"           # Editar outputs IA
    APPROVE_DELIVERABLES = "approve_deliverables"  # Aprobar entregables
    SHARE_WITH_CLIENT = "share_with_client"        # Compartir con cliente
    VIEW_APPROVED_REPORTS = "view_approved_reports"  # Ver reportes aprobados
    CREATE_ROADMAP = "create_roadmap"             # Crear roadmap
    UPDATE_TASKS = "update_tasks"                  # Actualizar tareas
    VIEW_INTERNAL_PLAYBOOKS = "view_internal_playbooks"  # Ver playbooks internos
    VIEW_AUDIT = "view_audit"                      # Ver auditoría
    CONFIGURE_MODULES = "configure_modules"        # Configurar módulos
