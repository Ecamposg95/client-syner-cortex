import os
import sys
import datetime

# Add the current directory to python path to allow importing app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.models.models import Organization, User, Module, OrganizationModule
from app.models.clevel import (
    ConsultingEngagement, Finding, StrategicInitiative,
    Deliverable, Risk, Decision,
    EngagementStatus, FindingCriticality, InitiativeStatus, RiskStatus, DecisionStatus
)
from app.security.auth import get_password_hash

def seed_clevel_bjx():
    db = SessionLocal()
    try:
        print("Starting C-Level seed for BJX Motors...")

        # Make sure tables exist
        Base.metadata.create_all(bind=engine)
        
        # 1. Organization
        org = db.query(Organization).filter(Organization.slug == "bjx-motors").first()
        if not org:
            org = Organization(name="BJX Motors", slug="bjx-motors", organization_type="CLIENT")
            db.add(org)
            db.flush()

        # 2. C-Level Users
        ceo_email = "ceo@bjx.local"
        ceo = db.query(User).filter(User.email == ceo_email).first()
        if not ceo:
            ceo = User(
                email=ceo_email,
                hashed_password=get_password_hash("password123"),
                full_name="Carlos Balderas",
                user_type="CLIENT_USER",
                is_active=True
            )
            db.add(ceo)
            db.flush()
        
        # 3. Create Engagement
        print("Creating Engagement...")
        db.query(ConsultingEngagement).filter(ConsultingEngagement.organization_id == org.id).delete()
        eng = ConsultingEngagement(
            organization_id=org.id,
            title="Diagnóstico Ejecutivo y Roadmap de Expansión BJX",
            objective="Escalar la operación, digitalizar procesos y construir un modelo franquiciable.",
            status=EngagementStatus.ACTIVE,
            start_date=datetime.date.today() - datetime.timedelta(days=30),
            end_date=datetime.date.today() + datetime.timedelta(days=90)
        )
        db.add(eng)
        db.flush()

        # 4. Create Findings
        print("Creating Findings...")
        f1 = Finding(engagement_id=eng.id, title="Dependencia de conocimiento informal", description="Los procesos dependen de la memoria de las personas clave.", area="Operaciones", criticality=FindingCriticality.CRITICAL, impact="Baja escalabilidad", recommendation="Estandarizar macroprocesos y documentar SOPs.")
        f2 = Finding(engagement_id=eng.id, title="Ausencia de tablero de KPIs directivos", description="Dirección no tiene visibilidad de las métricas en tiempo real.", area="Datos", criticality=FindingCriticality.HIGH, impact="Toma de decisiones reactiva", recommendation="Implementar dashboard ejecutivo de operación.")
        db.add_all([f1, f2])
        db.flush()

        # 5. Create Initiatives
        print("Creating Initiatives...")
        i1 = StrategicInitiative(engagement_id=eng.id, title="Estandarización del modelo operativo multi-sede", objective="Crear el Franchise Ready Pack", area="Operaciones", status=InitiativeStatus.IN_PROGRESS, priority="HIGH", estimated_budget=150000.0)
        i2 = StrategicInitiative(engagement_id=eng.id, title="Digitalización de procesos críticos", objective="Implementar Syner Cortex", area="Tecnología", status=InitiativeStatus.APPROVED, priority="HIGH", estimated_budget=200000.0)
        db.add_all([i1, i2])

        # 6. Create Deliverables
        print("Creating Deliverables...")
        d1 = Deliverable(engagement_id=eng.id, title="01 Franchise Ready Pack", type="Manual Maestro", status="DELIVERED", executive_summary="Arquitectura principal del sistema BJX, SOPs y lógica franchise-ready.")
        d2 = Deliverable(engagement_id=eng.id, title="06 Propuesta de Gobernanza", type="Deck", status="IN_REVIEW", executive_summary="Propuesta de comités, consejo y protección a minorías.")
        db.add_all([d1, d2])

        # 7. Create Risks & Decisions
        print("Creating Risks & Decisions...")
        db.query(Risk).filter(Risk.organization_id == org.id).delete()
        db.query(Decision).filter(Decision.organization_id == org.id).delete()

        r1 = Risk(organization_id=org.id, description="Crecimiento operativo sin estandarización", category="Operativo", probability="HIGH", impact="CRITICAL", mitigation_plan="Implementar auditorías estrictas en piso.", status=RiskStatus.OPEN)
        db.add(r1)

        dec1 = Decision(organization_id=org.id, title="Aprobar presupuesto para MVP de franquicia", context="Se requiere capital para el equipo de transformación", syner_recommendation="Aprobar fase 1 del roadmap", status=DecisionStatus.PENDING, deadline=datetime.date.today() + datetime.timedelta(days=7))
        db.add(dec1)

        db.commit()
        print("C-Level seed for BJX Motors completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_clevel_bjx()
