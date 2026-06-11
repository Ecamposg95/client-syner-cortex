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
