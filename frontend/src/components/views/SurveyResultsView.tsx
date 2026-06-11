import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Loader2, AlertTriangle, Sparkles, MessageSquareQuote,
  BarChart3, Gauge, Inbox,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import apiClient from '../../api/client';
import { Card } from '../ui/Card';

// ── API shapes ──────────────────────────────────────────────────────────
type QuestionType = 'SINGLE_CHOICE' | 'MULTI_CHOICE' | 'LINEAR_SCALE' | 'OPEN_TEXT';

interface ResultQuestion {
  question_id: number;
  order: number;
  section_title: string | null;
  text: string;
  question_type: QuestionType;
  option_counts?: Record<string, number>;
  average?: number | null;
  distribution?: Record<string, number>;
  answers?: string[];
}

interface DiagnosticReading {
  pattern: string;
  suggestion: string;
  triggered: boolean;
  detail: string;
}

interface CampaignResults {
  campaign_id: number;
  survey_title: string;
  response_count: number;
  questions: ResultQuestion[];
  diagnostic_readings: DiagnosticReading[];
}

const BAR_COLORS = ['#6366f1', '#0ea5e9', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6', '#f43f5e'];

const ChartTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs shadow-float"
      style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--ink)' }}
    >
      <div className="font-semibold">{label}</div>
      <div className="text-[var(--muted)]">{payload[0].value} respuestas</div>
    </div>
  );
};

export const SurveyResultsView: React.FC = () => {
  const { campaignId } = useParams<{ campaignId: string }>();
  const navigate = useNavigate();

  const [results, setResults] = useState<CampaignResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!campaignId) return;
    setLoading(true);
    apiClient
      .get<CampaignResults>(`/campaigns/${campaignId}/results`)
      .then((res) => setResults(res.data))
      .catch((e) => {
        console.error(e);
        setError('No se pudieron cargar los resultados.');
      })
      .finally(() => setLoading(false));
  }, [campaignId]);

  const triggeredCount = useMemo(
    () => results?.diagnostic_readings.filter((r) => r.triggered).length ?? 0,
    [results],
  );

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-4">
        <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
        <p className="text-sm text-[var(--muted)]">Cargando resultados...</p>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="space-y-6">
        <BackButton onClick={() => navigate('/surveys')} />
        <div className="text-center py-16">
          <p className="text-[var(--muted)]">{error || 'Resultados no disponibles.'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <BackButton onClick={() => navigate('/surveys')} />
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className="p-2.5 rounded-xl text-white"
              style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
            >
              <BarChart3 size={24} />
            </div>
            <div>
              <h2 className="font-extrabold text-2xl">{results.survey_title}</h2>
              <p className="text-sm text-[var(--muted)]">Resultados de la campaña</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-extrabold text-[var(--accent)]">{results.response_count}</div>
            <div className="text-xs text-[var(--muted)] uppercase tracking-wide">respuestas</div>
          </div>
        </div>
      </div>

      {/* Empty state */}
      {results.response_count === 0 ? (
        <Card className="p-12 flex flex-col items-center justify-center gap-3 text-center">
          <Inbox size={40} className="text-[var(--muted-2)]" />
          <h3 className="font-bold text-lg text-[var(--ink)]">Aún no hay respuestas</h3>
          <p className="text-sm text-[var(--muted)] max-w-md">
            Comparte el enlace público de la campaña para empezar a recibir respuestas. Los
            resultados y la lectura diagnóstica aparecerán aquí automáticamente.
          </p>
        </Card>
      ) : (
        <>
          {/* ── Lectura Diagnóstica ── */}
          {results.diagnostic_readings.length > 0 && (
            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles size={18} className="text-[var(--accent)]" />
                <h3 className="font-bold text-lg text-[var(--ink)]">Lectura Diagnóstica</h3>
                {triggeredCount > 0 && (
                  <span className="status-badge status-badge--risk">
                    {triggeredCount} {triggeredCount === 1 ? 'patrón detectado' : 'patrones detectados'}
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {results.diagnostic_readings.map((reading, idx) => (
                  <DiagnosticCard key={idx} reading={reading} />
                ))}
              </div>
            </section>
          )}

          {/* ── Questions ── */}
          <section className="space-y-5">
            {results.questions.map((q, idx) => {
              const prevSection = idx > 0 ? results.questions[idx - 1].section_title : null;
              const showSection = q.section_title && q.section_title !== prevSection;
              return (
                <React.Fragment key={q.question_id}>
                  {showSection && (
                    <div className="pt-2">
                      <span className="text-xs font-semibold uppercase tracking-wider text-[var(--muted-2)]">
                        {q.section_title}
                      </span>
                      <div className="mt-1 h-px w-full" style={{ background: 'var(--border)' }} />
                    </div>
                  )}
                  <QuestionCard question={q} index={idx} />
                </React.Fragment>
              );
            })}
          </section>
        </>
      )}
    </div>
  );
};

// ── Sub-components ──────────────────────────────────────────────────────
const BackButton: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className="inline-flex items-center gap-1.5 text-sm font-medium transition-colors"
    style={{ color: 'var(--muted)' }}
  >
    <ArrowLeft size={16} />
    Volver a encuestas
  </button>
);

const DiagnosticCard: React.FC<{ reading: DiagnosticReading }> = ({ reading }) => {
  if (reading.triggered) {
    return (
      <Card
        className="p-5"
        // override border to amber/accent for the highlighted alert
      >
        <div
          className="rounded-lg -m-5 p-5"
          style={{ borderLeft: '4px solid #f59e0b', background: 'rgba(245, 158, 11, 0.06)' }}
        >
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg text-white shrink-0" style={{ background: 'linear-gradient(135deg, #f59e0b, #d97706)' }}>
              <AlertTriangle size={18} />
            </div>
            <div className="min-w-0">
              <h4 className="font-bold text-base text-[var(--ink)] leading-tight">{reading.pattern}</h4>
              <p className="text-sm text-[var(--muted)] mt-1 leading-relaxed">{reading.suggestion}</p>
              {reading.detail && (
                <p className="text-xs font-mono text-[var(--muted-2)] mt-2 break-words">{reading.detail}</p>
              )}
            </div>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-5 opacity-70">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg shrink-0" style={{ background: 'var(--surface-2)', color: 'var(--muted-2)' }}>
          <Sparkles size={18} />
        </div>
        <div className="min-w-0">
          <h4 className="font-semibold text-sm text-[var(--muted)] leading-tight">{reading.pattern}</h4>
          <p className="text-xs text-[var(--muted-2)] mt-1">No se detectó este patrón en las respuestas.</p>
          {reading.detail && (
            <p className="text-xs font-mono text-[var(--muted-2)] mt-1.5 break-words">{reading.detail}</p>
          )}
        </div>
      </div>
    </Card>
  );
};

const QuestionCard: React.FC<{ question: ResultQuestion; index: number }> = ({ question, index }) => {
  return (
    <Card className="p-5">
      <div className="flex items-start gap-2 mb-4">
        <span className="text-xs font-bold text-[var(--muted-2)] mt-0.5">{index + 1}.</span>
        <div className="min-w-0">
          <h4 className="font-bold text-base text-[var(--ink)] leading-tight">{question.text}</h4>
          <span className="text-[10px] uppercase tracking-wider text-[var(--muted-2)] font-semibold">
            {QUESTION_TYPE_LABEL[question.question_type]}
          </span>
        </div>
      </div>

      {(question.question_type === 'SINGLE_CHOICE' || question.question_type === 'MULTI_CHOICE') && (
        <ChoiceChart counts={question.option_counts ?? {}} />
      )}

      {question.question_type === 'LINEAR_SCALE' && (
        <ScaleResult average={question.average ?? null} distribution={question.distribution ?? {}} />
      )}

      {question.question_type === 'OPEN_TEXT' && <OpenTextAnswers answers={question.answers ?? []} />}
    </Card>
  );
};

const QUESTION_TYPE_LABEL: Record<QuestionType, string> = {
  SINGLE_CHOICE: 'Opción única',
  MULTI_CHOICE: 'Opción múltiple',
  LINEAR_SCALE: 'Escala lineal',
  OPEN_TEXT: 'Texto abierto',
};

const ChoiceChart: React.FC<{ counts: Record<string, number> }> = ({ counts }) => {
  const data = useMemo(
    () => Object.entries(counts).map(([name, value]) => ({ name, value })),
    [counts],
  );
  if (data.length === 0) {
    return <p className="text-xs text-[var(--muted)]">Sin datos.</p>;
  }
  // Use a vertical layout so option labels stay readable regardless of count.
  const chartHeight = Math.max(120, data.length * 44);
  return (
    <div style={{ width: '100%', height: chartHeight }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
          <XAxis type="number" allowDecimals={false} stroke="var(--muted-2)" fontSize={11} />
          <YAxis
            type="category"
            dataKey="name"
            width={140}
            stroke="var(--muted-2)"
            fontSize={11}
            tick={{ fill: 'var(--muted)' }}
          />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: 'var(--accent-tint)' }} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={20}>
            {data.map((_, i) => (
              <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

const ScaleResult: React.FC<{ average: number | null; distribution: Record<string, number> }> = ({
  average,
  distribution,
}) => {
  const data = useMemo(() => {
    const keys = ['1', '2', '3', '4', '5'];
    const present = Object.keys(distribution);
    const allKeys = present.length ? Array.from(new Set([...keys, ...present])) : keys;
    return allKeys
      .sort((a, b) => Number(a) - Number(b))
      .map((k) => ({ name: k, value: distribution[k] ?? 0 }));
  }, [distribution]);

  return (
    <div className="flex flex-col sm:flex-row gap-5 items-center">
      <div className="flex flex-col items-center justify-center px-5 py-3 rounded-xl shrink-0" style={{ background: 'var(--accent-tint)' }}>
        <Gauge size={18} className="text-[var(--accent-strong)] mb-1" />
        <div className="text-3xl font-extrabold text-[var(--accent-strong)]">
          {average != null ? average.toFixed(1) : '—'}
        </div>
        <div className="text-[10px] uppercase tracking-wide text-[var(--muted)]">promedio</div>
      </div>
      <div className="flex-1 w-full" style={{ height: 140 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
            <XAxis dataKey="name" stroke="var(--muted-2)" fontSize={11} />
            <YAxis allowDecimals={false} stroke="var(--muted-2)" fontSize={11} width={28} />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: 'var(--accent-tint)' }} />
            <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={32}>
              {data.map((_, i) => (
                <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const OpenTextAnswers: React.FC<{ answers: string[] }> = ({ answers }) => {
  if (answers.length === 0) {
    return <p className="text-xs text-[var(--muted)]">Sin respuestas de texto.</p>;
  }
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-xs text-[var(--muted)] mb-1">
        <MessageSquareQuote size={14} />
        {answers.length} {answers.length === 1 ? 'respuesta' : 'respuestas'}
      </div>
      {answers.map((answer, i) => (
        <div
          key={i}
          className="px-3 py-2.5 rounded-lg text-sm italic"
          style={{ background: 'var(--surface-2)', color: 'var(--muted)', borderLeft: '3px solid var(--border)' }}
        >
          “{answer}”
        </div>
      ))}
    </div>
  );
};

export default SurveyResultsView;
