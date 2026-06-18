from sqlalchemy.orm import Session
from app.models.toolkit import (
    ConsultingToolkit, ConsultingTool, ToolRun, ToolInput, 
    ToolOutput, ToolRecommendation, ToolExport, ToolRunStatus
)
from app.schemas.toolkit import ConsultingToolkitCreate, ConsultingToolCreate

class ConsultingToolkitService:
    @staticmethod
    def get_all_toolkits(db: Session):
        return db.query(ConsultingToolkit).filter(ConsultingToolkit.is_active == True).all()

    @staticmethod
    def create_toolkit(db: Session, data: ConsultingToolkitCreate):
        toolkit = ConsultingToolkit(**data.dict())
        db.add(toolkit)
        db.commit()
        db.refresh(toolkit)
        return toolkit

class ToolExecutionService:
    @staticmethod
    def create_run(db: Session, tool_id: int, org_id: int, user_id: int, workspace_id: int = None):
        run = ToolRun(
            tool_id=tool_id,
            organization_id=org_id,
            workspace_id=workspace_id,
            created_by=user_id,
            status=ToolRunStatus.DRAFT
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def execute_tool(db: Session, run_id: int):
        run = db.query(ToolRun).filter(ToolRun.id == run_id).first()
        if not run:
            return None
        
        # In a real scenario, we would call an LLM using the tool's template and the run's inputs.
        # For now, we simulate the LLM output based on the tool's name.
        tool = db.query(ConsultingTool).filter(ConsultingTool.id == run.tool_id).first()
        tool_name = tool.name.lower() if tool else ""
        
        mock_output = ToolExecutionService._generate_mock_output(tool_name)
        
        output = ToolOutput(
            run_id=run.id,
            content_json=mock_output
        )
        db.add(output)
        
        run.status = ToolRunStatus.AI_GENERATED
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def _generate_mock_output(tool_name: str) -> dict:
        if 'foda' in tool_name:
            return {
              "fortalezas": ["Equipo técnico certificado y con experiencia", "Red de sucursales en ubicaciones estratégicas", "Fuerte lealtad de clientes recurrentes"],
              "oportunidades": ["Digitalización de órdenes de servicio para reducir tiempos", "Modelo franquiciable multi-sede", "Alianzas con flotillas empresariales (B2B)"],
              "debilidades": ["Falta de estandarización de SOPs entre sucursales", "Silos de información entre áreas", "Alta dependencia operativa del fundador"],
              "amenazas": ["Entrada de competidores con plataformas digitales nativas", "Rotación de personal técnico clave", "Incremento de costos de refacciones importadas"]
            }
        if 'hallazgos' in tool_name:
            return {
              "hallazgos": [
                { "titulo": "Ausencia de tablero de KPIs", "area": "Dirección", "impacto": "ALTO", "descripcion": "No existe un sistema centralizado para monitorear indicadores clave.", "recomendacion": "Implementar dashboard ejecutivo con métricas en tiempo real." },
                { "titulo": "Procesos de recepción no estandarizados", "area": "Operaciones", "impacto": "MEDIO", "descripcion": "Cada sucursal maneja un proceso distinto para la recepción vehicular.", "recomendacion": "Diseñar y documentar un SOP unificado." },
              ],
              "oportunidades": [
                { "titulo": "Modelo de suscripción para mantenimiento preventivo", "area": "Comercial", "impacto_potencial": "Generación de ingreso recurrente", "accion_sugerida": "Diseñar un paquete de membresía anual." },
              ]
            }
        if 'raci' in tool_name:
            return {
              "roles": ["Director General", "Gerente Operaciones", "Jefe Taller", "Recepción", "Almacén"],
              "procesos": [
                { "proceso": "Recepción de vehículo", "asignaciones": { "Director General": "I", "Gerente Operaciones": "A", "Jefe Taller": "C", "Recepción": "R", "Almacén": "" } },
                { "proceso": "Diagnóstico técnico", "asignaciones": { "Director General": "", "Gerente Operaciones": "I", "Jefe Taller": "A", "Recepción": "C", "Almacén": "I" } },
                { "proceso": "Autorización de presupuesto", "asignaciones": { "Director General": "A", "Gerente Operaciones": "R", "Jefe Taller": "C", "Recepción": "I", "Almacén": "" } },
                { "proceso": "Orden de refacciones", "asignaciones": { "Director General": "I", "Gerente Operaciones": "A", "Jefe Taller": "C", "Recepción": "", "Almacén": "R" } },
              ]
            }
        if 'macroflujo' in tool_name:
            return {
              "proceso_nombre": "Proceso de Servicio Automotriz End-to-End",
              "fases": [
                { "orden": 1, "nombre": "Recepción", "descripcion": "El cliente llega y se registra el vehículo.", "actor_responsable": "Asesor de Servicio", "entradas": ["Vehículo", "Datos del cliente"], "salidas": ["Orden de servicio"], "puntos_decision": [] },
                { "orden": 2, "nombre": "Diagnóstico", "descripcion": "Inspección técnica para identificar problemas.", "actor_responsable": "Técnico Senior", "entradas": ["Orden de servicio"], "salidas": ["Reporte de diagnóstico"], "puntos_decision": ["¿Requiere refacciones?"] },
                { "orden": 3, "nombre": "Cotización y Autorización", "descripcion": "Se genera presupuesto y se envía al cliente.", "actor_responsable": "Asesor de Servicio", "entradas": ["Reporte diagnóstico"], "salidas": ["Presupuesto autorizado"], "puntos_decision": ["¿Cliente autoriza?"] },
                { "orden": 4, "nombre": "Ejecución del Servicio", "descripcion": "Se realiza la reparación o mantenimiento.", "actor_responsable": "Técnico Asignado", "entradas": ["Presupuesto autorizado", "Refacciones"], "salidas": ["Vehículo reparado"], "puntos_decision": [] },
                { "orden": 5, "nombre": "Entrega y Facturación", "descripcion": "Se entrega el vehículo y se cobra.", "actor_responsable": "Asesor de Servicio", "entradas": ["Vehículo reparado"], "salidas": ["Factura", "Vehículo entregado"], "puntos_decision": [] },
              ]
            }
        if 'kpi' in tool_name:
            return {
              "kpis": [
                { "nombre": "Tasa de Satisfacción del Cliente (NPS)", "area": "Comercial", "formula": "(Promotores - Detractores) / Total * 100", "frecuencia": "Mensual", "responsable": "Gerente Comercial", "meta": "≥ 70", "unidad": "%" },
                { "nombre": "Tiempo Promedio de Servicio", "area": "Operaciones", "formula": "Suma de horas servicio / Número de órdenes", "frecuencia": "Semanal", "responsable": "Jefe de Taller", "meta": "≤ 4 hrs", "unidad": "horas" },
                { "nombre": "Tasa de Retrabajo", "area": "Calidad", "formula": "Retrabajos / Órdenes Completadas * 100", "frecuencia": "Mensual", "responsable": "Gerente Operaciones", "meta": "≤ 3%", "unidad": "%" },
                { "nombre": "Revenue por Sucursal", "area": "Finanzas", "formula": "Ingresos totales / Número de sucursales", "frecuencia": "Mensual", "responsable": "CFO", "meta": "≥ $500K MXN", "unidad": "MXN" },
                { "nombre": "Índice de Rotación de Personal", "area": "RRHH", "formula": "Bajas / Plantilla total * 100", "frecuencia": "Trimestral", "responsable": "Director General", "meta": "≤ 10%", "unidad": "%" },
              ]
            }
        if 'roadmap' in tool_name:
            return {
              "horizonte_30": [
                { "accion": "Mapear procesos as-is de recepción y diagnóstico", "responsable": "Consultor Syner", "entregable": "Documento de macroflujo actual", "kpi_exito": "100% de procesos documentados" },
                { "accion": "Implementar tablero de KPIs piloto en 1 sucursal", "responsable": "Atlas Tech", "entregable": "Dashboard funcional en Syner Cortex", "kpi_exito": "5 KPIs activos y monitoreados" },
              ],
              "horizonte_60": [
                { "accion": "Diseñar SOPs estandarizados para las 3 sucursales", "responsable": "Consultor Syner", "entregable": "Manual de procedimientos v1.0", "kpi_exito": "3 SOPs validados por Dirección" },
                { "accion": "Capacitar al equipo operativo en nuevos procesos", "responsable": "Academia Syner", "entregable": "Certificación de 15 colaboradores", "kpi_exito": "80% de aprobación en evaluación" },
              ],
              "horizonte_90": [
                { "accion": "Desplegar Syner Cortex en las 3 sucursales", "responsable": "Atlas Tech + Operaciones", "entregable": "Plataforma productiva multi-sede", "kpi_exito": "100% de adopción digital" },
                { "accion": "Presentar resultados a Junta Directiva", "responsable": "Director de Proyecto", "entregable": "Informe ejecutivo de transformación", "kpi_exito": "Aprobación de Fase 2 del roadmap" },
              ]
            }
        if 'journey' in tool_name:
            return {
              "journey_nombre": "Core Journey de Servicio Automotriz BJX",
              "fases": [
                { "fase": "Captación & Recepción", "etapas": [
                    { "codigo": "A1", "nombre": "Captación", "descripcion": "Lead entra por cita, walk-in o flotilla.", "responsable": "Comercial", "kpi": "Tasa de conversión de citas" },
                    { "codigo": "A2", "nombre": "Recepción", "descripcion": "Recepción física del vehículo y del cliente.", "responsable": "Asesor de Servicio", "kpi": "Tiempo de recepción" },
                    { "codigo": "A3", "nombre": "Registro", "descripcion": "Alta de la orden de servicio en sistema.", "responsable": "Asesor de Servicio", "kpi": "% órdenes con datos completos" },
                    { "codigo": "A4", "nombre": "Apertura", "descripcion": "Apertura formal de la orden y check-in.", "responsable": "Asesor de Servicio", "kpi": "Órdenes abiertas/día" }
                ]},
                { "fase": "Diagnóstico & Cotización", "etapas": [
                    { "codigo": "A5", "nombre": "Diagnóstico", "descripcion": "Inspección técnica del vehículo.", "responsable": "Técnico Senior", "kpi": "Precisión de diagnóstico" },
                    { "codigo": "A6", "nombre": "Cotización", "descripcion": "Elaboración del presupuesto.", "responsable": "Asesor de Servicio", "kpi": "Tiempo de cotización" },
                    { "codigo": "A7", "nombre": "Aprobación", "descripcion": "Autorización del cliente.", "responsable": "Cliente / Asesor", "kpi": "Tasa de aprobación" }
                ]},
                { "fase": "Planeación & Ejecución", "etapas": [
                    { "codigo": "A8", "nombre": "Planeación", "descripcion": "Asignación de bahía y técnico.", "responsable": "Jefe de Taller", "kpi": "Utilización de bahías" },
                    { "codigo": "A9", "nombre": "Refacciones", "descripcion": "Surtido de refacciones desde almacén.", "responsable": "Almacén", "kpi": "Disponibilidad de refacciones" },
                    { "codigo": "A10", "nombre": "Ejecución", "descripcion": "Realización del servicio.", "responsable": "Técnico Asignado", "kpi": "Tiempo de ejecución" },
                    { "codigo": "A12", "nombre": "Calidad", "descripcion": "Control de calidad final.", "responsable": "Control de Calidad", "kpi": "Tasa de retrabajo" }
                ]},
                { "fase": "Facturación & Entrega", "etapas": [
                    { "codigo": "A14", "nombre": "Facturación", "descripcion": "Generación de factura.", "responsable": "Administración", "kpi": "Tiempo de facturación" },
                    { "codigo": "A15", "nombre": "Cobro", "descripcion": "Cobro al cliente.", "responsable": "Caja", "kpi": "Cartera vencida" },
                    { "codigo": "A16", "nombre": "Entrega", "descripcion": "Entrega del vehículo.", "responsable": "Asesor de Servicio", "kpi": "Tiempo de entrega" }
                ]},
                { "fase": "Postventa", "etapas": [
                    { "codigo": "A17", "nombre": "Postventa", "descripcion": "Seguimiento y encuesta de satisfacción.", "responsable": "Comercial / CX", "kpi": "NPS" }
                ]}
              ]
            }
        if 'sop' in tool_name:
            return {
              "codigo": "SOP-OPS-02",
              "titulo": "Recepción de Vehículo",
              "objetivo": "Estandarizar la recepción del vehículo y del cliente para asegurar trazabilidad y una experiencia consistente en todas las sucursales.",
              "alcance": "Aplica desde la llegada del cliente hasta la apertura formal de la orden de servicio.",
              "responsable": "Asesor de Servicio",
              "pasos": [
                { "n": 1, "accion": "Recibir al cliente", "detalle": "Saludo protocolario, confirmar cita o registrar walk-in." },
                { "n": 2, "accion": "Inspección perimetral", "detalle": "Documentar con fotos el estado del vehículo (carrocería, kilometraje, nivel de combustible)." },
                { "n": 3, "accion": "Levantar requerimiento", "detalle": "Registrar síntomas y solicitudes del cliente en la orden." },
                { "n": 4, "accion": "Generar orden de servicio", "detalle": "Alta en sistema con datos completos del cliente y vehículo." },
                { "n": 5, "accion": "Confirmar expectativas", "detalle": "Acordar tiempos estimados y canal de contacto con el cliente." },
                { "n": 6, "accion": "Entregar acuse", "detalle": "Compartir folio de la orden y resguardo de llaves." }
              ],
              "entradas": ["Vehículo", "Datos del cliente", "Cita (si aplica)"],
              "salidas": ["Orden de servicio", "Evidencia fotográfica", "Resguardo de llaves"],
              "kpis": ["Tiempo de recepción ≤ 15 min", "% órdenes con datos completos ≥ 98%"],
              "riesgos": ["Daños no documentados", "Datos de contacto incorrectos", "Llaves sin resguardo"]
            }
        if 'academia' in tool_name:
            return {
              "curso": "Academia BJX Pit Crew",
              "modulo": "Módulo 1 · Recepción de Excelencia",
              "objetivo_aprendizaje": "Al finalizar, el asesor ejecuta el SOP de recepción cumpliendo trazabilidad y experiencia del cliente.",
              "duracion": "90 minutos",
              "publico": "Asesores de Servicio y Recepción",
              "lecciones": [
                { "titulo": "El primer contacto cuenta", "contenido": "Protocolo de bienvenida y manejo de expectativas del cliente.", "actividad": "Role-play de recepción en parejas." },
                { "titulo": "Inspección perimetral sin huecos", "contenido": "Cómo documentar el estado del vehículo con evidencia fotográfica.", "actividad": "Práctica de check-in con un vehículo real." },
                { "titulo": "Orden de servicio impecable", "contenido": "Captura de datos completos y síntomas del cliente.", "actividad": "Levantar 3 órdenes simuladas sin errores." }
              ],
              "evaluacion": ["Checklist de recepción ≥ 90%", "Evaluación práctica aprobada", "Quiz teórico ≥ 8/10"],
              "recursos": ["Plantilla de orden de servicio", "Guía rápida de inspección", "Video demostrativo"]
            }
        if 'gobernanza' in tool_name or 'organigrama' in tool_name:
            return {
              "organo_maximo": "Consejo de Administración BJX Motors",
              "comites": [
                { "nombre": "Comité de Operaciones", "proposito": "Seguimiento de KPIs operativos y estandarización entre sucursales.", "frecuencia": "Quincenal", "integrantes": ["Director General", "Gerente de Operaciones", "Jefes de Taller"] },
                { "nombre": "Comité Comercial", "proposito": "Revisión de pipeline, flotillas y satisfacción del cliente.", "frecuencia": "Mensual", "integrantes": ["Director General", "Gerente Comercial", "CX Lead"] },
                { "nombre": "Comité Financiero", "proposito": "Control presupuestal, cartera y rentabilidad por sucursal.", "frecuencia": "Mensual", "integrantes": ["Director General", "CFO", "Contraloría"] }
              ],
              "roles": [
                { "titulo": "Director General", "reporta_a": "Consejo de Administración", "responsabilidades": ["Estrategia", "Resultados globales", "Relación con el Consejo"] },
                { "titulo": "Gerente de Operaciones", "reporta_a": "Director General", "responsabilidades": ["Estandarización de procesos", "KPIs operativos", "Gestión de sucursales"] },
                { "titulo": "Gerente Comercial", "reporta_a": "Director General", "responsabilidades": ["Ventas y flotillas", "Pricing", "Experiencia del cliente"] },
                { "titulo": "CFO", "reporta_a": "Director General", "responsabilidades": ["Finanzas", "Presupuesto", "Cartera"] }
              ],
              "cadencia": ["Junta de Consejo: Trimestral", "Comités operativos: Quincenal/Mensual", "Cierre mensual: Primeros 5 días hábiles"]
            }
        if 'quick' in tool_name:
            return {
              "contexto": "Diagnóstico inicial BJX Motors: oportunidades de estandarización y digitalización de alto impacto y bajo esfuerzo.",
              "quick_wins": [
                { "titulo": "Estandarizar SOP de recepción en las 3 sucursales", "impacto": "ALTO", "esfuerzo": "BAJO", "responsable": "Gerente de Operaciones", "plazo": "2 semanas" },
                { "titulo": "Tablero de KPIs piloto en sucursal matriz", "impacto": "ALTO", "esfuerzo": "MEDIO", "responsable": "Atlas Tech", "plazo": "3 semanas" },
                { "titulo": "Resguardo de llaves con folio", "impacto": "MEDIO", "esfuerzo": "BAJO", "responsable": "Jefe de Taller", "plazo": "1 semana" },
                { "titulo": "Encuesta NPS post-servicio automatizada", "impacto": "MEDIO", "esfuerzo": "BAJO", "responsable": "CX Lead", "plazo": "2 semanas" }
              ],
              "proximos_pasos": [
                "Validar SOPs con Dirección y publicarlos en piso.",
                "Definir los 5 KPIs core del tablero ejecutivo.",
                "Agendar capacitación Pit Crew para el equipo operativo."
              ]
            }
        if 'ehs' in tool_name:
            return {
              "titulo": "Plan EHS · Manejo de Residuos Peligrosos en Taller",
              "alcance": "Aplica a las áreas de servicio, almacén y manejo de aceites, solventes y baterías.",
              "peligros": [
                { "peligro": "Derrame de aceites y solventes", "nivel": "ALTO", "control": "Contención secundaria y kit antiderrames en cada bahía." },
                { "peligro": "Manejo de baterías y ácidos", "nivel": "ALTO", "control": "Almacén ventilado con bandeja anticorrosiva y EPP específico." },
                { "peligro": "Inhalación de vapores", "nivel": "MEDIO", "control": "Ventilación forzada y mascarillas con filtro." },
                { "peligro": "Resbalones por piso húmedo", "nivel": "MEDIO", "control": "Señalización y limpieza inmediata de derrames." }
              ],
              "epp": ["Guantes de nitrilo", "Lentes de seguridad", "Botas con casquillo", "Mascarilla con filtro", "Mandil resistente a químicos"],
              "procedimientos": [
                { "nombre": "Segregación de residuos", "descripcion": "Separar residuos peligrosos por tipo en contenedores etiquetados." },
                { "nombre": "Bitácora de residuos", "descripcion": "Registrar volumen, tipo y disposición final de cada residuo." },
                { "nombre": "Respuesta a derrames", "descripcion": "Contener, absorber y disponer según protocolo; reportar el evento." }
              ],
              "normativa": ["NOM-052-SEMARNAT (residuos peligrosos)", "NOM-018-STPS (sustancias químicas)", "Bitácora ante SEMARNAT"],
              "responsables": ["Coordinador EHS", "Jefe de Taller", "Encargado de Almacén"]
            }
        if 'costos' in tool_name or 'costo' in tool_name:
            return {
              "titulo": "Análisis de Costos Operativos BJX",
              "periodo": "2025-2026",
              "categorias": [
                { "categoria": "Nómina operativa", "monto": "$4,200,000", "porcentaje": 42 },
                { "categoria": "Refacciones e insumos", "monto": "$3,000,000", "porcentaje": 30 },
                { "categoria": "Renta y servicios", "monto": "$1,500,000", "porcentaje": 15 },
                { "categoria": "Marketing y ventas", "monto": "$800,000", "porcentaje": 8 },
                { "categoria": "Otros / administrativos", "monto": "$500,000", "porcentaje": 5 }
              ],
              "hallazgos": [
                "La nómina representa el 42% de los costos: oportunidad de productividad por bahía.",
                "Compras de refacciones sin consolidar entre sucursales encarecen el insumo.",
                "No hay costeo por modelo de servicio, dificultando el pricing."
              ],
              "ahorros_potenciales": [
                { "concepto": "Compra consolidada de refacciones", "ahorro_estimado": "$300,000 / año", "accion": "Negociar volumen con proveedor único multi-sede." },
                { "concepto": "Costeo por modelo de servicio", "ahorro_estimado": "+8% margen", "accion": "Implementar tabla de costo por concepto de servicio." }
              ]
            }
        if 'visual' in tool_name:
            return {
              "titulo": "Visual Management Pack · Taller BJX",
              "tableros": [
                { "nombre": "Tablero de Bahías", "proposito": "Estado en tiempo real de cada bahía y unidad.", "metricas": ["Bahías ocupadas", "Tiempo en bahía", "Unidades en espera"], "frecuencia": "Tiempo real", "ubicacion": "Piso de taller" },
                { "nombre": "Tablero de KPIs Diarios", "proposito": "Seguimiento diario de productividad y calidad.", "metricas": ["Órdenes cerradas", "Retrabajos", "Tiempo promedio"], "frecuencia": "Diario", "ubicacion": "Oficina de jefe de taller" },
                { "nombre": "Tablero de Satisfacción", "proposito": "Visibilidad del NPS y quejas.", "metricas": ["NPS", "Quejas abiertas", "Tiempo de respuesta"], "frecuencia": "Semanal", "ubicacion": "Recepción" }
              ],
              "elementos_5s": ["Marcado de pisos por zona", "Sombras de herramienta", "Etiquetado de almacén", "Estándar de orden por bahía", "Auditoría 5S semanal"],
              "rutinas": [
                { "nombre": "Junta de arranque (huddle)", "cadencia": "Diario · 08:00", "responsable": "Jefe de Taller" },
                { "nombre": "Revisión de KPIs", "cadencia": "Semanal", "responsable": "Gerente de Operaciones" },
                { "nombre": "Auditoría 5S", "cadencia": "Semanal", "responsable": "Coordinador de Calidad" }
              ]
            }
        if 'manual' in tool_name:
            return {
              "titulo": "Manual Maestro BJX Motors — Franchise Ready",
              "version": "v1.0",
              "proposito": "Estandarizar la operación multi-sede y habilitar el modelo franquiciable.",
              "audiencia": "Franquiciatarios, Gerencia de Operaciones y equipo de piso.",
              "secciones": [
                { "numero": "1", "titulo": "Modelo de Negocio", "descripcion": "Propuesta de valor y promesa de marca.", "contenido_clave": ["Propuesta de valor", "Mercado objetivo", "Estándar de marca"] },
                { "numero": "2", "titulo": "Core Journey de Servicio", "descripcion": "Recorrido end-to-end A1→A17.", "contenido_clave": ["Mapa del journey", "Roles por etapa", "KPIs por etapa"] },
                { "numero": "3", "titulo": "SOPs Críticos", "descripcion": "Los 10 procedimientos operativos clave.", "contenido_clave": ["Recepción", "Diagnóstico", "Refacciones", "Calidad", "Entrega"] },
                { "numero": "4", "titulo": "Gobernanza y Estructura", "descripcion": "Organigrama, comités y RACI.", "contenido_clave": ["Organigrama", "Matriz RACI", "Cadencia de juntas"] },
                { "numero": "5", "titulo": "Control y KPIs", "descripcion": "KPI Book y tableros visuales.", "contenido_clave": ["KPI Book", "Tableros", "Rutinas de seguimiento"] },
                { "numero": "6", "titulo": "Cultura y Academia", "descripcion": "Capacitación y certificación Pit Crew.", "contenido_clave": ["Plan de academia", "Evaluaciones", "Certificación"] }
              ]
            }
        return { "message": "Output generado exitosamente" }

class ToolPromptBuilderService:
    @staticmethod
    def build_prompt(template: str, inputs: list):
        # Stub for compiling prompts
        pass

class ToolEvidenceService:
    @staticmethod
    def link_evidence(db: Session, output_id: int, doc_refs: list):
        # Stub for linking RAG documents as evidence
        pass

class ToolRecommendationService:
    @staticmethod
    def extract_recommendations(output_json: dict):
        # Stub for extracting recs from JSON AI Output
        pass

class ToolToRoadmapService:
    @staticmethod
    def convert_to_roadmap(db: Session, recommendation_id: int):
        # Stub for integration with Roadmap module
        pass

class ToolExportService:
    @staticmethod
    def generate_markdown(db: Session, run_id: int):
        # Stub for exporting ToolRun Output to Markdown
        pass
