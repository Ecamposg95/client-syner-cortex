import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Loader2, CheckCircle, AlertTriangle, Clock } from 'lucide-react';

// Local axios instance WITHOUT auth interceptors (public endpoint).
const publicApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

type QuestionType = 'SINGLE_CHOICE' | 'MULTI_CHOICE' | 'LINEAR_SCALE' | 'OPEN_TEXT';

interface SurveyQuestion {
  id: number;
  order: number;
  text: string;
  question_type: QuestionType;
  options?: string[];
  is_required: boolean;
  scale_min?: number;
  scale_max?: number;
  scale_min_label?: string;
  scale_max_label?: string;
}

interface SurveySection {
  id: number;
  title: string;
  order: number;
  questions: SurveyQuestion[];
}

interface Survey {
  campaign_id: number;
  title: string;
  description?: string;
  is_anonymous: boolean;
  collect_email: boolean;
  sections: SurveySection[];
}

type AnswerValue = string | number | string[] | undefined;

const inputStyle: React.CSSProperties = {
  background: 'var(--surface-2)',
  border: '1px solid var(--border)',
  color: 'var(--ink)',
};

export const PublicSurveyView: React.FC = () => {
  const { token } = useParams<{ token: string }>();

  const [loading, setLoading] = useState(true);
  const [survey, setSurvey] = useState<Survey | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [answers, setAnswers] = useState<Record<number, AnswerValue>>({});
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // question_id -> wrapper element, for scroll-to-error
  const questionRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const emailRef = useRef<HTMLDivElement | null>(null);
  const [invalidIds, setInvalidIds] = useState<Set<number>>(new Set());
  const [emailInvalid, setEmailInvalid] = useState(false);

  useEffect(() => {
    if (!token) {
      setLoadError('Token no proporcionado.');
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    publicApi
      .get(`/public/surveys/${token}`)
      .then((res) => {
        if (active) setSurvey(res.data);
      })
      .catch((err) => {
        if (!active) return;
        const detail = err?.response?.data?.detail;
        setLoadError(typeof detail === 'string' ? detail : 'Esta encuesta no está disponible.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [token]);

  const setAnswer = (qid: number, value: AnswerValue) => {
    setAnswers((prev) => ({ ...prev, [qid]: value }));
    if (invalidIds.has(qid)) {
      setInvalidIds((prev) => {
        const next = new Set(prev);
        next.delete(qid);
        return next;
      });
    }
  };

  const toggleMultiOption = (qid: number, option: string) => {
    setAnswers((prev) => {
      const current = Array.isArray(prev[qid]) ? (prev[qid] as string[]) : [];
      const next = current.includes(option)
        ? current.filter((o) => o !== option)
        : [...current, option];
      return { ...prev, [qid]: next };
    });
    if (invalidIds.has(qid)) {
      setInvalidIds((prev) => {
        const next = new Set(prev);
        next.delete(qid);
        return next;
      });
    }
  };

  const isAnswered = (q: SurveyQuestion): boolean => {
    const v = answers[q.id];
    if (v === undefined || v === null) return false;
    if (typeof v === 'string') return v.trim().length > 0;
    if (Array.isArray(v)) return v.length > 0;
    if (typeof v === 'number') return true;
    return false;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!survey || !token) return;

    setSubmitError(null);

    // Validate
    const missing = new Set<number>();
    survey.sections.forEach((section) => {
      section.questions.forEach((q) => {
        if (q.is_required && !isAnswered(q)) missing.add(q.id);
      });
    });

    const needEmail = survey.collect_email && email.trim().length === 0;

    setInvalidIds(missing);
    setEmailInvalid(needEmail);

    if (missing.size > 0 || needEmail) {
      setSubmitError('Por favor responde todas las preguntas requeridas.');
      // Scroll to first invalid element
      if (needEmail && emailRef.current) {
        emailRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        const firstId = survey.sections
          .flatMap((s) => s.questions)
          .find((q) => missing.has(q.id))?.id;
        if (firstId != null && questionRefs.current[firstId]) {
          questionRefs.current[firstId]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
      return;
    }

    // Build answers array (only answered questions).
    const payloadAnswers = survey.sections
      .flatMap((s) => s.questions)
      .filter((q) => isAnswered(q))
      .map((q) => {
        const v = answers[q.id];
        if (q.question_type === 'MULTI_CHOICE') {
          return { question_id: q.id, value_options: v as string[] };
        }
        if (q.question_type === 'LINEAR_SCALE') {
          return { question_id: q.id, value_number: v as number };
        }
        if (q.question_type === 'SINGLE_CHOICE') {
          return { question_id: q.id, value_text: v as string };
        }
        // OPEN_TEXT
        return { question_id: q.id, value_text: v as string };
      });

    const body: {
      respondent_email?: string;
      respondent_name?: string;
      answers: typeof payloadAnswers;
    } = { answers: payloadAnswers };

    if (survey.collect_email) {
      if (email.trim()) body.respondent_email = email.trim();
      if (name.trim()) body.respondent_name = name.trim();
    }

    setSubmitting(true);
    try {
      const res = await publicApi.post(`/public/surveys/${token}/responses`, body);
      setSuccessMessage(res.data?.message || 'Tu respuesta ha sido registrada. ¡Gracias!');
    } catch (err: unknown) {
      let detail = 'No se pudo enviar tu respuesta. Inténtalo de nuevo.';
      if (axios.isAxiosError(err)) {
        const d = err.response?.data?.detail;
        if (typeof d === 'string') detail = d;
      }
      setSubmitError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  // ── Shared brand header ──
  const BrandHeader = () => (
    <div className="flex items-center gap-3 mb-6">
      <div
        className="w-10 h-10 rounded-lg flex items-center justify-center font-extrabold text-white text-sm"
        style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
      >
        SH
      </div>
      <div>
        <h1 className="font-extrabold text-lg tracking-wide" style={{ color: 'var(--ink)' }}>
          Syner Hub
        </h1>
        <span
          className="font-mono text-[9px] uppercase tracking-widest"
          style={{ color: 'var(--muted-2)' }}
        >
          Transformación
        </span>
      </div>
    </div>
  );

  const PageShell: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div
      className="min-h-screen w-full flex justify-center px-4 py-10 font-sans"
      style={{ background: 'var(--bg)', color: 'var(--ink)' }}
    >
      <div className="w-full max-w-[640px]">{children}</div>
    </div>
  );

  // ── Loading ──
  if (loading) {
    return (
      <PageShell>
        <div className="flex flex-col items-center justify-center gap-4 py-24">
          <Loader2 size={36} className="animate-spin" style={{ color: 'var(--accent)' }} />
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            Cargando encuesta...
          </p>
        </div>
      </PageShell>
    );
  }

  // ── Error / unavailable ──
  if (loadError || !survey) {
    return (
      <PageShell>
        <BrandHeader />
        <div
          className="rounded-lg p-8 text-center"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <div className="flex justify-center mb-4">
            <AlertTriangle size={40} style={{ color: 'var(--neg, #ef4444)' }} />
          </div>
          <h2 className="font-bold text-lg mb-2" style={{ color: 'var(--ink)' }}>
            Encuesta no disponible
          </h2>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            {loadError || 'Esta encuesta no está disponible.'}
          </p>
        </div>
      </PageShell>
    );
  }

  // ── Success ──
  if (successMessage) {
    return (
      <PageShell>
        <BrandHeader />
        <div
          className="rounded-lg p-8 text-center"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <div className="flex justify-center mb-4">
            <CheckCircle size={48} style={{ color: 'var(--accent)' }} />
          </div>
          <h2 className="font-bold text-xl mb-2" style={{ color: 'var(--ink)' }}>
            ¡Gracias!
          </h2>
          <p className="text-sm" style={{ color: 'var(--muted)' }}>
            {successMessage}
          </p>
        </div>
      </PageShell>
    );
  }

  // ── Survey form ──
  const sortedSections = [...survey.sections].sort((a, b) => a.order - b.order);

  return (
    <PageShell>
      <BrandHeader />

      {/* Survey intro card */}
      <div
        className="rounded-lg p-6 mb-5"
        style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
      >
        <h2 className="font-extrabold text-2xl mb-2" style={{ color: 'var(--ink)' }}>
          {survey.title}
        </h2>
        {survey.description && (
          <p className="text-sm leading-relaxed mb-3" style={{ color: 'var(--muted)' }}>
            {survey.description}
          </p>
        )}
        <div
          className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full"
          style={{ background: 'var(--accent-tint, rgba(99,102,241,0.1))', color: 'var(--accent-strong)' }}
        >
          <Clock size={12} />
          <span>5–7 min{survey.is_anonymous ? ' · Anónima' : ''}</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Identity (when collecting email) */}
        {survey.collect_email && (
          <div
            ref={emailRef}
            className="rounded-lg p-6 space-y-4"
            style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
          >
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--muted)' }}>
                Correo electrónico <span style={{ color: 'var(--neg, #ef4444)' }}>*</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (emailInvalid) setEmailInvalid(false);
                }}
                placeholder="tucorreo@ejemplo.com"
                className="w-full p-2.5 rounded-lg text-sm outline-none transition-all"
                style={{
                  ...inputStyle,
                  borderColor: emailInvalid ? 'var(--neg, #ef4444)' : 'var(--border)',
                }}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1.5" style={{ color: 'var(--muted)' }}>
                Nombre (opcional)
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Tu nombre"
                className="w-full p-2.5 rounded-lg text-sm outline-none transition-all"
                style={inputStyle}
              />
            </div>
          </div>
        )}

        {/* Sections */}
        {sortedSections.map((section) => {
          const sortedQuestions = [...section.questions].sort((a, b) => a.order - b.order);
          return (
            <div
              key={section.id}
              className="rounded-lg p-6"
              style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
            >
              {section.title && (
                <h3 className="font-bold text-base mb-4" style={{ color: 'var(--ink)' }}>
                  {section.title}
                </h3>
              )}
              <div className="space-y-6">
                {sortedQuestions.map((q) => {
                  const invalid = invalidIds.has(q.id);
                  return (
                    <div
                      key={q.id}
                      ref={(el) => {
                        questionRefs.current[q.id] = el;
                      }}
                      className="rounded-lg"
                      style={
                        invalid
                          ? { boxShadow: '0 0 0 2px var(--neg, #ef4444)', padding: '0.75rem', margin: '-0.75rem' }
                          : undefined
                      }
                    >
                      <p className="text-sm font-semibold mb-3" style={{ color: 'var(--ink)' }}>
                        {q.text}
                        {q.is_required && <span style={{ color: 'var(--neg, #ef4444)' }}> *</span>}
                      </p>
                      {renderQuestion(q, answers[q.id], setAnswer, toggleMultiOption)}
                      {invalid && (
                        <p className="text-xs mt-2" style={{ color: 'var(--neg, #ef4444)' }}>
                          Esta pregunta es requerida.
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        {/* Submit error */}
        {submitError && (
          <div
            className="rounded-lg p-3.5 text-sm flex items-start gap-2"
            style={{
              background: 'var(--neg-tint, rgba(239,68,68,0.1))',
              border: '1px solid var(--neg, #ef4444)',
              color: 'var(--neg, #ef4444)',
            }}
          >
            <AlertTriangle size={16} className="flex-shrink-0 mt-0.5" />
            <span>{submitError}</span>
          </div>
        )}

        {/* Submit button */}
        <button
          type="submit"
          disabled={submitting}
          className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-semibold text-white transition-all disabled:opacity-50 disabled:pointer-events-none"
          style={{ background: 'var(--accent)' }}
        >
          {submitting ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Enviando...</span>
            </>
          ) : (
            <span>Enviar respuestas</span>
          )}
        </button>

        <p className="text-center text-[11px]" style={{ color: 'var(--muted-2)' }}>
          Powered by Syner Hub
        </p>
      </form>
    </PageShell>
  );
};

// ── Question renderer ──
function renderQuestion(
  q: SurveyQuestion,
  value: AnswerValue,
  setAnswer: (qid: number, value: AnswerValue) => void,
  toggleMultiOption: (qid: number, option: string) => void,
): React.ReactNode {
  switch (q.question_type) {
    case 'SINGLE_CHOICE':
      return (
        <div className="space-y-2">
          {(q.options || []).map((opt) => {
            const selected = value === opt;
            return (
              <label
                key={opt}
                className="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all"
                style={{
                  background: selected ? 'var(--accent-tint, rgba(99,102,241,0.1))' : 'var(--surface-2)',
                  border: `1px solid ${selected ? 'var(--accent)' : 'var(--border)'}`,
                }}
              >
                <input
                  type="radio"
                  name={`q-${q.id}`}
                  checked={selected}
                  onChange={() => setAnswer(q.id, opt)}
                  className="accent-[var(--accent)]"
                />
                <span className="text-sm" style={{ color: 'var(--ink)' }}>
                  {opt}
                </span>
              </label>
            );
          })}
        </div>
      );

    case 'MULTI_CHOICE': {
      const arr = Array.isArray(value) ? value : [];
      return (
        <div className="space-y-2">
          {(q.options || []).map((opt) => {
            const checked = arr.includes(opt);
            return (
              <label
                key={opt}
                className="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all"
                style={{
                  background: checked ? 'var(--accent-tint, rgba(99,102,241,0.1))' : 'var(--surface-2)',
                  border: `1px solid ${checked ? 'var(--accent)' : 'var(--border)'}`,
                }}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleMultiOption(q.id, opt)}
                  className="accent-[var(--accent)]"
                />
                <span className="text-sm" style={{ color: 'var(--ink)' }}>
                  {opt}
                </span>
              </label>
            );
          })}
        </div>
      );
    }

    case 'LINEAR_SCALE': {
      const min = q.scale_min ?? 1;
      const max = q.scale_max ?? 5;
      const range: number[] = [];
      for (let i = min; i <= max; i++) range.push(i);
      return (
        <div>
          <div className="flex items-stretch gap-2">
            {range.map((n) => {
              const selected = value === n;
              return (
                <button
                  key={n}
                  type="button"
                  onClick={() => setAnswer(q.id, n)}
                  className="flex-1 min-w-0 py-2.5 rounded-lg text-sm font-semibold transition-all"
                  style={{
                    background: selected ? 'var(--accent)' : 'var(--surface-2)',
                    border: `1px solid ${selected ? 'var(--accent)' : 'var(--border)'}`,
                    color: selected ? '#fff' : 'var(--ink)',
                  }}
                >
                  {n}
                </button>
              );
            })}
          </div>
          {(q.scale_min_label || q.scale_max_label) && (
            <div className="flex justify-between mt-2 text-[11px]" style={{ color: 'var(--muted)' }}>
              <span>{q.scale_min_label || ''}</span>
              <span>{q.scale_max_label || ''}</span>
            </div>
          )}
        </div>
      );
    }

    case 'OPEN_TEXT':
      return (
        <textarea
          value={typeof value === 'string' ? value : ''}
          onChange={(e) => setAnswer(q.id, e.target.value)}
          rows={4}
          placeholder="Escribe tu respuesta..."
          className="w-full p-2.5 rounded-lg text-sm resize-none outline-none transition-all"
          style={inputStyle}
        />
      );

    default:
      return null;
  }
}

export default PublicSurveyView;
