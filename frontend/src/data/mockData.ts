// ============================================================
// SYNER HUB — Mock Data for Demo Views
// All data is static; backend integration is Phase 2.
// ============================================================

export const project = {
  name: 'Reordenamiento operativo',
  client: 'Grupo Industrial del Norte',
  quarter: 'Q3 2026',
  phase: 4,
  totalPhases: 5,
  progress: 67,
  status: 'EN ADOPCIÓN' as const,
};

export type KPI = {
  label: string;
  value: string;
  delta: string;
  up: boolean;
};

export const kpis: KPI[] = [
  { label: 'Ahorro generado',   value: '$ 4.2M',  delta: '+18% vs baseline', up: true },
  { label: 'Adopción usuarios', value: '82%',      delta: '+12 pp este mes',  up: true },
  { label: 'Procesos auto.',    value: '27 / 34',  delta: '5 en sprint',      up: true },
  { label: 'OKRs trimestre',    value: '6 / 8',    delta: '2 en riesgo',      up: false },
];

export type Phase = {
  id: number;
  title: string;
  status: 'Completado' | 'En Curso' | 'Pendiente';
  date: string;
  responsible?: string;
  active?: boolean;
};

export const phases: Phase[] = [
  { id: 1, title: 'Diagnóstico e Inventario',           status: 'Completado', date: 'Jul 15',     responsible: 'Ana García' },
  { id: 2, title: 'Diseño de Blueprint y Arquitectura', status: 'Completado', date: 'Ago 10',     responsible: 'Carlos Méndez' },
  { id: 3, title: 'Implementación ERP Odoo',            status: 'Completado', date: 'Sep 05',     responsible: 'Laura Torres' },
  { id: 4, title: 'Adopción y Capacitación',            status: 'En Curso',   date: 'En proceso', responsible: 'Roberto Flores', active: true },
  { id: 5, title: 'Escalamiento e Integración IA',      status: 'Pendiente',  date: 'Oct 20',     responsible: 'Equipo Syner' },
];

export type Deliverable = {
  id: number;
  name: string;
  type: 'PDF' | 'PPTX' | 'PBIX' | 'XLSX' | 'DOCX';
  size: string;
  date: string;
  phase: number;
};

export const deliverables: Deliverable[] = [
  { id: 1, name: 'Diagnóstico 360 — Informe ejecutivo',       type: 'PDF',  size: '2.4 MB', date: 'Jul 18', phase: 1 },
  { id: 2, name: 'Blueprint operativo v2.1',                  type: 'PPTX', size: '8.1 MB', date: 'Ago 12', phase: 2 },
  { id: 3, name: 'Dashboard Power BI — Financiero',           type: 'PBIX', size: '12 MB',  date: 'Sep 01', phase: 3 },
  { id: 4, name: 'Manual de capacitación ERP',                type: 'PDF',  size: '5.6 MB', date: 'Sep 28', phase: 4 },
  { id: 5, name: 'Análisis de brechas RRHH',                  type: 'XLSX', size: '1.1 MB', date: 'Ago 25', phase: 2 },
  { id: 6, name: 'Roadmap de integración IA',                 type: 'DOCX', size: '3.2 MB', date: 'Oct 02', phase: 5 },
  { id: 7, name: 'Reporte de adopción — Semana 12',           type: 'PDF',  size: '1.8 MB', date: 'Oct 05', phase: 4 },
  { id: 8, name: 'Indicadores operativos — Dashboard',        type: 'PBIX', size: '9.4 MB', date: 'Sep 15', phase: 3 },
];

export type ChangelogEntry = {
  id: number;
  description: string;
  user: string;
  initials: string;
  timestamp: string;
  relative: string;
};

export const changelog: ChangelogEntry[] = [
  { id: 1, description: 'Se aprobó blueprint operativo v2.1 con directivos de GIN.',          user: 'Arturo Villanueva', initials: 'AV', timestamp: '2026-10-05 14:30', relative: 'Hace 2h' },
  { id: 2, description: 'Reunión de avance fase 4 — se reprogramaron 2 tareas por retrasos.', user: 'Ana García',        initials: 'AG', timestamp: '2026-10-05 11:15', relative: 'Hace 5h' },
  { id: 3, description: 'Entregable "Reporte de adopción S12" cargado al Vault.',             user: 'Carlos Méndez',     initials: 'CM', timestamp: '2026-10-04 17:00', relative: 'Ayer' },
  { id: 4, description: 'KPI "Procesos automatizados" actualizado de 24 a 27.',               user: 'Laura Torres',      initials: 'LT', timestamp: '2026-10-04 10:45', relative: 'Ayer' },
  { id: 5, description: 'Se escaló riesgo: 2 OKRs sin responsable asignado.',                 user: 'Roberto Flores',    initials: 'RF', timestamp: '2026-10-03 16:20', relative: 'Hace 2d' },
  { id: 6, description: 'Firma digital del acta de inicio Fase 4.',                           user: 'Arturo Villanueva', initials: 'AV', timestamp: '2026-10-02 09:00', relative: 'Hace 3d' },
  { id: 7, description: 'Dashboards Power BI conectados a fuente de datos real.',              user: 'Carlos Méndez',     initials: 'CM', timestamp: '2026-10-01 15:30', relative: 'Hace 4d' },
];

export type Task = {
  id: number;
  title: string;
  done: boolean;
  assignee: string;
};

export const tasks: Task[] = [
  { id: 1, title: 'Configurar módulo de inventarios en Odoo',   done: true,  assignee: 'Laura T.' },
  { id: 2, title: 'Capacitar equipo de compras (sesión 3/5)',   done: true,  assignee: 'Roberto F.' },
  { id: 3, title: 'Validar dashboard de KPIs con dirección',   done: false, assignee: 'Arturo V.' },
  { id: 4, title: 'Migrar catálogo de proveedores legacy',      done: false, assignee: 'Carlos M.' },
  { id: 5, title: 'Documentar SOP de cierre contable',          done: false, assignee: 'Ana G.' },
];

export const efficiencyData = [
  { month: 'May', value: 42 },
  { month: 'Jun', value: 48 },
  { month: 'Jul', value: 55 },
  { month: 'Ago', value: 59 },
  { month: 'Sep', value: 63 },
  { month: 'Oct', value: 67 },
];

// KPI detail table (for KPIs view)
export type KPIDetail = {
  id: number;
  name: string;
  area: 'Finanzas' | 'Operaciones' | 'RRHH';
  baseline: string;
  actual: string;
  meta: string;
  percent: number;
};

export const kpiDetails: KPIDetail[] = [
  { id: 1, name: 'Costo operativo / ingreso',     area: 'Finanzas',     baseline: '38%',     actual: '31%',     meta: '28%',     percent: 70 },
  { id: 2, name: 'Margen EBITDA',                  area: 'Finanzas',     baseline: '12%',     actual: '16%',     meta: '18%',     percent: 67 },
  { id: 3, name: 'Ciclo order-to-cash',            area: 'Operaciones',  baseline: '45 días', actual: '32 días', meta: '25 días', percent: 65 },
  { id: 4, name: 'Procesos automatizados',         area: 'Operaciones',  baseline: '12',      actual: '27',      meta: '34',      percent: 79 },
  { id: 5, name: 'Tasa de adopción tecnológica',   area: 'RRHH',         baseline: '45%',     actual: '82%',     meta: '90%',     percent: 82 },
  { id: 6, name: 'Índice de satisfacción interna', area: 'RRHH',         baseline: '3.2',     actual: '4.1',     meta: '4.5',     percent: 69 },
  { id: 7, name: 'Inventario dead stock',          area: 'Operaciones',  baseline: '$ 2.1M',  actual: '$ 0.9M',  meta: '$ 0.5M',  percent: 75 },
  { id: 8, name: 'Rotación de personal clave',     area: 'RRHH',         baseline: '22%',     actual: '14%',     meta: '10%',     percent: 67 },
];
