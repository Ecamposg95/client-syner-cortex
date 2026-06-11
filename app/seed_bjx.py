import os
import sys
import datetime

# Add the current directory to python path to allow importing app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.models.models import (
    User, Organization, OrganizationUser, Module,
    OrganizationModule, Workspace, Document, Diagnosis,
    DiagnosisDimension, Roadmap, RoadmapItem
)
from app.models.kpi import KPI
from app.security.auth import get_password_hash

def seed_bjx_data():
    db = SessionLocal()
    try:
        print("Starting seed for BJX Motors...")

        # Make sure tables exist
        Base.metadata.create_all(bind=engine)
        
        # Explicitly create KPI table if not done (due to metadata binding check)
        from app.models.kpi import Base as kpi_base
        kpi_base.metadata.create_all(bind=engine)

        # 1. Clean existing BJX Motors data if any
        bjx_org = db.query(Organization).filter(Organization.slug == "bjx-motors").first()
        if bjx_org:
            print("Found existing BJX Motors organization. Cleaning up data first...")
            
            # Delete KPIs
            db.query(KPI).filter(KPI.organization_id == bjx_org.id).delete()
            
            # Delete OrganizationModules
            db.query(OrganizationModule).filter(OrganizationModule.organization_id == bjx_org.id).delete()
            
            # Workspaces cleanup (cascades to Documents, Diagnoses, Roadmaps, etc.)
            workspaces = db.query(Workspace).filter(Workspace.organization_id == bjx_org.id).all()
            for ws in workspaces:
                db.delete(ws)
            
            # Delete OrganizationUsers
            db.query(OrganizationUser).filter(OrganizationUser.organization_id == bjx_org.id).delete()
            
            # Delete Organization
            db.delete(bjx_org)
            db.commit()
            print("Clean-up finished.")

        # Clean up specific seed users if they exist
        db.query(User).filter(User.email.in_(["jorge@bjxmotors.com", "carlos.balderas@bjxmotors.com"])).delete()
        db.commit()

        # 2. Seed Users
        print("Creating users...")
        jorge_user = User(
            email="jorge@bjxmotors.com",
            hashed_password=get_password_hash("password123"),
            full_name="Jorge",
            user_type="CLIENT_USER",
            is_active=True,
            is_superadmin=False
        )
        carlos_user = User(
            email="carlos.balderas@bjxmotors.com",
            hashed_password=get_password_hash("password123"),
            full_name="Carlos Balderas",
            user_type="CLIENT_USER",
            is_active=True,
            is_superadmin=False
        )
        db.add(jorge_user)
        db.add(carlos_user)
        db.flush() # Get IDs

        # 3. Seed Organization
        print("Creating organization...")
        org = Organization(
            name="BJX Motors",
            slug="bjx-motors",
            organization_type="CLIENT"
        )
        db.add(org)
        db.flush() # Get ID

        # 4. Link Users to Organization
        print("Linking users to organization...")
        # Owner (Jorge)
        link_jorge = OrganizationUser(
            organization_id=org.id,
            user_id=jorge_user.id,
            role="CLIENT_OWNER"
        )
        # CEO (Carlos Balderas)
        link_carlos = OrganizationUser(
            organization_id=org.id,
            user_id=carlos_user.id,
            role="CLIENT_EXECUTIVE"
        )
        db.add(link_jorge)
        db.add(link_carlos)

        # 5. Enable Modules
        print("Enabling platform modules for organization...")
        modules = db.query(Module).all()
        for m in modules:
            org_module = OrganizationModule(
                organization_id=org.id,
                module_id=m.id,
                is_enabled=True
            )
            db.add(org_module)

        # 6. Seed Workspaces
        print("Creating project workspaces...")
        ws_gober = Workspace(
            organization_id=org.id,
            name="Gobernanza y Estrategia",
            description="Comités de gobierno, estructura directiva y acuerdos del consejo."
        )
        ws_ops = Workspace(
            organization_id=org.id,
            name="Operaciones y Estandarización",
            description="Manual Maestro, biblioteca de SOPs, flujos de contingencia y visual management."
        )
        ws_cultura = Workspace(
            organization_id=org.id,
            name="Cultura y Capacitación",
            description="Academia BJX Pit Crew, rutas de formación y cultura en taller."
        )
        ws_ehs = Workspace(
            organization_id=org.id,
            name="Seguridad y EHS",
            description="Estrategia de higiene, seguridad industrial y residuos peligrosos."
        )
        db.add(ws_gober)
        db.add(ws_ops)
        db.add(ws_cultura)
        db.add(ws_ehs)
        db.flush() # Get IDs

        # 7. Seed Documents (Vault Deliverables)
        print("Creating vault documents...")
        docs_data = [
            # Operaciones
            {"ws_id": ws_ops.id, "name": "Manual Maestro BJX.docx", "type": "DOCX", "path": "context/Entregables/01 Franchise Ready Pack/Manual_Maestro_BJX.docx", "status": "COMPLETED"},
            {"ws_id": ws_ops.id, "name": "RACI + Estructura Operativa.docx", "type": "DOCX", "path": "context/Entregables/01 Franchise Ready Pack/RACI_Estructura_Operativa.docx", "status": "COMPLETED"},
            {"ws_id": ws_ops.id, "name": "Biblioteca inicial de SOPs.docx", "type": "DOCX", "path": "context/Entregables/01 Franchise Ready Pack/Biblioteca_Inicial_SOPs.docx", "status": "COMPLETED"},
            {"ws_id": ws_ops.id, "name": "Documento formal de 10 SOPs.docx", "type": "DOCX", "path": "context/Entregables/01 Franchise Ready Pack/Documento_Formal_10_SOPs.docx", "status": "COMPLETED"},
            {"ws_id": ws_ops.id, "name": "Flujos de excepción y contingencia.docx", "type": "DOCX", "path": "context/Entregables/01 Franchise Ready Pack/Flujos_Excepcion_Contingencia.docx", "status": "COMPLETED"},
            {"ws_id": ws_ops.id, "name": "Visual Management Pack.docx", "type": "DOCX", "path": "context/Entregables/02 Apoyo Visual/Visual_Management_Pack.docx", "status": "COMPLETED"},
            {"ws_id": ws_ops.id, "name": "KPI Book + tablero ejecutivo.docx", "type": "DOCX", "path": "context/Entregables/01 Franchise Ready Pack/KPI_Book_Tablero_Ejecutivo.docx", "status": "COMPLETED"},
            
            # EHS
            {"ws_id": ws_ehs.id, "name": "EHS + Residuos peligrosos.docx", "type": "DOCX", "path": "context/Entregables/04 Estrategia de Higiene/EHS_Residuos_Peligrosos.docx", "status": "COMPLETED"},
            
            # Gobernanza
            {"ws_id": ws_gober.id, "name": "Gobierno Corporativo BJX.docx", "type": "DOCX", "path": "context/Entregables/06 Gobernanza/Gobierno_Corporativo_BJX.docx", "status": "COMPLETED"},
            
            # Cultura
            {"ws_id": ws_cultura.id, "name": "Academia BJX Pit Crew.docx", "type": "DOCX", "path": "context/Entregables/05 Academia Cultura/Academia_BJX_Pit_Crew.docx", "status": "COMPLETED"},
            {"ws_id": ws_cultura.id, "name": "Mural / posters / macroflujo.docx", "type": "DOCX", "path": "context/Entregables/03 Branding Mural Core Journey/Mural_Posters_Macroflujo.docx", "status": "PROCESSING"}
        ]

        for d in docs_data:
            doc = Document(
                workspace_id=d["ws_id"],
                organization_id=org.id,
                name=d["name"],
                file_type=d["type"],
                file_path=d["path"],
                status=d["status"],
                visibility="CLIENT_SHARED"
            )
            db.add(doc)

        # 8. Seed Diagnosis & SWOT (attached to the core workspace: ws_ops)
        print("Creating 360-degree business diagnosis...")
        diagnosis = Diagnosis(
            workspace_id=ws_ops.id,
            organization_id=org.id,
            user_id=jorge_user.id,
            status="COMPLETED",
            visibility="CLIENT_VISIBLE"
        )
        db.add(diagnosis)
        db.flush() # Get ID

        dimensions_data = [
            {
                "name": "Operaciones",
                "rating": 4,
                "findings": "Se completó el Manual Maestro, la biblioteca inicial de SOPs y flujos de contingencia. El reto principal es la adopción física e implementación en el taller de piso.",
                "recs": "Establecer auditorías semanales de adherencia a SOPs en piso, implementar tableros de gestión visual diarios y asignar líderes de estación.",
                "swot": {
                    "strengths": ["Documentación maestro completa", "Manuales de excepción ya validados", "Diseño visual del journey del cliente listo"],
                    "weaknesses": ["Brecha entre estándares teóricos y prácticas en piso", "Cierto grado de resistencia al cambio de mecánicos antiguos"],
                    "opportunities": ["Montaje inmediato del Visual Management Pack en piso", "Uso de checklists de SOPs automatizados"],
                    "threats": ["Pérdida de consistencia en calidad si el taller tiene alta rotación de técnicos"]
                }
            },
            {
                "name": "Recursos Humanos",
                "rating": 3,
                "findings": "La Academia BJX Pit Crew cuenta con diseño pedagógico y de cultura completo, pero el pilotaje de los tracks de capacitación y la inducción formal no han iniciado.",
                "recs": "Definir calendario formal para el pilotaje de Academia Pit Crew, entrenar a los entrenadores internos y ligar las certificaciones a incentivos de desempeño.",
                "swot": {
                    "strengths": ["Estructura cultural sólida (Academia Pit Crew)", "Estructura organizativa clara con RACI definida"],
                    "weaknesses": ["Sin instructores internos formalmente habilitados", "Falta registrar el avance individual de mecánicos"],
                    "opportunities": ["Creación de un programa de incentivos ligado a la aprobación de SOPs", "Desarrollo de videos cortos de apoyo"],
                    "threats": ["Falta de tiempo de los técnicos senior para capacitar a los juniors"]
                }
            },
            {
                "name": "Administracion",
                "rating": 3,
                "findings": "Se han estructurado lineamientos de gobierno corporativo, protección a minorías y regulación del cliente ancla. No obstante, las sesiones de consejo aún no están programadas formalmente.",
                "recs": "Agendar y celebrar la primera sesión del consejo de administración, constituir formalmente el comité operativo y automatizar las minutas.",
                "swot": {
                    "strengths": ["Regulación clara de la influencia del cliente ancla", "Mecanismo de gobernanza para blindaje corporativo definido"],
                    "weaknesses": ["Baja frecuencia de reuniones del comité directivo", "Decisiones ejecutivas aún centralizadas en pocas personas"],
                    "opportunities": ["Establecer un calendario anual de sesiones del consejo", "Documentar decisiones clave mediante actas formales"],
                    "threats": ["Conflictos de interés no resueltos por falta de mediación institucional en consejo"]
                }
            },
            {
                "name": "Ventas",
                "rating": 2,
                "findings": "El modelo de franquicia ('franchise-ready') y la narrativa de marca están listos, pero no hay un pipeline de prospección ni embudo comercial para captar nuevos franquiciados.",
                "recs": "Estructurar y configurar el pipeline en un CRM, generar un dossier formal de presentación y definir la estrategia de outbound marketing.",
                "swot": {
                    "strengths": ["Narrativa institucional sólida", "Materiales listos para convertirse en kit de franquicias"],
                    "weaknesses": ["Sin canales activos de prospección de inversionistas", "Falta de un CRM de ventas configurado"],
                    "opportunities": ["Lanzamiento de campaña digital enfocada en inversionistas automotrices", "Participación en ferias de franquicias"],
                    "threats": ["Copias de competidores si no se registra y resguarda la propiedad industrial rápidamente"]
                }
            },
            {
                "name": "Tecnologia",
                "rating": 2,
                "findings": "Se cuenta con un KPI book conceptual muy robusto, pero el seguimiento y registro de datos actual es completamente manual y se lleva en hojas de cálculo.",
                "recs": "Integrar las métricas operativas y financieras del taller en un tablero dinámico y evaluar la implementación de un software de piso móvil.",
                "swot": {
                    "strengths": ["KPI book muy completo con fórmulas e indicadores clave definidos"],
                    "weaknesses": ["Captura de datos manual propensa a errores", "Falta de integración de sistemas de inventarios con el taller"],
                    "opportunities": ["Sincronizar el tablero ejecutivo con bases de datos del taller", "Automatizar alertas de seguridad e inventario"],
                    "threats": ["Pérdida de historial de datos por fallas de almacenamiento local o sobreescritura"]
                }
            }
        ]

        for d in dimensions_data:
            dim_record = DiagnosisDimension(
                diagnosis_id=diagnosis.id,
                name=d["name"],
                rating=d["rating"],
                findings=d["findings"],
                recommendations=d["recs"],
                swot_analysis=d["swot"]
            )
            db.add(dim_record)

        # 9. Seed Roadmap & Roadmap Items (30/60/90 days)
        print("Creating 30/60/90-day execution roadmap...")
        roadmap = Roadmap(
            workspace_id=ws_ops.id,
            organization_id=org.id,
            diagnosis_id=diagnosis.id,
            visibility="CLIENT_VISIBLE"
        )
        db.add(roadmap)
        db.flush() # Get ID

        today = datetime.date.today()
        roadmap_items = [
            {
                "title": "[Operaciones] Priorizar SOPs, visual management, EHS y KPIs en piso",
                "desc": "Establecer la disciplina diaria en el taller aplicando los primeros SOPs y montando la señalética visual de piso.",
                "dim": "Operaciones", "phase": 30, "status": "IN_PROGRESS", "days": 30
            },
            {
                "title": "[Recursos Humanos] Definir responsables internos por pilar y carpeta",
                "desc": "Asignar formalmente coordinadores dentro del personal del taller para vigilar la adopción y vigencia de la documentación.",
                "dim": "Recursos Humanos", "phase": 30, "status": "TODO", "days": 30
            },
            {
                "title": "[Administracion] Validar e implementar comités y gobernanza corporativa",
                "desc": "Constituir los comités operativos semanales y convocar a la primera sesión de consejo oficial de BJX Motors.",
                "dim": "Administracion", "phase": 60, "status": "TODO", "days": 60
            },
            {
                "title": "[Operaciones] Establecer calendario de revisión y cierre de observaciones",
                "desc": "Crear un proceso recurrente para refinar manuales operativos y actualizar flujos de excepción tras las primeras semanas de adopción.",
                "dim": "Operaciones", "phase": 60, "status": "TODO", "days": 60
            },
            {
                "title": "[Recursos Humanos] Lanzamiento y pilotaje de Academia BJX Pit Crew",
                "desc": "Iniciar la capacitación sistemática de mecánicos en base a las rutas pedagógicas diseñadas en el manual de cultura.",
                "dim": "Recursos Humanos", "phase": 90, "status": "TODO", "days": 90
            },
            {
                "title": "[Ventas] Determinar materiales de adopción interna vs presentación externa",
                "desc": "Segmentar qué entregables del manual de marca y franquicia se utilizarán exclusivamente de forma interna y cuáles formarán parte del kit comercial para el exterior.",
                "dim": "Ventas", "phase": 90, "status": "TODO", "days": 90
            }
        ]

        for item in roadmap_items:
            ri = RoadmapItem(
                roadmap_id=roadmap.id,
                title=item["title"],
                description=item["desc"],
                dimension=item["dim"],
                phase=item["phase"],
                status=item["status"],
                due_date=today + datetime.timedelta(days=item["days"]),
                visibility="CLIENT_VISIBLE"
            )
            db.add(ri)

        # 10. Seed KPIs (with the new KPI model linked correctly to base)
        print("Creating dashboard KPIs...")
        kpis_data = [
            {"name": "Adopción de SOPs en taller", "value": 45.0},
            {"name": "Cumplimiento EHS (Seguridad)", "value": 60.0},
            {"name": "Eficiencia de Operaciones Pit Crew", "value": 50.0},
            {"name": "EBITDA Taller", "value": 14.0},
            {"name": "Dead Stock / Merma", "value": 1.2}
        ]

        for k in kpis_data:
            kpi = KPI(
                organization_id=org.id,
                name=k["name"],
                value=k["value"]
            )
            db.add(kpi)

        # Commit everything to database
        db.commit()
        print("--------------------------------------------------")
        print("BJX Motors client successfully seeded!")
        print(f"Organization ID: {org.id}")
        print("Credentials:")
        print(" - Dueño: jorge@bjxmotors.com (pwd: password123)")
        print(" - CEO: carlos.balderas@bjxmotors.com (pwd: password123)")
        print("--------------------------------------------------")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_bjx_data()
