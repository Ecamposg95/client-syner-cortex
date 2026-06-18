import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.models.toolkit import ConsultingToolkit, ConsultingTool, ToolTemplate

def seed_toolkits():
    db = SessionLocal()
    try:
        print("Starting Cortex Consulting Toolkit seed...")
        Base.metadata.create_all(bind=engine)

        # Clear existing to prevent duplicates
        db.query(ToolTemplate).delete()
        db.query(ConsultingTool).delete()
        db.query(ConsultingToolkit).delete()

        # ═══ TOOLKITS ═══
        toolkits_data = [
            {"name": "Strategic Diagnosis Toolkit", "description": "Diagnóstico y análisis estratégico de alto nivel para la dirección general.", "icon": "search"},
            {"name": "Governance & Structure Toolkit", "description": "Diseño organizacional, matrices de responsabilidad y gobierno corporativo.", "icon": "landmark"},
            {"name": "Process & Operations Toolkit", "description": "Mapeo de macroflujos, blueprints de servicio y optimización operativa.", "icon": "settings"},
            {"name": "Control & Performance Toolkit", "description": "KPIs ejecutivos, scorecards y medición de resultados.", "icon": "activity"},
            {"name": "Visual Management & Adoption Toolkit", "description": "Tableros de gestión visual, 5S y adopción de mejoras.", "icon": "monitor"},
            {"name": "Quality, Safety & Compliance Toolkit", "description": "Estándares EHS, calidad, auditorías y normativas.", "icon": "shield"},
            {"name": "Culture, Training & Adoption Toolkit", "description": "Gestión de cambio, capacitación y cultura organizacional.", "icon": "users"},
            {"name": "Commercial & Client Relationship Toolkit", "description": "Estrategia comercial B2B, modelos de pricing y relación con clientes.", "icon": "briefcase"},
            {"name": "Economic & Financial Toolkit", "description": "Modelado financiero, ROI de proyectos y análisis de inversión.", "icon": "dollar-sign"},
            {"name": "Implementation Toolkit", "description": "Roadmaps de implementación, planes 30/60/90 y seguimiento de despliegue.", "icon": "rocket"},
        ]

        created_toolkits = {}
        for tk_data in toolkits_data:
            tk = ConsultingToolkit(**tk_data)
            db.add(tk)
            db.flush()
            created_toolkits[tk.name] = tk.id

        # ═══ TOOLS + TEMPLATES ═══

        tools_and_templates = [
            # ── Strategic Diagnosis Toolkit ──
            {
                "toolkit": "Strategic Diagnosis Toolkit",
                "name": "FODA Ejecutivo",
                "description": "Análisis de Fortalezas, Oportunidades, Debilidades y Amenazas a nivel C-Level.",
                "system_prompt": "Eres un consultor estratégico de alto nivel (C-Level). Evalúa los inputs proporcionados por el cliente o el equipo y genera una matriz FODA (SWOT) profesional, estructurada y concisa. Responde siempre en formato JSON puro respetando el esquema indicado.",
                "user_prompt": "Contexto de la empresa:\n{contexto}\n\nHallazgos previos:\n{hallazgos}\n\nPor favor genera las 4 dimensiones del FODA con al menos 3 elementos cada una.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "fortalezas": {"type": "array", "items": {"type": "string"}},
                        "oportunidades": {"type": "array", "items": {"type": "string"}},
                        "debilidades": {"type": "array", "items": {"type": "string"}},
                        "amenazas": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["fortalezas", "oportunidades", "debilidades", "amenazas"]
                },
                "input_fields": ["contexto", "hallazgos"]
            },
            {
                "toolkit": "Strategic Diagnosis Toolkit",
                "name": "Matriz de Hallazgos y Oportunidades",
                "description": "Consolidación de hallazgos críticos y oportunidades detectadas durante el diagnóstico.",
                "system_prompt": "Eres un Business Analyst senior. A partir de las observaciones del consultor, genera una matriz estructurada de hallazgos y oportunidades, clasificados por impacto (ALTO, MEDIO, BAJO) y área funcional.",
                "user_prompt": "Empresa: {empresa}\nÁreas evaluadas: {areas}\nObservaciones del consultor:\n{observaciones}\n\nGenera la matriz de hallazgos y oportunidades.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "hallazgos": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "titulo": {"type": "string"},
                                "area": {"type": "string"},
                                "impacto": {"type": "string", "enum": ["ALTO", "MEDIO", "BAJO"]},
                                "descripcion": {"type": "string"},
                                "recomendacion": {"type": "string"}
                            }
                        }},
                        "oportunidades": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "titulo": {"type": "string"},
                                "area": {"type": "string"},
                                "impacto_potencial": {"type": "string"},
                                "accion_sugerida": {"type": "string"}
                            }
                        }}
                    }
                },
                "input_fields": ["empresa", "areas", "observaciones"]
            },

            # ── Governance & Structure Toolkit ──
            {
                "toolkit": "Governance & Structure Toolkit",
                "name": "Matriz RACI",
                "description": "Definición de Responsabilidades (Responsible, Accountable, Consulted, Informed) por proceso.",
                "system_prompt": "Eres un consultor especializado en gobierno corporativo y estructura organizacional. Genera una matriz RACI profesional basada en los procesos y roles indicados. Cada celda debe contener R, A, C, I o estar vacía.",
                "user_prompt": "Empresa: {empresa}\nProcesos clave:\n{procesos}\nRoles identificados:\n{roles}\n\nGenera la matriz RACI como un arreglo de filas.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "roles": {"type": "array", "items": {"type": "string"}},
                        "procesos": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "proceso": {"type": "string"},
                                "asignaciones": {"type": "object"}
                            }
                        }}
                    }
                },
                "input_fields": ["empresa", "procesos", "roles"]
            },

            # ── Process & Operations Toolkit ──
            {
                "toolkit": "Process & Operations Toolkit",
                "name": "Macroflujo Operativo",
                "description": "Mapeo de nivel 0 de los procesos operativos del cliente.",
                "system_prompt": "Eres un consultor de procesos y operaciones. Genera un macroflujo operativo de nivel 0 que capture las fases principales del proceso, los actores involucrados, las entradas y salidas de cada fase, y los puntos de decisión clave.",
                "user_prompt": "Empresa: {empresa}\nProceso a mapear: {proceso}\nDescripción general:\n{descripcion}\nActores involucrados: {actores}\n\nGenera el macroflujo operativo.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "proceso_nombre": {"type": "string"},
                        "fases": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "orden": {"type": "integer"},
                                "nombre": {"type": "string"},
                                "descripcion": {"type": "string"},
                                "actor_responsable": {"type": "string"},
                                "entradas": {"type": "array", "items": {"type": "string"}},
                                "salidas": {"type": "array", "items": {"type": "string"}},
                                "puntos_decision": {"type": "array", "items": {"type": "string"}}
                            }
                        }}
                    }
                },
                "input_fields": ["empresa", "proceso", "descripcion", "actores"]
            },

            # ── Control & Performance Toolkit ──
            {
                "toolkit": "Control & Performance Toolkit",
                "name": "KPI Book",
                "description": "Definición de indicadores clave de desempeño (KPIs) ejecutivos por área.",
                "system_prompt": "Eres un Data Product Manager y consultor de performance. Genera un KPI Book profesional con indicadores claramente definidos, sus fórmulas, frecuencia de medición, responsable y meta sugerida.",
                "user_prompt": "Empresa: {empresa}\nÁreas a medir: {areas}\nObjetivos estratégicos:\n{objetivos}\n\nGenera el KPI Book con al menos 2 KPIs por área.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "kpis": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "nombre": {"type": "string"},
                                "area": {"type": "string"},
                                "formula": {"type": "string"},
                                "frecuencia": {"type": "string"},
                                "responsable": {"type": "string"},
                                "meta": {"type": "string"},
                                "unidad": {"type": "string"}
                            }
                        }}
                    }
                },
                "input_fields": ["empresa", "areas", "objetivos"]
            },

            # ── Implementation Toolkit ──
            {
                "toolkit": "Implementation Toolkit",
                "name": "Roadmap 30/60/90",
                "description": "Plan de despliegue ejecutivo a 30, 60 y 90 días con hitos medibles.",
                "system_prompt": "Eres un consultor de implementación y transformación digital. Genera un roadmap ejecutivo dividido en 3 horizontes (30, 60 y 90 días) con acciones concretas, responsables, entregables y KPIs de éxito para cada fase.",
                "user_prompt": "Empresa: {empresa}\nProyecto: {proyecto}\nObjetivo general:\n{objetivo}\nRecursos disponibles: {recursos}\n\nGenera el roadmap 30/60/90.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "horizonte_30": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "accion": {"type": "string"},
                                "responsable": {"type": "string"},
                                "entregable": {"type": "string"},
                                "kpi_exito": {"type": "string"}
                            }
                        }},
                        "horizonte_60": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "accion": {"type": "string"},
                                "responsable": {"type": "string"},
                                "entregable": {"type": "string"},
                                "kpi_exito": {"type": "string"}
                            }
                        }},
                        "horizonte_90": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "accion": {"type": "string"},
                                "responsable": {"type": "string"},
                                "entregable": {"type": "string"},
                                "kpi_exito": {"type": "string"}
                            }
                        }}
                    }
                },
                "input_fields": ["empresa", "proyecto", "objetivo", "recursos"]
            },

            # ── Process & Operations Toolkit · Core Journey ──
            {
                "toolkit": "Process & Operations Toolkit",
                "name": "Core Journey del Cliente",
                "description": "Recorrido end-to-end del cliente (Captación → Postventa) agrupado por fases, ideal para presentar en juntas.",
                "system_prompt": "Eres un consultor de experiencia de cliente y operaciones. Construye el 'core journey' end-to-end del cliente como una secuencia de etapas codificadas (A1, A2, ...) agrupadas en fases macro. Cada etapa lleva un código corto, nombre, descripción breve, responsable y un KPI asociado. Responde solo en JSON puro respetando el esquema.",
                "user_prompt": "Empresa: {empresa}\nSector / tipo de servicio: {sector}\nMomentos clave del cliente:\n{momentos}\n\nGenera el core journey agrupado en 4-6 fases macro, con sus etapas codificadas.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "journey_nombre": {"type": "string"},
                        "fases": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "fase": {"type": "string"},
                                "etapas": {"type": "array", "items": {
                                    "type": "object",
                                    "properties": {
                                        "codigo": {"type": "string"},
                                        "nombre": {"type": "string"},
                                        "descripcion": {"type": "string"},
                                        "responsable": {"type": "string"},
                                        "kpi": {"type": "string"}
                                    }
                                }}
                            }
                        }}
                    },
                    "required": ["journey_nombre", "fases"]
                },
                "input_fields": ["empresa", "sector", "momentos"]
            },

            # ── Process & Operations Toolkit · SOP Card ──
            {
                "toolkit": "Process & Operations Toolkit",
                "name": "SOP Card Operativo",
                "description": "Procedimiento operativo estándar en formato tarjeta visual (objetivo, pasos, entradas/salidas, KPIs y riesgos).",
                "system_prompt": "Eres un ingeniero de procesos. Documenta un Procedimiento Operativo Estándar (SOP) en formato tarjeta, claro y accionable para piso. Incluye código, objetivo, alcance, responsable, pasos numerados con detalle, entradas, salidas, KPIs de control y riesgos. Responde solo en JSON puro respetando el esquema.",
                "user_prompt": "Empresa: {empresa}\nProceso a estandarizar: {proceso}\nContexto / notas del consultor:\n{contexto}\n\nGenera el SOP Card con al menos 5 pasos.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "codigo": {"type": "string"},
                        "titulo": {"type": "string"},
                        "objetivo": {"type": "string"},
                        "alcance": {"type": "string"},
                        "responsable": {"type": "string"},
                        "pasos": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "n": {"type": "integer"},
                                "accion": {"type": "string"},
                                "detalle": {"type": "string"}
                            }
                        }},
                        "entradas": {"type": "array", "items": {"type": "string"}},
                        "salidas": {"type": "array", "items": {"type": "string"}},
                        "kpis": {"type": "array", "items": {"type": "string"}},
                        "riesgos": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["codigo", "titulo", "objetivo", "pasos"]
                },
                "input_fields": ["empresa", "proceso", "contexto"]
            },

            # ── Culture, Training & Adoption Toolkit · Academia ──
            {
                "toolkit": "Culture, Training & Adoption Toolkit",
                "name": "Módulo de Academia Syner",
                "description": "Diseño instruccional de un módulo de curso (objetivo de aprendizaje, lecciones, actividad y evaluación) para impartir en clase.",
                "system_prompt": "Eres un diseñador instruccional experto en capacitación corporativa. Diseña un módulo de curso listo para impartir, con objetivo de aprendizaje claro, lecciones con contenido y una actividad práctica por lección, criterios de evaluación y recursos. Responde solo en JSON puro respetando el esquema.",
                "user_prompt": "Curso / Academia: {curso}\nTema del módulo: {tema}\nPúblico objetivo: {publico}\nDuración estimada: {duracion}\n\nGenera el módulo con 3-5 lecciones.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "curso": {"type": "string"},
                        "modulo": {"type": "string"},
                        "objetivo_aprendizaje": {"type": "string"},
                        "duracion": {"type": "string"},
                        "publico": {"type": "string"},
                        "lecciones": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "titulo": {"type": "string"},
                                "contenido": {"type": "string"},
                                "actividad": {"type": "string"}
                            }
                        }},
                        "evaluacion": {"type": "array", "items": {"type": "string"}},
                        "recursos": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["curso", "modulo", "objetivo_aprendizaje", "lecciones"]
                },
                "input_fields": ["curso", "tema", "publico", "duracion"]
            },

            # ── Governance & Structure Toolkit · Gobernanza ──
            {
                "toolkit": "Governance & Structure Toolkit",
                "name": "Organigrama de Gobernanza",
                "description": "Estructura de gobierno corporativo: órgano máximo, comités, roles clave y cadencia de juntas.",
                "system_prompt": "Eres un consultor de gobierno corporativo. Diseña la estructura de gobernanza de la organización: órgano máximo de decisión, comités (con propósito, frecuencia e integrantes), roles clave (con a quién reportan y responsabilidades) y la cadencia de juntas. Responde solo en JSON puro respetando el esquema.",
                "user_prompt": "Empresa: {empresa}\nTamaño / etapa: {etapa}\nÁreas y liderazgos actuales:\n{liderazgos}\n\nGenera la estructura de gobernanza.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "organo_maximo": {"type": "string"},
                        "comites": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "nombre": {"type": "string"},
                                "proposito": {"type": "string"},
                                "frecuencia": {"type": "string"},
                                "integrantes": {"type": "array", "items": {"type": "string"}}
                            }
                        }},
                        "roles": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "titulo": {"type": "string"},
                                "reporta_a": {"type": "string"},
                                "responsabilidades": {"type": "array", "items": {"type": "string"}}
                            }
                        }},
                        "cadencia": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["organo_maximo", "comites", "roles"]
                },
                "input_fields": ["empresa", "etapa", "liderazgos"]
            },

            # ── Implementation Toolkit · Quick Wins ──
            {
                "toolkit": "Implementation Toolkit",
                "name": "Quick Wins & Próximos Pasos",
                "description": "One-pager de victorias rápidas priorizadas por impacto/esfuerzo y próximos pasos inmediatos.",
                "system_prompt": "Eres un consultor de implementación. Identifica 'quick wins' accionables priorizados por impacto (ALTO/MEDIO/BAJO) y esfuerzo (ALTO/MEDIO/BAJO), cada uno con responsable y plazo, más una lista de próximos pasos inmediatos. Responde solo en JSON puro respetando el esquema.",
                "user_prompt": "Empresa: {empresa}\nHallazgos / contexto del diagnóstico:\n{contexto}\n\nGenera 4-6 quick wins y los próximos pasos.",
                "schema": {
                    "type": "object",
                    "properties": {
                        "contexto": {"type": "string"},
                        "quick_wins": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "titulo": {"type": "string"},
                                "impacto": {"type": "string", "enum": ["ALTO", "MEDIO", "BAJO"]},
                                "esfuerzo": {"type": "string", "enum": ["ALTO", "MEDIO", "BAJO"]},
                                "responsable": {"type": "string"},
                                "plazo": {"type": "string"}
                            }
                        }},
                        "proximos_pasos": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["quick_wins", "proximos_pasos"]
                },
                "input_fields": ["empresa", "contexto"]
            },
        ]

        for t in tools_and_templates:
            toolkit_id = created_toolkits[t["toolkit"]]
            tool = ConsultingTool(toolkit_id=toolkit_id, name=t["name"], description=t["description"])
            db.add(tool)
            db.flush()

            template = ToolTemplate(
                tool_id=tool.id,
                system_prompt=t["system_prompt"],
                user_prompt_template=t["user_prompt"],
                json_schema_output=t["schema"],
            )
            db.add(template)
            print(f"  ✓ {t['toolkit']} → {t['name']}")

        db.commit()
        print("\n✅ Cortex Consulting Toolkit seed completed!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_toolkits()
