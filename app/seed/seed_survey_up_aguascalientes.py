"""Seed the 'Encuesta Diagnóstica Inicial — Módulo 3' as a reusable Survey template.

Source: context/Matriz_Encuesta_Diagnostica_Modulo3_UP_Aguascalientes.xlsx
(Grupo Syner · Diplomado Gestión Efectiva del Negocio para MIPYMES · UP Aguascalientes)

Run standalone:  python -m app.seed.seed_survey_up_aguascalientes
Idempotent: removes any prior template with the same title before inserting.
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import engine, SessionLocal, Base
# Import base models so FK targets (users, organizations, workspaces) are registered
# in Base.metadata before create_all / flush resolves Survey's foreign keys.
import app.models.models  # noqa: F401
from app.models.survey import (
    Survey, SurveySection, SurveyQuestion, SurveyDiagnosticRule, SurveyQuestionType,
)

SURVEY_TITLE = "Encuesta Diagnóstica Inicial — Módulo 3: Gestión de Equipos y Operación"
SURVEY_DESCRIPTION = (
    "Esta encuesta tiene como objetivo conocer mejor el perfil de los participantes, "
    "los principales retos operativos y digitales de sus empresas y sus expectativas "
    "para el Módulo 3. Las respuestas serán utilizadas únicamente para adaptar los "
    "ejemplos, herramientas y dinámicas de clase a la realidad de las MIPYMES participantes."
)

# (title, [questions]) — each question is a dict matching SurveyQuestion fields.
SC = SurveyQuestionType.SINGLE_CHOICE
MC = SurveyQuestionType.MULTI_CHOICE
LS = SurveyQuestionType.LINEAR_SCALE
OT = SurveyQuestionType.OPEN_TEXT

SECTIONS = [
    ("Sección 1. Perfil de la empresa", [
        {
            "text": "¿Cuál es tu rol principal en la empresa?", "question_type": SC,
            "options": ["Dueño/a o socio/a", "Director/a general", "Gerente o encargado/a de área",
                        "Familiar involucrado en la empresa", "Responsable operativo", "Emprendedor/a", "Otro"],
            "is_required": True,
            "diagnostic_use": "Segmentar lenguaje, ejemplos y nivel de autoridad de los participantes.",
        },
        {
            "text": "¿Cuál es el giro principal de tu empresa?", "question_type": SC,
            "options": ["Comercio / retail", "Servicios profesionales", "Alimentos y bebidas",
                        "Manufactura / producción", "Construcción / mantenimiento", "Logística / distribución",
                        "Salud / bienestar", "Tecnología / servicios digitales", "Otro"],
            "is_required": True, "diagnostic_use": "Ajustar casos y ejemplos por sector.",
        },
        {
            "text": "¿Cuántas personas trabajan aproximadamente en tu empresa?", "question_type": SC,
            "options": ["1 a 5", "6 a 10", "11 a 30", "31 a 50", "51 a 100", "Más de 100"],
            "is_required": True, "diagnostic_use": "Distinguir micro, pequeña y mediana empresa.",
        },
        {
            "text": "¿La empresa es familiar?", "question_type": SC,
            "options": ["Sí, participan varios familiares en la operación",
                        "Sí, pero solo uno o dos familiares participan activamente",
                        "No es familiar", "No estoy seguro/a"],
            "is_required": True, "diagnostic_use": "Detectar sensibilidad de sucesión y continuidad.",
        },
    ]),
    ("Sección 2. Situación operativa actual", [
        {
            "text": "¿Qué tan ordenada consideras hoy la operación diaria de tu empresa?",
            "question_type": LS, "scale_min": 1, "scale_max": 5,
            "scale_min_label": "Muy desordenada", "scale_max_label": "Muy ordenada",
            "is_required": True, "diagnostic_use": "Medir madurez operativa inicial.",
        },
        {
            "text": "¿Qué tan clara está la asignación de responsabilidades en tu empresa?",
            "question_type": LS, "scale_min": 1, "scale_max": 5,
            "scale_min_label": "Nada clara", "scale_max_label": "Muy clara",
            "is_required": True, "diagnostic_use": "Determinar énfasis en matriz RACI y roles.",
        },
        {
            "text": "¿Qué tan frecuente ocurre que las tareas se retrasan porque nadie da seguimiento?",
            "question_type": SC,
            "options": ["Muy frecuente", "Frecuente", "A veces", "Rara vez", "Casi nunca"],
            "is_required": True, "diagnostic_use": "Dimensionar dolor de seguimiento.",
        },
        {
            "text": "¿Cuál es el principal problema operativo que más se repite en tu empresa?",
            "question_type": SC,
            "options": ["Falta de seguimiento", "Roles poco claros", "Retrabajos o errores frecuentes",
                        "Falta de comunicación entre áreas", "Dependencia excesiva del dueño/director",
                        "Personal que no cumple estándares", "Problemas de inventario, entregas o tiempos",
                        "Falta de indicadores", "Otro"],
            "is_required": True, "diagnostic_use": "Seleccionar casos y herramientas prioritarias.",
        },
        {
            "text": "¿Tu empresa cuenta con procesos documentados o formas estándar de trabajar?",
            "question_type": SC,
            "options": ["Sí, y se usan de manera consistente", "Sí, pero no siempre se aplican",
                        "Algunos procesos están documentados", "No, casi todo se maneja de manera informal", "No sé"],
            "is_required": True, "diagnostic_use": "Introducir sistema de gestión mínimo viable.",
        },
        {
            "text": "¿Actualmente utilizan indicadores para dar seguimiento a la operación?",
            "question_type": SC,
            "options": ["Sí, los revisamos periódicamente", "Sí, pero no se revisan con disciplina",
                        "Tenemos algunos datos, pero no indicadores formales", "No usamos indicadores", "No sé"],
            "is_required": True, "diagnostic_use": "Conectar seguimiento operativo con tablero e indicadores.",
        },
        {
            "text": "¿Qué herramientas digitales utilizan hoy para operar o dar seguimiento al negocio?",
            "question_type": MC,
            "options": ["WhatsApp / WhatsApp Business", "Excel o Google Sheets", "Formularios digitales",
                        "CRM", "ERP", "Punto de venta / POS", "Sistema de inventarios",
                        "Software contable o facturación", "Trello, Asana, Monday, Notion u otro tablero",
                        "Dashboards / BI", "IA generativa, por ejemplo ChatGPT, Copilot o Gemini",
                        "Ninguna de las anteriores", "Otro"],
            "is_required": True,
            "diagnostic_use": "Preparar intervención del consultor Syner sobre digitalización realista.",
        },
        {
            "text": "¿Qué tan integradas están tus herramientas digitales entre sí?",
            "question_type": SC,
            "options": ["Muy integradas: la información fluye entre sistemas",
                        "Parcialmente integradas: algunas cosas se conectan",
                        "Poco integradas: usamos varias herramientas aisladas",
                        "Nada integradas: todo se captura manualmente o varias veces",
                        "No usamos herramientas digitales", "No sé"],
            "is_required": True,
            "diagnostic_use": "Detectar dolor de doble captura, datos dispersos y APIs/integraciones.",
        },
        {
            "text": "¿Qué proceso te gustaría digitalizar o automatizar primero?",
            "question_type": SC,
            "options": ["Seguimiento de prospectos o clientes", "Cotizaciones y ventas", "Pedidos por WhatsApp",
                        "Inventario o almacén", "Compras y proveedores", "Cobranza",
                        "Agenda de servicios o entregas", "Quejas o servicio al cliente", "Reportes e indicadores",
                        "Tareas internas y seguimiento", "Recursos humanos / asistencia / capacitación", "Otro"],
            "is_required": True, "diagnostic_use": "Orientar ejemplos de CRM, ERP simple, automatización e IA.",
        },
        {
            "text": "¿Cuál es el principal obstáculo para digitalizar o automatizar más la operación?",
            "question_type": SC,
            "options": ["No sabemos por dónde empezar", "Falta de presupuesto", "Resistencia del equipo",
                        "Falta de tiempo", "Procesos desordenados", "Falta de datos confiables",
                        "Herramientas actuales no se comunican", "Miedo a complicar la operación",
                        "No lo vemos necesario por ahora", "Otro"],
            "is_required": True, "diagnostic_use": "Aterrizar mensajes del consultor: ordenar antes de automatizar.",
        },
    ]),
    ("Sección 3. Equipos, liderazgo y sucesión", [
        {
            "text": "¿Qué tan dependiente es la empresa del dueño, fundador o director general para operar correctamente?",
            "question_type": LS, "scale_min": 1, "scale_max": 5,
            "scale_min_label": "Poco dependiente", "scale_max_label": "Totalmente dependiente",
            "is_required": True, "diagnostic_use": "Abrir conversación de delegación y continuidad operativa.",
        },
        {
            "text": "¿La empresa tiene personas preparadas para asumir mayores responsabilidades en el futuro?",
            "question_type": SC,
            "options": ["Sí, claramente identificadas", "Algunas, pero requieren desarrollo",
                        "No estamos seguros", "No, todo depende de pocas personas", "No aplica"],
            "is_required": True, "diagnostic_use": "Medir necesidad de futuros liderazgos.",
        },
        {
            "text": "En empresas familiares: ¿hay conversaciones activas sobre sucesión o continuidad del negocio?",
            "question_type": SC,
            "options": ["Sí, ya existe un plan claro", "Sí se habla, pero no hay plan formal",
                        "Es un tema pendiente o incómodo", "No se ha hablado", "No aplica / no es empresa familiar"],
            "is_required": True, "diagnostic_use": "Identificar interés y tensión en sucesión familiar.",
        },
    ]),
    ("Sección 4. Expectativas del módulo", [
        {
            "text": "¿Qué te gustaría llevarte de este módulo?", "question_type": MC,
            "options": ["Herramientas para ordenar la operación", "Mejorar seguimiento y cumplimiento",
                        "Definir responsabilidades con claridad", "Coordinar mejor a mi equipo",
                        "Mejorar comunicación entre áreas", "Aprender a medir desempeño",
                        "Resolver problemas repetitivos", "Preparar futuros líderes",
                        "Reducir dependencia del dueño/director", "Ideas para profesionalizar una empresa familiar",
                        "Ideas simples para digitalizar o automatizar procesos",
                        "Entender cuándo conviene un CRM, ERP o tablero digital", "Otro"],
            "is_required": True, "diagnostic_use": "Alinear énfasis didáctico del módulo.",
        },
        {
            "text": ("Describe en una frase un problema real de operación, equipo, digitalización o "
                     "sucesión que te gustaría trabajar durante el módulo."),
            "question_type": OT, "is_required": False,
            "diagnostic_use": "Seleccionar historias reales para la Clínica de Casos MIPYME.",
        },
    ]),
]

# Rule-based "Lectura Diagnóstica": pattern -> suggested classroom adjustment.
# `condition` is an optional hint consumed by SurveyDiagnosticService to auto-trigger
# the rule from aggregated answers. Format: {"question_order": int, "op": str, "value": ...}
#   op "scale_gte"/"scale_lte": avg of LINEAR_SCALE question vs value
#   op "option_share_gte": share of responses choosing any of value[options] >= threshold
DIAGNOSTIC_RULES = [
    {
        "pattern": "Alta dependencia del dueño + empresa familiar",
        "suggestion": "Abrir con sucesión operativa, delegación y mapa de continuidad.",
        "condition": {"question_order": 15, "op": "scale_gte", "value": 4},
    },
    {
        "pattern": "Roles poco claros + tareas sin seguimiento",
        "suggestion": "Dar más peso a RACI MIPYME, huddle de 10 minutos y tablero semanal.",
        "condition": {"question_order": 6, "op": "scale_lte", "value": 2.5},
    },
    {
        "pattern": "Procesos no documentados",
        "suggestion": "Enfatizar sistema de gestión mínimo viable: procesos, roles, indicadores, rutinas y mejora.",
        "condition": {"question_order": 9, "op": "option_share_gte",
                      "options": ["No, casi todo se maneja de manera informal",
                                  "Algunos procesos están documentados"], "value": 0.4},
    },
    {
        "pattern": "Bajo uso de indicadores",
        "suggestion": "Usar ejemplos simples: entregas a tiempo, quejas, retrabajos, ventas cerradas, pendientes vencidos.",
        "condition": {"question_order": 10, "op": "option_share_gte",
                      "options": ["No usamos indicadores",
                                  "Tenemos algunos datos, pero no indicadores formales"], "value": 0.4},
    },
    {
        "pattern": "Uso alto de WhatsApp/Excel pero bajo CRM/ERP",
        "suggestion": "Mostrar digitalización gradual: de captura dispersa a tablero y seguimiento.",
        "condition": {"question_order": 11, "op": "option_share_gte",
                      "options": ["WhatsApp / WhatsApp Business", "Excel o Google Sheets"], "value": 0.5},
    },
    {
        "pattern": "Herramientas no integradas / doble captura",
        "suggestion": "Intervención del consultor: integraciones simples, automatización de tareas y flujo de datos.",
        "condition": {"question_order": 12, "op": "option_share_gte",
                      "options": ["Nada integradas: todo se captura manualmente o varias veces",
                                  "Poco integradas: usamos varias herramientas aisladas"], "value": 0.4},
    },
    {
        "pattern": "Deseo de automatizar ventas, pedidos o cobranza",
        "suggestion": "Explicar CRM, embudo, alertas, recordatorios y trazabilidad del cliente.",
        "condition": {"question_order": 13, "op": "option_share_gte",
                      "options": ["Seguimiento de prospectos o clientes", "Cotizaciones y ventas",
                                  "Pedidos por WhatsApp", "Cobranza"], "value": 0.3},
    },
    {
        "pattern": "Deseo de automatizar inventario, compras o entregas",
        "suggestion": "Explicar ERP simple, inventarios, requisiciones, mínimos y flujo operativo.",
        "condition": {"question_order": 13, "op": "option_share_gte",
                      "options": ["Inventario o almacén", "Compras y proveedores",
                                  "Agenda de servicios o entregas"], "value": 0.3},
    },
]


def seed_survey_template():
    db = SessionLocal()
    try:
        print("Starting Survey template seed (UP Aguascalientes · Módulo 3)...")
        Base.metadata.create_all(bind=engine)

        # Idempotent: remove prior template(s) with the same title.
        existing = db.query(Survey).filter(
            Survey.title == SURVEY_TITLE, Survey.is_template == True
        ).all()
        for s in existing:
            db.delete(s)
        db.flush()

        survey = Survey(title=SURVEY_TITLE, description=SURVEY_DESCRIPTION, is_template=True)
        db.add(survey)
        db.flush()

        q_order = 0
        for s_idx, (sec_title, questions) in enumerate(SECTIONS):
            section = SurveySection(survey_id=survey.id, title=sec_title, order=s_idx)
            db.add(section)
            db.flush()
            for q in questions:
                q_order += 1
                db.add(SurveyQuestion(section_id=section.id, order=q_order, **q))

        for rule in DIAGNOSTIC_RULES:
            db.add(SurveyDiagnosticRule(survey_id=survey.id, **rule))

        db.commit()
        print(f"✅ Seeded survey template #{survey.id} with {q_order} questions "
              f"and {len(DIAGNOSTIC_RULES)} diagnostic rules.")
        return survey.id
    except Exception as e:
        db.rollback()
        print(f"❌ Error during survey seed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_survey_template()
