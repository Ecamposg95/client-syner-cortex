"""Seed the BJX Motors RACI matrix from the Franchise Ready Pack deliverable
(RACI_Estructura_Operativa_Pod_BJX.pptx), idempotent.

Creates one RaciMatrix "RACI · Pod BJX" for the bjx-motors organization with:
  - 7 roles + authority charters (PPTX slide 5)
  - 9 critical processes + handoff evidence (slides 7 & 8)
  - the full R/A/C/I assignment grid (slide 7), where R/A cells become two rows

Re-running never duplicates: if the named matrix already exists for the org it
is left untouched. Runs as part of the deploy startCommand (|| true) and can be
invoked directly:

    python -m app.scripts.seed_raci_bjx
"""
from app.database import SessionLocal
import app.models.models  # noqa: F401
from app.models.models import Organization
from app.models.raci import RaciMatrix, RaciRole, RaciProcess, RaciAssignment, RaciValue

MATRIX_NAME = "RACI · Pod BJX"

# (name, charter_decides, charter_blocks, charter_escalates) — order = column order
ROLES = [
    ("Asesora de Servicio",
     "Recepción, OS, documentación, ETA, comunicación y entrega al cliente.",
     "No prometer tiempos o alcance no validados.",
     "Escalar desviaciones de cliente o documentación."),
    ("Crew Chief (Jefe de Mecánicos)",
     "Secuencia técnica, asignación de carga, validación de trabajo, retrabajo, go / no-go técnico.",
     "Bloquear unidad insegura, rechazar cierre no conforme, reasignar recursos en turno.",
     "Saturación sostenida o desviaciones repetitivas de calidad."),
    ("Técnico / Mecánico",
     "Ejecución técnica del trabajo asignado, evidencia técnica y reporte de hallazgos.",
     "Detener trabajo ante condición insegura o fuera de alcance.",
     "Hallazgos que cambian alcance o comprometen seguridad."),
    ("Almacén / Abasto",
     "Stock crítico, surtido, backorders, trazabilidad y control de salidas.",
     "Detener consumos no trazables; activar compra urgente según política.",
     "Backorders que comprometen SLA o cliente estratégico."),
    ("Administración / Cierre",
     "Cierre documental, facturación y reporte del Pod.",
     "Detener cierre sin evidencia completa.",
     "Desviaciones de margen o fugas de facturación."),
    ("Calidad / EHS",
     "Auditar cumplimiento, activar NCR, gestionar incidentes y veto por seguridad.",
     "Parar operación no segura y exigir evidencia / corrección antes de cierre.",
     "Incidentes EHS o incumplimientos normativos."),
    ("Gerente de Sitio",
     "P&L operativo del Pod, KPIs, staffing, disciplina de ejecución; priorización global y contingencias del sitio.",
     "Liberación de acciones correctivas; veto a prioridades que rompan capacidad.",
     "Decisiones de expansión, capex o cambio estructural a Dirección."),
]

# (name, evidence_min, handoff_owner)
PROCESSES = [
    ("Recepción y apertura de OS", "Unidad, folios, motivo, fotos iniciales.", "Asesora"),
    ("Clasificación y asignación", "OS clasificada, prioridad, técnico y ETA.", "Crew Chief"),
    ("Solicitud y surtido de refacciones", "Solicitud, stock, sustitutos, salida trazable.", "Almacén"),
    ("Ejecución técnica", "Trabajo, evidencia técnica, hallazgos.", "Técnico"),
    ("Validación / liberación técnica", "Checklist, conformidad o retrabajo.", "Crew Chief / Calidad"),
    ("Entrega y cierre documental", "Firma, encuesta, cierre documental.", "Asesora / Admin"),
    ("Incidente EHS / no conformidad", "NCR, evidencia, corrección.", "Calidad / EHS"),
    ("Backorder crítico / compra urgente", "Aging de backorder, política de compra.", "Almacén"),
    ("Cierre diario / reporte del Pod", "Tablero, KPIs del día, unidades abiertas.", "Administración"),
]

# Assignment grid — one cell per (process row, role column). A cell may hold
# several letters (e.g. "RA"). Columns follow ROLES order.
#                  Ases  Crew  Tec   Alm   Adm   EHS   Ger
GRID = [
    ["R",  "C",  "I",  "I",  "C",  "I",  "A"],   # Recepción y apertura
    ["I",  "RA", "C",  "I",  "I",  "I",  "C"],   # Clasificación y asignación
    ["I",  "A",  "R",  "R",  "I",  "I",  "C"],   # Solicitud y surtido
    ["I",  "A",  "R",  "C",  "I",  "I",  "I"],   # Ejecución técnica
    ["I",  "R",  "C",  "I",  "I",  "A",  "C"],   # Validación / liberación
    ["R",  "C",  "I",  "I",  "R",  "I",  "A"],   # Entrega y cierre documental
    ["I",  "C",  "I",  "I",  "I",  "RA", "C"],   # Incidente EHS / no conformidad
    ["I",  "A",  "C",  "R",  "C",  "I",  "C"],   # Backorder crítico
    ["C",  "C",  "I",  "C",  "R",  "C",  "A"],   # Cierre diario / reporte
]


def seed_raci_bjx():
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.slug == "bjx-motors").first()
        if not org:
            print("[seed_raci_bjx] org 'bjx-motors' no existe — corre seed_bjx_client primero. Skip.")
            return

        existing = db.query(RaciMatrix).filter(
            RaciMatrix.organization_id == org.id, RaciMatrix.name == MATRIX_NAME,
        ).first()
        if existing:
            print(f"[seed_raci_bjx] matriz '{MATRIX_NAME}' ya existe (id={existing.id}). Skip.")
            return

        matrix = RaciMatrix(
            organization_id=org.id,
            name=MATRIX_NAME,
            description="RACI ejecutiva de procesos críticos del Pod BJX. "
                        "Regla de diseño: un solo Accountable (A) por proceso.",
            version="1.0",
        )
        db.add(matrix)
        db.flush()

        role_rows = []
        for i, (name, decides, blocks, escalates) in enumerate(ROLES):
            r = RaciRole(
                matrix_id=matrix.id, name=name, order=i,
                charter_decides=decides, charter_blocks=blocks, charter_escalates=escalates,
            )
            db.add(r)
            role_rows.append(r)

        process_rows = []
        for i, (name, evidence, owner) in enumerate(PROCESSES):
            p = RaciProcess(
                matrix_id=matrix.id, name=name, order=i,
                evidence_min=evidence, handoff_owner=owner,
            )
            db.add(p)
            process_rows.append(p)
        db.flush()  # assign ids

        n_assign = 0
        for pi, row in enumerate(GRID):
            for ri, cell in enumerate(row):
                for letter in cell:  # "RA" -> R, A
                    db.add(RaciAssignment(
                        matrix_id=matrix.id,
                        process_id=process_rows[pi].id,
                        role_id=role_rows[ri].id,
                        value=RaciValue(letter),
                    ))
                    n_assign += 1

        db.commit()
        print(f"[seed_raci_bjx] creada '{MATRIX_NAME}' (id={matrix.id}): "
              f"{len(role_rows)} roles, {len(process_rows)} procesos, {n_assign} asignaciones.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_raci_bjx()
