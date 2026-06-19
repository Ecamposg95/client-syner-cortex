# Fase 3 — Plan de retrofit (PR2 endpoints) y alineación de datos (PR3)

> Documento-spec. **No incluye código.** Guía el cableado del motor de política
> (`app/policy/`) sobre los endpoints existentes (PR2) y la alineación de los
> datos al §5 del Task Pack (PR3), de forma segura sobre producción (org **BJX
> Motors** ya existe).

## 0. Contexto del motor (lo que ya existe)

- **`Action`** (16 acciones, `app/policy/actions.py`) — una por fila de la matriz §8.
- **`CAPABILITY_MATRIX`** (`app/policy/capabilities.py`) — `is_allowed(role, action)`; `ALLOW`/`DENY`/`CONDITIONAL`/`CLIENT_APPROVAL`, deny-by-default, `SUPERADMIN` por encima.
- **`ObjectType`** = {DOCUMENT, REPORT, TOOLRUN, ROADMAP_ITEM, RECOMMENDATION} con sus estados visibles a cliente (`app/policy/visibility.py`).
- **Deps FastAPI** (`app/policy/deps.py`):
  - `get_principal` — resuelve el `Principal` (memberships → `org_roles`).
  - `require_action(action)` — gate ejes 1+2 contra el header `X-Organization-ID`.
  - `scoped_query(db, model, principal, org_id, object_type=, owner_column=)` — query ya filtrada por org (eje 1) + visibilidad (eje 3).
- **`engine.authorize / can_view / can_access`** — los tres ejes.

**Guards legacy en uso hoy** (`app/dependencies.py`):
- `RoleChecker([...])` — RBAC ad-hoc por lista de strings; ya bloquea CLIENT_USER de asumir roles `SYNER_*`; `SUPERADMIN` bypassa.
- `get_organization_context` → `OrganizationUser` (valida membership; crew sin membership actúa como `SYNER_PARTNER`).
- `get_current_org_id` → `int` (igual, devuelve solo el id).
- `get_current_syner_crew` → solo crew/superadmin.
- `get_current_organization_id` — **DEPRECATED**, confía en el header sin validar membership.
- `apply_visibility_filter(query, user)` — filtro legacy con set divergente (`CLIENT_SHARED, CLIENT_UPLOAD, APPROVED, CLIENT_VISIBLE`), **nadie lo llama hoy** en los routers.

---

## PARTE 1 — Mapa de wiring (endpoints de negocio)

Convenciones de columnas:
- **Acción §8**: `require_action(Action.X)` que el endpoint debería exigir.
- **ObjectType**: tipo de visibilidad si devuelve objetos compartibles; `—` si no.
- **owner_column**: columna de propietario para estados own-only (ej. `CLIENT_UPLOAD`).
- **Guard actual**: dependencia real hoy.
- **⚠** = endpoint cliente-facing que hoy **NO filtra visibilidad** (riesgo de fuga de estado interno a un CLIENT_USER).

Se ignoran `/health` y `/auth/*` (signup, login, login-json, me, change-password — solo identidad).

### Router `documents` (`app/routers/documents.py`)

| Método+Path | Acción §8 (require_action) | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `POST /documents/upload` (l.87) | `UPLOAD_CLIENT_DOCS` (o `UPLOAD_INTERNAL_DOCS` según `visibility` destino) | DOCUMENT | `uploaded_by` (nuevo, ver PR3) | `RoleChecker(["CLIENT_OWNER","CLIENT_EXECUTIVE","CONSULTANT"])` | Rol `"CONSULTANT"` es **drift** (canónico = `SYNER_CONSULTANT`). Al crear, fijar `visibility=CLIENT_UPLOAD` y `uploaded_by=principal.user_id` cuando sube cliente; `INTERNAL_ONLY` cuando sube crew. |
| `GET /documents` (l.150) ⚠ | `VIEW_APPROVED_REPORTS` (lectura) | DOCUMENT | `uploaded_by` | `get_organization_context` | **FUGA**: `db.query(Document).filter(workspace_id==)` devuelve TODO, incl. `INTERNAL_ONLY`, a CLIENT_USER. Reemplazar por `scoped_query(db, Document, principal, org_id, object_type=DOCUMENT, owner_column=Document.uploaded_by)` y filtrar también por workspace. |
| `DELETE /documents/{id}` (l.169) | `UPLOAD_CLIENT_DOCS`/`CONFIGURE_MODULES` (no hay acción "delete" en §8; gate por edición) | — | — | `RoleChecker(["CLIENT_OWNER","CLIENT_EXECUTIVE"])` | Confirmar quién puede borrar; un cliente no debería poder borrar docs internos. Validar ownership/visibility antes de borrar (no solo org). |

### Router `chat` (`app/routers/chat.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `POST /chat/sessions` (l.12) | `CLIENT_LIMITED_CHAT` (cliente) / `USE_INTERNAL_RAG` (crew) | — | `user_id` | `get_organization_context` | Setear `visibility` coherente; el chat de cliente es CONDITIONAL (`CLIENT_LIMITED_CHAT`). |
| `GET /chat/sessions` (l.41) ⚠ | `CLIENT_LIMITED_CHAT` | ChatSession (no es ObjectType §8) | `user_id` | `get_organization_context` | **FUGA parcial**: lista TODAS las sesiones del workspace, incluidas las de crew (`INTERNAL_ONLY`) y de otros usuarios. Filtrar por `user_id == principal.user_id` para clientes (o por visibilidad). ChatSession no está en `ObjectType`; decidir si se modela o se filtra a mano. |
| `GET /chat/sessions/{id}/messages` (l.63) ⚠ | `CLIENT_LIMITED_CHAT` | — | (vía session) | `get_organization_context` | Validar que la sesión sea del caller antes de devolver mensajes. |
| `POST /chat/sessions/{id}/messages` (l.84) | `CLIENT_LIMITED_CHAT` / `USE_INTERNAL_RAG` | — | (vía session) | `get_organization_context` | El RAG interno sobre docs no debe exponer chunks de docs `INTERNAL_ONLY` a clientes — ver nota de retrieval en PR3 (riesgo transversal). |

### Router `documents`/`diagnoses` (`app/routers/diagnoses.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `POST /diagnoses` (l.12) | `RUN_TOOLS` / `EDIT_AI_OUTPUTS` | REPORT | — | `RoleChecker(["CLIENT_OWNER","CLIENT_EXECUTIVE","CONSULTANT"])` | Drift `"CONSULTANT"`. Diagnosis es generador de reporte; gate por acción de ejecución. |
| `GET /diagnoses/latest` (l.41) ⚠ | `VIEW_APPROVED_REPORTS` | REPORT | — | `get_organization_context` | **FUGA**: devuelve el último diagnosis sin mirar `visibility` (puede ser `INTERNAL_ONLY`/`DRAFT_INTERNAL`). Para clientes, filtrar a estados aprobados/compartidos vía `scoped_query(..., object_type=REPORT)`. |
| `GET /diagnoses/{id}` (l.64) ⚠ | `VIEW_APPROVED_REPORTS` | REPORT | — | `get_organization_context` | **FUGA**: detalle por id solo filtra por org, no por visibilidad. Añadir `can_view(principal, REPORT, diag.visibility)` antes de devolver. |

### Router `reports` (`app/routers/reports.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `GET /reports/executive-brief` (l.9) ⚠ | `VIEW_APPROVED_REPORTS` | REPORT | — | `get_organization_context` | **FUGA**: compila brief a partir del *último* Diagnosis + Roadmap del workspace **sin filtrar visibilidad**; un CLIENT_USER puede ver findings/SWOT internos no aprobados. Filtrar Diagnosis/Roadmap por estados visibles para clientes; añadir `require_action(VIEW_APPROVED_REPORTS)`. |

### Router `roadmaps` (`app/routers/roadmaps.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `GET /roadmaps/latest` (l.11) ⚠ | `VIEW_APPROVED_REPORTS` | ROADMAP_ITEM | — | `get_organization_context` | **FUGA**: devuelve el roadmap completo (todos los items, cualquier `visibility`). Filtrar items por estados visibles (`CLIENT_VISIBLE/CLIENT_ASSIGNED/COMPLETED`) para clientes. |
| `PATCH /roadmaps/items/{id}` (l.34) | `UPDATE_TASKS` | ROADMAP_ITEM | — | `RoleChecker(["CLIENT_OWNER","CLIENT_EXECUTIVE","CLIENT_MANAGER","CONSULTANT"])` | Drift `"CONSULTANT"`. `UPDATE_TASKS` es CONDITIONAL para CLIENT_OWNER/EXECUTIVE; un cliente solo debería tocar items visibles/asignados. Validar `can_view` sobre el item antes de mutar. |

### Router `workspaces` (`app/routers/workspaces.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `GET /workspaces` (l.11) | — (lista por org) | — | — | `get_organization_context` | Org-scoped OK. Workspaces no son objetos compartibles per-state; sin cambio de visibilidad. |
| `POST /workspaces` (l.22) | `CREATE_WORKSPACE` | — | — | `RoleChecker(["CLIENT_OWNER","CLIENT_EXECUTIVE","CONSULTANT"])` | Drift `"CONSULTANT"`. **Nota §8**: `CREATE_WORKSPACE` es ALLOW solo para crew (ADMIN/PARTNER/CONSULTANT) — hoy permite a CLIENT_OWNER/EXECUTIVE. **Decisión de negocio pendiente**: cerrar a crew o documentar excepción. |

### Router `organizations` (`app/routers/organizations.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `GET /organizations` (l.11) | — (identidad) | — | — | `get_current_active_user` | Lista las orgs del usuario; crew ve todas. OK, no objeto §8. |
| `POST /organizations` (l.46) | `CREATE_CLIENT` | — | — | `get_current_active_user` | **§8**: `CREATE_CLIENT` es ALLOW solo `SYNER_ADMIN`. Hoy cualquier usuario autenticado crea org y se vuelve `CLIENT_OWNER` (flujo self-signup). **Decisión**: mantener como "org personal" (no es cliente formal) o gatear con `CREATE_CLIENT`. Aclarar semántica `organization_type`. |
| `GET /organizations/users` (l.75) | `CONFIGURE_MODULES` (admin de org) | — | — | `RoleChecker(["CLIENT_OWNER","CLIENT_EXECUTIVE","CONSULTANT"])` | Drift `"CONSULTANT"`. |
| `POST /organizations/users` (l.99) | `CONFIGURE_MODULES` | — | — | `RoleChecker(["CLIENT_OWNER"])` | Validar que el `role` invitado pertenezca al set canónico (hoy acepta cualquier string). |

### Router `toolkit` (`app/routers/toolkit.py`) — **el de mayor riesgo**

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `GET /toolkits` (l.25) | — (catálogo) | — | — | **ninguno** (solo `get_db`) | Sin auth. Catálogo global; al menos exigir usuario autenticado. |
| `POST /toolkits` (l.29) | `CONFIGURE_MODULES` | — | — | **ninguno** | **Sin auth** — cualquiera crea toolkits. Gatear a crew/admin. |
| `GET /toolkits/{id}/tools` (l.35) | — | — | — | **ninguno** | Sin auth; añadir principal. |
| `GET /tools/{id}` (l.43) | — | — | — | **ninguno** | Sin auth. |
| `POST /tool-runs` (l.69) | `RUN_TOOLS` | — | `created_by` | `get_current_org_id` + `get_current_user` | Gatear con `RUN_TOOLS` (CONDITIONAL para ANALYST/PM). |
| `POST /tool-runs/{id}/execute` (l.84) ⚠ | `RUN_TOOLS` | — | `created_by` | **ninguno** (solo `get_db`) | **Sin auth ni org-scope** — ejecutable por id desde cualquier org. Riesgo grave: añadir principal + verificar org del run. |
| `GET /tool-runs/{id}` (l.91) ⚠ | `VIEW_APPROVED_REPORTS` | TOOLRUN | `created_by` | **ninguno** | **FUGA + sin scope**: devuelve run con `visibility` cruda por id, sin verificar org ni visibilidad. Cargar vía `scoped_query(..., object_type=TOOLRUN)` y `can_view`. |
| `PATCH /tool-runs/{id}/status` (l.123) ⚠ | `SHARE_WITH_CLIENT` (al pasar a CLIENT_SHARED) / `APPROVE_DELIVERABLES` | TOOLRUN | `created_by` | **ninguno** | **Sin auth**: cualquiera cambia el status (incluido `CLIENT_SHARED`) de cualquier run. Compartir con cliente es `SHARE_WITH_CLIENT` (solo crew). Gate crítico. |
| `POST /tool-runs/{id}/inputs` (l.135) | `RUN_TOOLS` | — | `uploaded_by` | `get_current_user` (sin org) | Falta validar org del run. |
| `POST /tool-runs/{id}/outputs` (l.148) ⚠ | `EDIT_AI_OUTPUTS` | — | — | **ninguno** | **Sin auth**: cualquiera inyecta outputs y fuerza `AI_GENERATED`. Gatear con `EDIT_AI_OUTPUTS`. |
| `POST /tool-runs/{id}/recommendations` (l.162) ⚠ | `EDIT_AI_OUTPUTS` | RECOMMENDATION | — | **ninguno** | **Sin auth**. |
| `GET /tool-runs/{id}/recommendations` (l.170) ⚠ | `VIEW_APPROVED_REPORTS` | RECOMMENDATION | — | **ninguno** | **Sin auth + sin filtro visibilidad** de recomendaciones. |
| `POST /tool-runs/{id}/export-markdown` (l.176) | `VIEW_APPROVED_REPORTS` | TOOLRUN | `created_by` | `get_current_user` (sin org) | Validar org + visibilidad del run antes de exportar. |

### Router `clevel` (`app/routers/clevel.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `GET /clevel/engagements` (l.93) ⚠ | `VIEW_APPROVED_REPORTS` | REPORT-like | — | `get_current_org_id` | Org-scoped, pero sin estado de visibilidad — los engagements/findings son material interno de consultoría. **Riesgo de exposición de findings/risks crudos a clientes.** Definir visibilidad o restringir a crew. |
| `GET /clevel/engagements/{id}/findings` (l.97) ⚠ | `VIEW_INTERNAL_PLAYBOOKS` | — | — | `get_current_org_id` | Findings = material interno; probablemente solo crew. |
| `GET /clevel/engagements/{id}/initiatives` (l.104) ⚠ | `VIEW_APPROVED_REPORTS` | — | — | `get_current_org_id` | Idem. |
| `GET /clevel/engagements/{id}/deliverables` (l.111) ⚠ | `VIEW_APPROVED_REPORTS` | REPORT | — | `get_current_org_id` | Deliverable tiene `status` (DRAFT/IN_REVIEW/DELIVERED/APPROVED) — filtrar a APPROVED/DELIVERED para clientes. |
| `GET /clevel/risks` (l.118) ⚠ | `VIEW_INTERNAL_PLAYBOOKS` | — | — | `get_current_org_id` | Riesgos = interno; restringir a crew. |
| `GET /clevel/decisions` (l.122) ⚠ | `VIEW_APPROVED_REPORTS` | — | — | `get_current_org_id` | Decisiones se exponen al cliente para resolución; OK pero validar. |
| `PATCH /clevel/decisions/{id}` (l.136) | `APPROVE_DELIVERABLES` (CLIENT_APPROVAL para owner/exec) | — | — | `RoleChecker(_DECISION_ROLES)` | `_DECISION_ROLES` ya usa nombres canónicos `SYNER_*`. Mapea bien a la lane `CLIENT_APPROVAL`. |

### Router `insights` (`app/routers/insights.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `GET /insights` (l.105) ⚠ | `VIEW_APPROVED_REPORTS` | RECOMMENDATION-like | — | `get_current_org_id` | Insights no tienen `visibility`; son material de priorización interno. **Riesgo**: cliente ve todos los insights crudos. Definir visibilidad o restringir. |
| `GET /insights/matrix` (l.130) ⚠ | `VIEW_APPROVED_REPORTS` | — | — | `get_current_org_id` | Idem. |
| `GET /insights/critical-alarms` (l.154) ⚠ | `VIEW_INTERNAL_PLAYBOOKS` | — | — | `get_current_org_id` | Alarmas críticas = sensibles; probablemente solo crew/exec. |
| `POST /insights/generate` (l.172) | `RUN_TOOLS`/`EDIT_AI_OUTPUTS` | — | — | `RoleChecker(_MANAGE_ROLES)` | `_MANAGE_ROLES` = `["SYNER_PARTNER","SYNER_CONSULTANT"]` canónicos OK. |
| `POST /insights` (l.182) | `EDIT_AI_OUTPUTS` | — | — | `RoleChecker(_MANAGE_ROLES)` | OK. |
| `PATCH /insights/{id}` (l.212) | `UPDATE_TASKS` | — | — | `RoleChecker(_TRIAGE_ROLES)` | `_TRIAGE_ROLES` canónicos OK. |

### Router `raci` (`app/routers/raci.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `GET /raci/matrices` (l.195) | — (org-scoped) | — | — | `get_current_org_id` | Sin estado de visibilidad; org-scoped OK. |
| `GET /raci/matrices/{id}` (l.218) | — | — | — | `get_current_org_id` | OK (valida org). |
| `POST /raci/matrices` (l.227) | `CONFIGURE_MODULES`/`UPDATE_TASKS` | — | — | `RoleChecker(_EDIT_ROLES)` | `_EDIT_ROLES` canónicos OK. |
| `DELETE /raci/matrices/{id}` (l.243) | `CONFIGURE_MODULES` | — | — | `RoleChecker(_EDIT_ROLES)` | OK. |
| `POST .../roles` (l.255), `POST .../processes` (l.276), `DELETE /raci/roles/{id}` (l.295), `DELETE /raci/processes/{id}` (l.314), `PATCH .../cell` (l.333) | `UPDATE_TASKS` | — | — | `RoleChecker(_EDIT_ROLES)` | Todos validan org vía `_get_owned_matrix`/join. OK. |

### Router `kpi` (`app/routers/kpi.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `GET /kpi` (l.34) | — (org-scoped) | — | — | `get_current_org_id` | OK. Sin visibilidad. |
| `POST /kpi` (l.38) | `UPDATE_TASKS` | — | — | `get_current_org_id` | **No hay RoleChecker**: cualquier miembro (incl. CLIENT_VIEWER) crea KPIs. Gatear con acción. |
| `PUT /kpi/{id}` (l.46) | `UPDATE_TASKS` | — | — | `get_current_org_id` | Idem, gatear. |
| `DELETE /kpi/{id}` (l.57) | `UPDATE_TASKS` | — | — | `get_current_org_id` | Idem, gatear. |

### Router `agents` (`app/routers/agents.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `POST /agents/{id}/chat` (l.12) | `USE_INTERNAL_RAG` / `CLIENT_LIMITED_CHAT` | — | — | `get_current_org_id` | Valida org. Distinguir cliente (CONDITIONAL) vs crew. |

### Router `portal` (`app/routers/portal.py`)

| Método+Path | Acción §8 | ObjectType | owner_column | Guard actual | Nota de retrofit |
|---|---|---|---|---|---|
| `GET /portal/summary` (l.14) ⚠ | `VIEW_APPROVED_REPORTS` | REPORT/ROADMAP agregado | — | `get_organization_context` | **Riesgo de agregación**: `build_summary` arma un resumen sobre varias fuentes; auditar que NO incluya estados internos para clientes. Es la superficie cliente-facing #1. |

### Router `admin` (`app/routers/admin.py`) — crew-only

| Método+Path | Acción §8 | Guard actual | Nota de retrofit |
|---|---|---|---|
| `GET /admin/clients` (l.89) | `CREATE_CLIENT`/`CONFIGURE_MODULES` | `get_current_syner_crew` | OK crew. |
| `POST /admin/clients` (l.107) | `CREATE_CLIENT` | `get_current_syner_crew` | §8 = solo `SYNER_ADMIN`; hoy cualquier crew. Estrechar a admin si se desea. |
| `GET /admin/clients/{id}` (l.131) | `CONFIGURE_MODULES` | `get_current_syner_crew` | OK. |
| `POST /admin/clients/{id}/users` (l.167) | `CONFIGURE_MODULES` | `get_current_syner_crew` | `_create_client_user` valida `role ∈ CLIENT_ROLES` pero el set **omite `CLIENT_CONTRIBUTOR`** (ver PR3). |
| `PUT /admin/clients/{id}/modules` (l.178) | `CONFIGURE_MODULES` | `get_current_syner_crew` | §8 solo `SYNER_ADMIN`. |
| `POST /admin/clients/{id}/workspaces` (l.203) | `CREATE_WORKSPACE` | `get_current_syner_crew` | OK. |

### Router `surveys` (`app/routers/surveys.py`) — crew-only

| Método+Path | Guard actual | Nota |
|---|---|---|
| Todos (`/surveys`, `/campaigns`, results, status) | `get_current_syner_crew` (+ `_optional_org_id`) | Crew-only; sin objeto §8 cliente-facing. OK. `_optional_org_id` permite listar cross-org a crew (consistente). |

### Router `public_surveys` (`app/routers/public_surveys.py`) — público por token

| Método+Path | Guard actual | Nota |
|---|---|---|
| `GET /public/surveys/{token}` (l.28), `POST .../responses` (l.71) | **ninguno** (público, por token + ventana) | Intencional: encuesta pública. Fuera del modelo de roles. Validar solo rate-limit/ventana (ya lo hace). |

### Router `audit` (`app/routers/audit.py`)

| Método+Path | Acción §8 | Guard actual | Nota de retrofit |
|---|---|---|---|
| `GET /audit` (l.11) | `VIEW_AUDIT` | `RoleChecker(["CLIENT_OWNER","CLIENT_EXECUTIVE","CONSULTANT"])` | **§8**: `VIEW_AUDIT` es ALLOW solo `SYNER_ADMIN` (CONDITIONAL para PARTNER). Hoy lo ven CLIENT_OWNER/EXECUTIVE — **divergencia fuerte de política**. Reemplazar por `require_action(VIEW_AUDIT)`. Drift `"CONSULTANT"`. |

### Resumen de la Parte 1

- **Endpoints de negocio mapeados:** **~54** (excluye `/health` y 5 de `/auth`).
- **Marcados ⚠ (fuga / sin guard cliente-facing):** **~24**.
  - **Sin auth alguno (toolkit):** 9 endpoints (`POST/GET toolkits`, `tools`, y casi todo `/tool-runs/*` incl. `execute`, `status`, `outputs`, `recommendations`) — el clúster más crítico.
  - **Fuga de visibilidad (devuelven `visibility`/estado interno sin filtrar a CLIENT_USER):** `GET /documents`, `GET /diagnoses/latest`, `GET /diagnoses/{id}`, `GET /reports/executive-brief`, `GET /roadmaps/latest`, `GET /tool-runs/{id}`, chat sessions/messages, y todo `/clevel/*` + `/insights/*` (sin columna `visibility`).
- **Divergencia de política directa:** `GET /audit` expuesto a roles cliente; `CREATE_WORKSPACE`/`CREATE_CLIENT` con guards más laxos que §8.
- **Drift de strings de rol:** `"CONSULTANT"` (en vez de `SYNER_CONSULTANT`) en `documents`, `diagnoses`, `roadmaps`, `workspaces`, `organizations`, `audit`. **Estos `RoleChecker(["...CONSULTANT"])` hoy NO matchean a un crew con rol canónico `SYNER_CONSULTANT`** — se "salvan" solo porque crew entra como `SYNER_PARTNER` por defecto o es superadmin.

**Patrón de retrofit recomendado (PR2):** sustituir cada `RoleChecker([...])` por `require_action(Action.X)` y cada `db.query(Model)` cliente-facing por `scoped_query(..., object_type=..., owner_column=...)`, resolviendo el `Principal` con `get_principal`. Empezar por el clúster `toolkit` (sin auth) y las fugas de `reports/diagnoses/roadmaps/documents`.

---

## PARTE 2 — Plan PR3 (alineación de datos a §5)

### 2.1 ENUMS / ROLES

**Estado actual:** `User.user_type` y `OrganizationUser.role` son `Column(String)`. Faltan en datos/seed los roles canónicos: **`SYNER_PM`, `SYNER_VIEWER`, `CLIENT_CONTRIBUTOR`** (existen en `app/policy/roles.py` y en la matriz, pero no se crean ni se validan en escritura).

**Estrategia recomendada: mantener STRING + validación contra el set canónico** (`app/policy/roles.ALL_ROLES`), **no migrar a Enum PG**. Justificación:

1. **No rompe datos prod.** BJX y los crew ya tienen filas con strings; un `Enum` PG nativo exigiría `ALTER TYPE`/recreación y validación previa de todos los valores existentes (frágil sobre prod).
2. **Flexibilidad de evolución.** Añadir un rol nuevo a un Enum PG es un `ALTER TYPE ... ADD VALUE` no transaccional y no reversible limpiamente; con STRING + validación en código basta editar `roles.py`.
3. **La verdad ya vive en código.** `CAPABILITY_MATRIX` y `ALL_ROLES` son la fuente de verdad; el Enum PG duplicaría esa verdad en el esquema.
4. **Defensa en profundidad ya existe.** `RoleChecker` ya impide que un `CLIENT_USER` asuma `SYNER_*`.

**Acción concreta:** añadir validación en *toda escritura de rol* (no a nivel de columna): rechazar roles fuera de `ALL_ROLES`; opcionalmente un `CHECK constraint` PG laxo (lista de strings) como red de seguridad — reversible y no destructivo.

**Lugares que crean/asignan roles y deben actualizarse:**

| Archivo | Qué hace | Cambio |
|---|---|---|
| `app/routers/admin.py` `CLIENT_ROLES` (l.19) | `{"CLIENT_OWNER","CLIENT_EXECUTIVE","CLIENT_MANAGER","CLIENT_VIEWER"}` | **Falta `CLIENT_CONTRIBUTOR`.** Reemplazar por `R.CLIENT_ROLES` de `policy/roles.py`. |
| `app/routers/organizations.py` `POST /users` (l.124) | inserta `role=member_in.role` sin validar | Validar contra `ALL_ROLES`; bloquear `SYNER_*` desde flujo cliente. |
| `app/routers/auth.py` signup (l.50) | `role="CLIENT_OWNER"` | OK (canónico). |
| `app/routers/organizations.py` create_org (l.68) | `role="CLIENT_OWNER"` | OK. |
| `app/scripts/seed_crew.py` (l.32-34, 90) | crea `SYNER_PARTNER` para 3 crew | **Sembrar también `SYNER_PM`/`SYNER_VIEWER`** si el negocio los requiere; usar constantes. |
| `app/scripts/bootstrap_admin.py` (l.87) | `role="SUPERADMIN"` | OK. |
| `app/scripts/seed_bjx_client.py` (l.79), `app/seed_bjx.py` (l.95,101), `app/seed/seed_clevel_bjx.py` | `CLIENT_OWNER`/`CLIENT_EXECUTIVE` | OK; migrar a constantes para evitar drift. |
| `app/dependencies.py` (mocks crew → `SYNER_PARTNER`, superadmin → `SUPERADMIN`) | strings canónicos | OK; usar constantes. |

### 2.2 VISIBILIDADES — divergencias reales vs §5 canónico

Estados canónicos esperados por el motor (`app/policy/visibility.py`):

| ObjectType | Estados visibles a cliente (canónico) |
|---|---|
| DOCUMENT | `CLIENT_SHARED`, `CLIENT_UPLOAD` (own-only) |
| REPORT | `CLIENT_SHARED` |
| TOOLRUN | `CLIENT_SHARED` |
| ROADMAP_ITEM | `CLIENT_VISIBLE`, `CLIENT_ASSIGNED`, `COMPLETED` |
| RECOMMENDATION | `SHARED`, `EXECUTIVE_ONLY`, `TASK_VISIBLE` |

**Valores reales hoy en los modelos:**

| Modelo (archivo) | Columna | Valores reales | Mapea a ObjectType | Divergencia |
|---|---|---|---|---|
| `Document` (models.py l.110) | `visibility` String | `INTERNAL_ONLY`, `CLIENT_SHARED`, `CLIENT_UPLOAD` | DOCUMENT | **Alineado.** Falta `uploaded_by` para own-only (ver 2.3). |
| `Diagnosis` (l.171) | `visibility` String | `INTERNAL_ONLY`, `DRAFT_INTERNAL`, `APPROVED`, `CLIENT_VISIBLE` | REPORT | **DIVERGE**: REPORT canónico solo expone `CLIENT_SHARED`. Hoy usa `APPROVED`/`CLIENT_VISIBLE`. **Mapeo:** `APPROVED→CLIENT_SHARED`, `CLIENT_VISIBLE→CLIENT_SHARED`; `INTERNAL_ONLY`/`DRAFT_INTERNAL` se quedan (internos). |
| `Roadmap` (l.203) | `visibility` String | `INTERNAL_ONLY`, `DRAFT_INTERNAL`, `APPROVED`, `CLIENT_VISIBLE` | (contenedor) | El motor mira `RoadmapItem`, no `Roadmap`. Mantener pero documentar. |
| `RoadmapItem` (l.222) | `visibility` String | `INTERNAL_ONLY`, `DRAFT_INTERNAL`, `APPROVED`, `CLIENT_VISIBLE` | ROADMAP_ITEM | **DIVERGE parcial**: canónico = `CLIENT_VISIBLE`/`CLIENT_ASSIGNED`/`COMPLETED`. Tiene `CLIENT_VISIBLE` ✓ pero NO `CLIENT_ASSIGNED`/`COMPLETED` y sí `APPROVED` extra. **Mapeo:** `APPROVED→CLIENT_VISIBLE`; añadir `CLIENT_ASSIGNED`/`COMPLETED` como estados nuevos (status `DONE`→ podría reflejarse como `COMPLETED` visible). |
| `ChatSession`/`ChatMessage` (l.140,157) | `visibility` String | `INTERNAL_ONLY` (default) | — (no en ObjectType) | No hay ObjectType para chat; el filtrado será por `user_id`, no por estado. Decidir si se modela o se documenta. |
| `ToolRun` (toolkit.py l.69) | `visibility` **Enum(`Visibility`)** | `INTERNAL_ONLY`, `CLIENT_SHARED`, `CLIENT_UPLOAD`, `DRAFT_INTERNAL`, `APPROVED`, `CLIENT_VISIBLE` | TOOLRUN | **Alineado** para `CLIENT_SHARED`. ⚠ **Es Enum PG**, no String — `scoped_query` compara contra strings; verificar que `model.visibility.in_({"CLIENT_SHARED"})` funcione contra el Enum (puede requerir comparar por `.value` o `native_enum=False`). |
| `ToolRun` (toolkit.py l.68) | `status` **Enum(`ToolRunStatus`)** | `DRAFT`, `IN_PROGRESS`, `AI_GENERATED`, `CONSULTANT_REVIEW`, `APPROVED`, `CLIENT_SHARED`, `ARCHIVED` | (ReportStatus §5) | `status` y `visibility` solapan semánticamente (`CLIENT_SHARED` en ambos). Definir cuál gobierna la visibilidad del run (recomendado: `visibility`). |
| `survey.py` (l.131) | `visibility` String | default `CLIENT_UPLOAD` | (respuestas) | Respuestas de encuesta tratadas como subida de cliente; revisar si entra al modelo DOCUMENT o queda aparte. |
| `clevel` Deliverable (clevel.py l.92) | `status` String | `DRAFT`, `IN_REVIEW`, `DELIVERED`, `APPROVED` | ReportStatus §5 | No tiene `visibility`. Para exponer a cliente, mapear `DELIVERED/APPROVED→CLIENT_SHARED`. |
| `Insight` (insight.py) | `status` Enum | `NEW`,`ACKNOWLEDGED`,`IN_PROGRESS`,`RESOLVED`,`DISMISSED` | — | Sin `visibility`. Si se expone a cliente, requiere columna de visibilidad (ver 2.3 Recommendation). |

**`ReportStatus` / `ToolRunStatus` / `RecVisibility` / `RoadmapItemVis` canónicos (§5) — gaps:**
- No existe modelo `Report` propio con `ReportStatus` (Diagnosis hace de proxy). Ver 2.3.
- `RecVisibility` (`SHARED`/`EXECUTIVE_ONLY`/`TASK_VISIBLE`) no existe en ningún modelo; las recomendaciones viven en `ToolRecommendation` (sin visibilidad) y no hay `Recommendation` standalone. Ver 2.3.
- `RoadmapItemVis` canónico añade `CLIENT_ASSIGNED`/`COMPLETED`, ausentes hoy.

**Mapeo de migración de datos (data backfill, NO romper BJX):**

```
Document.visibility:        sin cambios (ya alineado). Backfill uploaded_by (ver 2.3).
Diagnosis.visibility:       'CLIENT_VISIBLE' -> 'CLIENT_SHARED'
                            'APPROVED'       -> 'CLIENT_SHARED'
                            'INTERNAL_ONLY' / 'DRAFT_INTERNAL' -> (sin cambio)
RoadmapItem.visibility:     'CLIENT_VISIBLE' -> (sin cambio)
                            'APPROVED'       -> 'CLIENT_VISIBLE'
                            (status 'DONE' + visible) -> opcional set 'COMPLETED'
                            'INTERNAL_ONLY' / 'DRAFT_INTERNAL' -> (sin cambio)
ToolRun.visibility (Enum):  ya alineado; verificar comparación string en scoped_query.
clevel.Deliverable.status:  no es visibility; añadir columna visibility y derivar
                            'DELIVERED'/'APPROVED' -> 'CLIENT_SHARED', resto INTERNAL_ONLY.
```

> ⚠ El backfill debe ser **idempotente** y ejecutarse en datos de BJX. Antes de migrar `APPROVED→CLIENT_SHARED`, confirmar con el negocio que todo `APPROVED` debe ser visible al cliente (si no, dejar `APPROVED` como interno y exigir un paso explícito de "share").

### 2.3 MODELOS FALTANTES

| Modelo | Tipo | Tabla | Campos clave | FKs | Notas |
|---|---|---|---|---|---|
| **`Report`** | **Nuevo** | `reports` | `id`, `title`, `content_json`/`markdown`, `status` (ReportStatus: `DRAFT`/`IN_REVIEW`/`APPROVED`/`CLIENT_SHARED`/`ARCHIVED`), `visibility` (REPORT: `INTERNAL_ONLY`/`CLIENT_SHARED`), `created_by` | `organization_id`→organizations, `workspace_id`→workspaces, `created_by`→users | Reporte propio en vez de reusar Diagnosis como proxy. Diagnosis puede *generar* un Report. |
| **`WorkspaceUser`** | **Nuevo** | `workspace_users` | `id`, `role` (rol dentro del workspace, validado contra `ALL_ROLES`), `created_at` | `workspace_id`→workspaces, `user_id`→users | Membership a nivel workspace (eje 1 fino). Hoy el scope es solo org-level. Permite asignaciones por workspace. |
| **`Comment`** | **Nuevo (polimórfico)** | `comments` | `id`, `body`, `target_type` (DOCUMENT/REPORT/TOOLRUN/ROADMAP_ITEM/RECOMMENDATION), `target_id`, `visibility`, `created_at` | `organization_id`→organizations, `author_id`→users | Polimórfico vía (`target_type`,`target_id`). Visibilidad propia para comentarios internos vs compartidos. |
| **`Recommendation`** | **Nuevo (standalone)** | `recommendations` | `id`, `title`, `description`, `visibility` (`RecVisibility`: `INTERNAL`/`SHARED`/`EXECUTIVE_ONLY`/`TASK_VISIBLE`), `priority`, `status` | `organization_id`→organizations, `workspace_id`→workspaces, `source_run_id`→toolkit_runs (nullable), `created_by`→users | Reemplaza/complementa `ToolRecommendation` (que vive atado a un run y sin visibilidad). `EXECUTIVE_ONLY` ya soportado por el motor (`CLIENT_EXECUTIVE_TIER`). |
| **`Document.uploaded_by`** | **Alteración** | `documents` (add col) | `uploaded_by` Integer nullable | →users | **Necesario para own-only de `CLIENT_UPLOAD`**: `scoped_query` exige `owner_column` para que un cliente vea solo SU subida. Hoy no se persiste quién subió. Backfill: nullable; filas viejas quedan NULL (no own-visible hasta reasignar). |

### 2.4 MIGRACIÓN ALEMBIC — secuencia (plan, sin código)

**Head actual:** `b7f3a9c1d2e4` (add_raci_matrix_tables). Cadena: `8b1354471d93` → `27fe7022dc62` → `b7f3a9c1d2e4`.

Secuencia propuesta (cada paso = una revisión, `down_revision` encadenado, **aditivo y reversible**; el riesgo se concentra solo en los backfills de datos, separados de los DDL):

1. **`m1_add_document_uploaded_by`** (down: `b7f3a9c1d2e4`)
   - DDL: `ADD COLUMN documents.uploaded_by INTEGER NULL` + FK→users.
   - Aditivo, reversible (`DROP COLUMN`). No toca datos. **Bajo riesgo.**

2. **`m2_create_reports`**
   - DDL: crea tabla `reports`. Reversible (`DROP TABLE`). Sin datos.

3. **`m3_create_recommendations`**
   - DDL: crea tabla `recommendations`. Reversible. Sin datos.

4. **`m4_create_workspace_users`**
   - DDL: crea `workspace_users`. Reversible. Sin datos.

5. **`m5_create_comments`**
   - DDL: crea `comments` (polimórfico). Reversible. Sin datos.

6. **`m6_add_visibility_clevel_deliverable`** (opcional, si se expone a cliente)
   - DDL: `ADD COLUMN clevel_deliverables.visibility String DEFAULT 'INTERNAL_ONLY'`.
   - Aditivo. **Bajo riesgo.**

7. **`m7_backfill_visibility_states`** — **paso de DATOS, mayor cuidado**
   - `UPDATE diagnoses SET visibility='CLIENT_SHARED' WHERE visibility IN ('APPROVED','CLIENT_VISIBLE')`
   - `UPDATE roadmap_items SET visibility='CLIENT_VISIBLE' WHERE visibility='APPROVED'`
   - (opcional) `UPDATE clevel_deliverables SET visibility='CLIENT_SHARED' WHERE status IN ('DELIVERED','APPROVED')`
   - **Idempotente** (re-ejecutable sin efecto extra), **reversible** vía mapa inverso registrado. Ejecutar fuera de horas pico; respaldar BJX antes.
   - ⚠ **Gate de negocio**: solo correr si se confirma que `APPROVED ⇒ visible al cliente`. Si no, omitir este backfill y mover la visibilidad por un endpoint explícito de "share".

8. **`m8_role_check_constraint`** (opcional, defensa)
   - DDL: `CHECK constraint` laxo sobre `organization_users.role` contra la lista canónica de strings (o índice/trigger). Reversible (`DROP CONSTRAINT`).
   - **Pre-requisito**: validar primero que no haya filas con roles fuera de `ALL_ROLES` (query de auditoría); si las hay, normalizar antes (ej. `"CONSULTANT"→"SYNER_CONSULTANT"` si existiera en datos).

**Principios:**
- DDL aditivo y datos en revisiones **separadas** (un fallo de backfill no bloquea el esquema; rollback selectivo).
- Toda columna nueva **nullable** o con default seguro (no `NOT NULL` sin default sobre tablas con datos).
- Cada `downgrade` definido (drop col/table, update inverso).
- Ejecutar en staging contra una copia de BJX antes de prod.

---

## Apéndice — los 3-4 cambios de mayor riesgo/impacto (PR3)

1. **Backfill de visibilidad de `Diagnosis`/`RoadmapItem` (`APPROVED`/`CLIENT_VISIBLE`→`CLIENT_SHARED`/`CLIENT_VISIBLE`)** sobre datos vivos de BJX. Riesgo de exponer de más o de menos. Requiere gate de negocio explícito.
2. **`Document.uploaded_by`** + backfill: sin él, el own-only de `CLIENT_UPLOAD` no funciona y `scoped_query` deja las subidas viejas (NULL) invisibles para su dueño cliente.
3. **`ToolRun.visibility`/`status` son Enum PG, no String**: `scoped_query` compara contra strings — validar la comparación (o normalizar a `native_enum=False`) o el filtro de toolkit fallará silenciosamente (riesgo de fuga o de resultado vacío).
4. **`Recommendation` standalone con `RecVisibility`**: hoy las recomendaciones (`ToolRecommendation`) no tienen visibilidad y se devuelven sin filtrar; crear el modelo y migrar es prerequisito para no filtrar recomendaciones internas a clientes.
