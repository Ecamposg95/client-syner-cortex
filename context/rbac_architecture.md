# Role-Based Access Control (RBAC) Architecture

Syner Hub implements a strict dual-user model separating internal consulting staff from external clients. This prevents accidental data leaks and ensures clients only see finalized, approved deliverables and tasks.

## User Types

1. **`SYNER_CREW`**:
   - Internal employees and partners of Grupo Syner.
   - Operators of the platform.
   - Can manage clients, create workspaces, upload raw documents, run AI agents for diagnosis, and generate roadmaps and reports.
   - Have exclusive access to internal playbooks, prompts, and global audit logs.

2. **`CLIENT_USER`**:
   - External users belonging to a client company.
   - Can only access their own organization (`organization_type = "CLIENT"`).
   - Can view shared documents, approved reports, visible roadmaps, and assigned tasks.
   - Cannot see other clients, internal config, or unapproved drafts.

## Roles Matrix

Roles are defined in the `organization_users` table, linking a user to an organization.

### Internal Roles (for `SYNER_CREW` only)
- `SUPERADMIN`: Global access. Can manage the entire platform.
- `SYNER_ADMIN`: Can manage internal Syner operations, billing, and global settings.
- `SYNER_PARTNER`: Lead consultant on an account. Approves deliverables before client visibility.
- `SYNER_CONSULTANT`: Standard consultant. Generates reports, manages roadmaps, runs AI agents.
- `SYNER_ANALYST`: Junior consultant. Can upload documents and run preliminary analysis (read/draft access).

### External Roles (for `CLIENT_USER` only)
- `CLIENT_OWNER`: Top executive at the client company. Has full access to the client portal and can invite other client users.
- `CLIENT_MANAGER`: Mid-level manager. Can view reports, manage tasks assigned to their team.
- `CLIENT_VIEWER`: Read-only access to approved dashboards and reports.

## Object-Level Visibility

To handle data isolation within a shared workspace, all core entities (Documents, Reports, Tasks, Recommendations) implement a `visibility` column.

- `INTERNAL_ONLY`: Strictly for `SYNER_CREW`. E.g., raw financial data, internal notes, AI reasoning traces.
- `CLIENT_SHARED`: Shared with the client by the Syner Crew.
- `CLIENT_UPLOAD`: Uploaded directly by a `CLIENT_USER`. Visible to both client and crew.
- `DRAFT_INTERNAL`: Work in progress by the Syner Crew. Not visible to the client.
- `APPROVED`: Finalized by a `SYNER_PARTNER` and published to the client portal.
- `CLIENT_VISIBLE`: General public tag for UI elements and general dashboard KPIs.

**Implementation Rule:** Any SQLAlchemy query executed on behalf of a `CLIENT_USER` MUST include an `apply_visibility_filter()` that automatically excludes `INTERNAL_ONLY` and `DRAFT_INTERNAL` objects.
