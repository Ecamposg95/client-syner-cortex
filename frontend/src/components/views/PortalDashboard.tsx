import React, { useEffect, useMemo, useState } from 'react';
import {
  Loader2, Activity, Gauge, ListChecks, FileText, AlertTriangle,
  Scale, Inbox, Calendar,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import apiClient from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { ProgressBar } from '../ui/ProgressBar';

// ── API shapes ──────────────────────────────────────────────────────────
interface Engagement {
  id: number;
  title: string;
  objective: string;
  status: string;
  start_date: string | null;
  end_date: string | null;
}

interface DiagnosisDimension {
  name: string;
  rating: number;
  recommendations?: string;
}

interface Diagnosis {
  diagnosis_id: number;
  average_rating: number;
  dimensions: DiagnosisDimension[];
  top_weaknesses: { name: string; rating: number }[];
}

interface PhaseStat {
  total: number;
  done: number;
  in_progress: number;
  percent: number;
}

interface Roadmap {
  roadmap_id: number;
  overall_percent: number;
  phases: { '30'?: PhaseStat; '60'?: PhaseStat; '90'?: PhaseStat };
}

interface DeliverablesSummary {
  engagement_by_status: Record<string, number>;
  documents_by_status: Record<string, number>;
  document_total: number;
}

interface CriticalFinding {
  id: number;
  title: string;
  area: string;
  criticality: string;
  recommendation: string;
}

interface OpenDecision {
  id: number;
  title: string;
  context: string;
  syner_recommendation: string;
  deadline: string | null;
}

interface KpiItem {
  id: number;
  name: string;
  value: string | number;
  timestamp: string;
}

interface PortalSummary {
  organization_id: number;
  engagement: Engagement | null;
  diagnosis: Diagnosis | null;
  roadmap: Roadmap | null;
  deliverables: DeliverablesSummary;
  critical_findings: CriticalFinding[];
  open_decisions: OpenDecision[];
  kpis: KpiItem[];
}

const BAR_COLORS = ['#6366f1', '#0ea5e9', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6', '#f43f5e'];

const engagementBadge = (status: string): { variant: 'active' | 'completed' | 'pending' | 'risk'; label: string } => {
  switch (status) {
    case 'ACTIVE': return { variant: 'active', label: 'Activo' };
    case 'COMPLETED': return { variant: 'completed', label: 'Completado' };
    case 'CANCELLED': return { variant: 'risk', label: 'Cancelado' };
    case 'ON_HOLD': return { variant: 'pending', label: 'En pausa' };
    case 'DRAFT': return { variant: 'pending', label: 'Borrador' };
    default: return { variant: 'pending', label: status };
  }
};

const fmtDate = (d: string | null): string => {
  if (!d) return '—';
  try {
    return new Date(d).toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return d;
  }
};

const ChartTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs shadow-float"
      style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--ink)' }}
    >
      <div className="font-semibold">{label}</div>
      <div className="text-[var(--muted)]">{Number(payload[0].value).toFixed(1)} / 5</div>
    </div>
  );
};

export const PortalDashboard: React.FC = () => {
  const [summary, setSummary] = useState<PortalSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // The /portal/summary endpoint requires the X-Organization-ID header, which the
  // API client derives from the active organization. Wait for it to be selected
  // (avoids a 422 race on first load) and refetch whenever it changes.
  const activeOrgId = useAuthStore((s) => s.currentOrgRelation?.organization_id);

  useEffect(() => {
    if (!activeOrgId) return;
    setLoading(true);
    setError(null);
    apiClient
      .get<PortalSummary>('/portal/summary')
      .then((res) => setSummary(res.data))
      .catch((e) => {
        console.error(e);
        setError('No se pudo cargar el estado de la consultoría.');
      })
      .finally(() => setLoading(false));
  }, [activeOrgId]);

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-4">
        <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
        <p className="text-sm text-[var(--muted)]">Cargando estado de la consultoría...</p>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <Card className="p-12 flex flex-col items-center justify-center gap-3 text-center">
        <Inbox size={40} className="text-[var(--muted-2)]" />
        <p className="text-sm text-[var(--muted)]">{error || 'Estado no disponible.'}</p>
      </Card>
    );
  }

  const { engagement, diagnosis, roadmap, deliverables, critical_findings, open_decisions, kpis } = summary;

  return (
    <div className="space-y-8">
      {/* ── Header ── */}
      <EngagementHeader engagement={engagement} />

      {/* ── Salud del diagnóstico ── */}
      <DiagnosisSection diagnosis={diagnosis} />

      {/* ── Avance del roadmap ── */}
      <RoadmapSection roadmap={roadmap} />

      {/* ── Entregables ── */}
      <DeliverablesSection deliverables={deliverables} />

      {/* ── Hallazgos críticos ── */}
      <FindingsSection findings={critical_findings} />

      {/* ── Decisiones pendientes ── */}
      <DecisionsSection decisions={open_decisions} />

      {/* ── KPIs ── */}
      <KpisSection kpis={kpis} />
    </div>
  );
};

// ── Sections ────────────────────────────────────────────────────────────
const SectionTitle: React.FC<{ icon: React.ReactNode; title: string; subtitle?: string }> = ({ icon, title, subtitle }) => (
  <div className="flex items-center gap-2">
    <span className="text-[var(--accent)]">{icon}</span>
    <div>
      <h3 className="font-bold text-lg text-[var(--ink)]">{title}</h3>
      {subtitle && <p className="text-xs text-[var(--muted)]">{subtitle}</p>}
    </div>
  </div>
);

const EngagementHeader: React.FC<{ engagement: Engagement | null }> = ({ engagement }) => {
  if (!engagement) {
    return (
      <Card className="p-6 flex items-center gap-3">
        <Inbox size={22} className="text-[var(--muted-2)]" />
        <div>
          <h2 className="font-extrabold text-2xl text-[var(--ink)]">Sin engagement activo</h2>
          <p className="text-sm text-[var(--muted)]">Aún no hay un proyecto de consultoría asociado a tu organización.</p>
        </div>
      </Card>
    );
  }
  const badge = engagementBadge(engagement.status);
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="space-y-2">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className="font-extrabold text-2xl text-[var(--ink)]">{engagement.title}</h2>
          <Badge variant={badge.variant} label={badge.label} />
        </div>
        {engagement.objective && (
          <p className="text-sm text-[var(--muted)] max-w-2xl">{engagement.objective}</p>
        )}
      </div>
      <div className="flex items-center gap-2 text-xs font-mono text-[var(--muted)]">
        <Calendar size={14} />
        <span>{fmtDate(engagement.start_date)} → {fmtDate(engagement.end_date)}</span>
      </div>
    </div>
  );
};

const DiagnosisSection: React.FC<{ diagnosis: Diagnosis | null }> = ({ diagnosis }) => {
  const weakNames = useMemo(
    () => new Set((diagnosis?.top_weaknesses ?? []).map((w) => w.name)),
    [diagnosis],
  );
  const data = useMemo(
    () => (diagnosis?.dimensions ?? []).map((d) => ({ name: d.name, rating: d.rating, weak: weakNames.has(d.name) })),
    [diagnosis, weakNames],
  );

  return (
    <section className="space-y-3">
      <SectionTitle icon={<Activity size={18} />} title="Salud del diagnóstico" subtitle="Calificación por dimensión (0–5)" />
      {!diagnosis ? (
        <Card className="p-8 text-center text-sm text-[var(--muted)]">Aún no hay diagnóstico disponible.</Card>
      ) : (
        <Card className="p-5">
          <div className="flex flex-col lg:flex-row gap-6 items-stretch">
            <div className="flex flex-col items-center justify-center px-6 py-4 rounded-xl shrink-0" style={{ background: 'var(--accent-tint)' }}>
              <Gauge size={20} className="text-[var(--accent-strong)] mb-1" />
              <div className="text-4xl font-extrabold text-[var(--accent-strong)]">{diagnosis.average_rating.toFixed(1)}</div>
              <div className="text-[10px] uppercase tracking-wide text-[var(--muted)]">promedio / 5</div>
            </div>
            <div className="flex-1 w-full" style={{ height: Math.max(140, data.length * 40) }}>
              {data.length === 0 ? (
                <p className="text-xs text-[var(--muted)]">Sin dimensiones.</p>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
                    <XAxis type="number" domain={[0, 5]} stroke="var(--muted-2)" fontSize={11} />
                    <YAxis type="category" dataKey="name" width={150} stroke="var(--muted-2)" fontSize={11} tick={{ fill: 'var(--muted)' }} />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: 'var(--accent-tint)' }} />
                    <Bar dataKey="rating" radius={[0, 6, 6, 0]} barSize={18}>
                      {data.map((d, i) => (
                        <Cell key={i} fill={d.weak ? '#f43f5e' : BAR_COLORS[i % BAR_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
          {diagnosis.top_weaknesses.length > 0 && (
            <div className="mt-4 pt-4 border-t border-[var(--border)] flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wide">Debilidades clave:</span>
              {diagnosis.top_weaknesses.map((w) => (
                <span key={w.name} className="status-badge status-badge--risk">
                  {w.name} · {w.rating.toFixed(1)}
                </span>
              ))}
            </div>
          )}
        </Card>
      )}
    </section>
  );
};

const PhaseBar: React.FC<{ label: string; stat?: PhaseStat }> = ({ label, stat }) => {
  const percent = stat?.percent ?? 0;
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <span className="font-medium text-[var(--muted)]">Fase {label} días</span>
        <span className="font-bold text-[var(--accent-strong)]">{Math.round(percent)}%</span>
      </div>
      <ProgressBar percent={percent} />
      {stat && (
        <p className="text-[10px] text-[var(--muted-2)] font-mono">
          {stat.done}/{stat.total} listas · {stat.in_progress} en curso
        </p>
      )}
    </div>
  );
};

const RoadmapSection: React.FC<{ roadmap: Roadmap | null }> = ({ roadmap }) => (
  <section className="space-y-3">
    <SectionTitle icon={<ListChecks size={18} />} title="Avance del roadmap" subtitle="Progreso por horizonte" />
    {!roadmap ? (
      <Card className="p-8 text-center text-sm text-[var(--muted)]">Aún no hay roadmap publicado.</Card>
    ) : (
      <Card className="p-5 space-y-5">
        <div className="space-y-1.5">
          <div className="flex justify-between text-sm">
            <span className="font-semibold text-[var(--ink)]">Avance general</span>
            <span className="font-bold text-[var(--accent-strong)]">{Math.round(roadmap.overall_percent)}%</span>
          </div>
          <ProgressBar percent={roadmap.overall_percent} />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-2 border-t border-[var(--border)]">
          <PhaseBar label="30" stat={roadmap.phases['30']} />
          <PhaseBar label="60" stat={roadmap.phases['60']} />
          <PhaseBar label="90" stat={roadmap.phases['90']} />
        </div>
      </Card>
    )}
  </section>
);

const DeliverablesSection: React.FC<{ deliverables: DeliverablesSummary }> = ({ deliverables }) => {
  const entries = Object.entries(deliverables.documents_by_status ?? {});
  return (
    <section className="space-y-3">
      <SectionTitle icon={<FileText size={18} />} title="Entregables" subtitle={`${deliverables.document_total} documentos en total`} />
      <Card className="p-5">
        {entries.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">Aún no hay documentos.</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {entries.map(([status, count]) => (
              <div key={status} className="rounded-xl p-4 text-center" style={{ background: 'var(--surface-2)' }}>
                <div className="text-2xl font-extrabold text-[var(--ink)]">{count}</div>
                <div className="text-[10px] uppercase tracking-wide text-[var(--muted)] mt-1">{status}</div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </section>
  );
};

const findingBadge = (criticality: string): { variant: 'active' | 'completed' | 'pending' | 'risk'; label: string } => {
  switch (criticality) {
    case 'CRITICAL': return { variant: 'risk', label: 'Crítico' };
    case 'HIGH': return { variant: 'pending', label: 'Alto' };
    default: return { variant: 'pending', label: criticality };
  }
};

const FindingsSection: React.FC<{ findings: CriticalFinding[] }> = ({ findings }) => (
  <section className="space-y-3">
    <SectionTitle icon={<AlertTriangle size={18} />} title="Hallazgos críticos" />
    {findings.length === 0 ? (
      <Card className="p-8 text-center text-sm text-[var(--muted)]">Sin hallazgos críticos abiertos.</Card>
    ) : (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {findings.map((f) => {
          const badge = findingBadge(f.criticality);
          return (
            <Card key={f.id} className="p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h4 className="font-bold text-[var(--ink)] leading-tight">{f.title}</h4>
                  <span className="text-[10px] uppercase tracking-wider text-[var(--muted-2)] font-semibold">{f.area}</span>
                </div>
                <Badge variant={badge.variant} label={badge.label} />
              </div>
              {f.recommendation && (
                <div className="mt-3 p-3 rounded-lg text-sm" style={{ background: 'var(--surface-2)' }}>
                  <span className="font-semibold block text-[var(--accent-strong)] mb-1">Recomendación:</span>
                  <p className="text-[var(--muted)]">{f.recommendation}</p>
                </div>
              )}
            </Card>
          );
        })}
      </div>
    )}
  </section>
);

const DecisionsSection: React.FC<{ decisions: OpenDecision[] }> = ({ decisions }) => (
  <section className="space-y-3">
    <SectionTitle icon={<Scale size={18} />} title="Decisiones pendientes" />
    {decisions.length === 0 ? (
      <Card className="p-8 text-center text-sm text-[var(--muted)]">No hay decisiones pendientes.</Card>
    ) : (
      <div className="grid grid-cols-1 gap-4">
        {decisions.map((d) => (
          <Card key={d.id} className="p-5 border-l-4" style={{ borderLeftColor: 'var(--warn)' }}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <h4 className="font-bold text-[var(--ink)]">{d.title}</h4>
              {d.deadline && (
                <span className="inline-flex items-center gap-1 text-xs font-mono text-[var(--muted)]">
                  <Calendar size={12} /> {fmtDate(d.deadline)}
                </span>
              )}
            </div>
            {d.context && <p className="text-sm text-[var(--muted)] mt-1">{d.context}</p>}
            {d.syner_recommendation && (
              <div className="mt-3 p-3 rounded-lg text-sm" style={{ background: 'var(--surface-2)' }}>
                <span className="font-semibold block text-[var(--accent-strong)] mb-1">Recomendación Syner:</span>
                <p className="text-[var(--muted)]">{d.syner_recommendation}</p>
              </div>
            )}
          </Card>
        ))}
      </div>
    )}
  </section>
);

const KpisSection: React.FC<{ kpis: KpiItem[] }> = ({ kpis }) => (
  <section className="space-y-3">
    <SectionTitle icon={<Gauge size={18} />} title="KPIs" />
    {kpis.length === 0 ? (
      <Card className="p-8 text-center text-sm text-[var(--muted)]">Aún no hay KPIs registrados.</Card>
    ) : (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {kpis.map((k) => (
          <Card key={k.id} className="p-4">
            <p className="text-xs text-[var(--muted)] uppercase tracking-wide">{k.name}</p>
            <p className="text-2xl font-extrabold text-[var(--ink)] mt-1">{String(k.value)}</p>
          </Card>
        ))}
      </div>
    )}
  </section>
);

export default PortalDashboard;
