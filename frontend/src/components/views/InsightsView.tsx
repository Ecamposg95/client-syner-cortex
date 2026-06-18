import React, { useEffect, useState } from 'react';
import { Card } from '../ui/Card';
import {
  Lightbulb, Loader2, AlertTriangle, Sparkles, Zap, Rocket,
  TrendingUp, MinusCircle, ChevronRight,
} from 'lucide-react';
import apiClient from '../../api/client';
import { useAuthStore } from '../../store/authStore';

interface Insight {
  id: number;
  title: string;
  description: string | null;
  category: string | null;
  impact: string;
  effort: string;
  priority_score: number;
  quadrant: string | null;
  status: string;
  is_critical_alarm: boolean;
  recommended_action: string | null;
  source_type: string;
  source_ref: number | null;
  created_at: string;
}

interface MatrixCell {
  quadrant: string;
  count: number;
  items: Insight[];
}

interface Matrix {
  quadrants: MatrixCell[];
  total: number;
  critical_alarms: number;
}

const QUADRANT_META: Record<string, { label: string; hint: string; icon: any; color: string }> = {
  QUICK_WIN:     { label: 'Quick Wins',      hint: 'Alto impacto · bajo esfuerzo', icon: Zap,        color: 'var(--pos)' },
  MAJOR_PROJECT: { label: 'Proyectos Mayores', hint: 'Alto impacto · alto esfuerzo', icon: Rocket,    color: 'var(--accent)' },
  INCREMENTAL:   { label: 'Incrementales',   hint: 'Bajo impacto · bajo esfuerzo', icon: TrendingUp, color: 'var(--warn)' },
  LOW_PRIORITY:  { label: 'Baja Prioridad',  hint: 'Bajo impacto · alto esfuerzo', icon: MinusCircle, color: 'var(--muted)' },
};

const LEVEL_COLOR: Record<string, string> = {
  HIGH:   'text-red-500 bg-red-500/10',
  MEDIUM: 'text-yellow-500 bg-yellow-500/10',
  LOW:    'text-blue-500 bg-blue-500/10',
};

const STATUS_FLOW: { value: string; label: string }[] = [
  { value: 'ACKNOWLEDGED', label: 'Reconocer' },
  { value: 'IN_PROGRESS', label: 'En progreso' },
  { value: 'RESOLVED', label: 'Resolver' },
  { value: 'DISMISSED', label: 'Descartar' },
];

export const InsightsView: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const isCrew = user?.user_type === 'SYNER_CREW';

  const [insights, setInsights] = useState<Insight[]>([]);
  const [matrix, setMatrix] = useState<Matrix | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [patchingId, setPatchingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = async () => {
    const [iRes, mRes] = await Promise.all([
      apiClient.get('/insights'),
      apiClient.get('/insights/matrix'),
    ]);
    setInsights(iRes.data);
    setMatrix(mRes.data);
  };

  useEffect(() => {
    (async () => {
      try {
        await fetchAll();
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      await apiClient.post('/insights/generate');
      await fetchAll();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'No se pudo generar insights');
    } finally {
      setGenerating(false);
    }
  };

  const handleStatus = async (id: number, status: string) => {
    setPatchingId(id);
    try {
      await apiClient.patch(`/insights/${id}`, { status });
      await fetchAll();
    } catch (e) {
      console.error(e);
    } finally {
      setPatchingId(null);
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-[var(--accent)]" /></div>;

  const alarms = insights.filter((i) => i.is_critical_alarm && ['NEW', 'ACKNOWLEDGED', 'IN_PROGRESS'].includes(i.status));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="font-bold text-2xl flex items-center gap-2">
            <Lightbulb className="text-[var(--accent)]" /> Insights & Recomendaciones
          </h2>
          <p className="text-sm text-[var(--muted)]">
            Recomendaciones priorizadas a partir de hallazgos, riesgos y diagnóstico
          </p>
        </div>
        {isCrew && (
          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-semibold text-white transition-colors disabled:opacity-50"
            style={{ background: 'var(--accent)' }}
          >
            {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            {generating ? 'Generando...' : 'Generar insights'}
          </button>
        )}
      </div>

      {error && (
        <div className="px-4 py-3 rounded-lg text-sm" style={{ background: 'var(--neg-tint, rgba(239,68,68,0.1))', color: 'var(--neg, #ef4444)' }}>
          {error}
        </div>
      )}

      {/* Critical alarms */}
      {alarms.length > 0 && (
        <Card className="p-5 border-l-4" style={{ borderLeftColor: 'var(--neg, #ef4444)' }}>
          <h3 className="font-bold text-base flex items-center gap-2 text-red-500 mb-3">
            <AlertTriangle size={18} /> Alarmas críticas ({alarms.length})
          </h3>
          <div className="space-y-2">
            {alarms.map((a) => (
              <div key={a.id} className="flex items-center gap-2 text-sm">
                <ChevronRight size={14} className="text-red-500 flex-shrink-0" />
                <span className="font-medium text-[var(--ink)]">{a.title}</span>
                {a.category && <span className="text-[var(--muted-2)] text-xs">· {a.category}</span>}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Impact / Effort matrix */}
      {matrix && (
        <div>
          <h3 className="font-bold text-lg mb-1">Matriz Impacto / Esfuerzo</h3>
          <p className="text-xs text-[var(--muted)] mb-4">{matrix.total} insights activos priorizados por cuadrante</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {matrix.quadrants.map((cell) => {
              const meta = QUADRANT_META[cell.quadrant] || QUADRANT_META.INCREMENTAL;
              const Icon = meta.icon;
              return (
                <Card key={cell.quadrant} className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Icon size={18} style={{ color: meta.color }} />
                      <div>
                        <p className="font-bold text-sm text-[var(--ink)]">{meta.label}</p>
                        <p className="text-[10px] uppercase tracking-wide text-[var(--muted-2)]">{meta.hint}</p>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded-md text-xs font-bold" style={{ background: 'var(--surface-2)', color: meta.color }}>
                      {cell.count}
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    {cell.items.length === 0 && <p className="text-xs text-[var(--muted-2)] italic">Sin insights</p>}
                    {cell.items.slice(0, 5).map((i) => (
                      <div key={i.id} className="flex items-center gap-2 text-xs text-[var(--muted)]">
                        <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: meta.color }} />
                        <span className="truncate text-[var(--ink-2)]">{i.title}</span>
                      </div>
                    ))}
                    {cell.items.length > 5 && (
                      <p className="text-[10px] text-[var(--muted-2)]">+{cell.items.length - 5} más</p>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Prioritized list */}
      <div className="space-y-4">
        <h3 className="font-bold text-lg">Lista priorizada</h3>
        {insights.length === 0 && (
          <Card className="p-8 text-center">
            <Lightbulb className="mx-auto mb-3 text-[var(--muted-2)]" size={28} />
            <p className="text-sm text-[var(--muted)]">
              No hay insights todavía.{isCrew ? ' Usa "Generar insights" para crearlos desde los datos del cliente.' : ''}
            </p>
          </Card>
        )}
        {insights.map((i) => {
          const meta = QUADRANT_META[i.quadrant || 'INCREMENTAL'] || QUADRANT_META.INCREMENTAL;
          const dimmed = ['RESOLVED', 'DISMISSED'].includes(i.status);
          return (
            <Card key={i.id} className="p-5" style={{ opacity: dimmed ? 0.6 : 1 }}>
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex items-start gap-3">
                  <Lightbulb size={20} className="mt-0.5 flex-shrink-0" style={{ color: meta.color }} />
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-bold text-[var(--ink)]">{i.title}</h4>
                      {i.is_critical_alarm && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold text-red-500 bg-red-500/10 flex items-center gap-1">
                          <AlertTriangle size={10} /> CRÍTICO
                        </span>
                      )}
                    </div>
                    {i.category && <p className="text-xs text-[var(--muted-2)] mt-0.5">{i.category}</p>}
                  </div>
                </div>
                <span className="px-2 py-1 rounded-md text-[10px] font-bold whitespace-nowrap" style={{ background: 'var(--surface-2)', color: meta.color }}>
                  {meta.label}
                </span>
              </div>

              {i.description && <p className="text-sm text-[var(--muted)] mb-3">{i.description}</p>}

              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${LEVEL_COLOR[i.impact]}`}>Impacto: {i.impact}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${LEVEL_COLOR[i.effort]}`}>Esfuerzo: {i.effort}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-[var(--surface-2)] text-[var(--muted)]">{i.status}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[var(--surface-2)] text-[var(--muted-2)]">P{i.priority_score}</span>
              </div>

              {i.recommended_action && (
                <div className="p-3 rounded-lg bg-[var(--surface-2)] text-sm mb-3">
                  <span className="font-semibold block text-[var(--accent-strong)] mb-1">Acción recomendada</span>
                  <p className="text-[var(--ink)]">{i.recommended_action}</p>
                </div>
              )}

              {!dimmed && (
                <div className="flex flex-wrap items-center gap-2">
                  {STATUS_FLOW.filter((s) => s.value !== i.status).map((s) => (
                    <button
                      key={s.value}
                      type="button"
                      disabled={patchingId === i.id}
                      onClick={() => handleStatus(i.id, s.value)}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium border border-[var(--border)] text-[var(--ink-2)] hover:bg-[var(--surface-2)] transition-colors disabled:opacity-50"
                    >
                      {patchingId === i.id && <Loader2 size={12} className="animate-spin" />}
                      {s.label}
                    </button>
                  ))}
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
};
