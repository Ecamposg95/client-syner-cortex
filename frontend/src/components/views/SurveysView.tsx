import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardList, FileText, Layers, Loader2, Plus, X,
  Copy, Check, Play, Square, BarChart3, Sparkles,
} from 'lucide-react';
import apiClient from '../../api/client';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

// ── API shapes ──────────────────────────────────────────────────────────
interface SurveySummary {
  id: number;
  title: string;
  description: string | null;
  is_template: boolean;
  organization_id: number | null;
  created_at: string;
  question_count: number;
  campaign_count: number;
}

type CampaignStatus = 'DRAFT' | 'OPEN' | 'CLOSED';

interface CampaignResponse {
  id: number;
  survey_id: number;
  name: string;
  public_token: string;
  status: CampaignStatus;
  is_anonymous: boolean;
  collect_email: boolean;
  opens_at: string | null;
  closes_at: string | null;
  max_responses: number | null;
  created_at: string;
  response_count: number;
  public_path: string;
}

// ── Status badge helper (maps to existing Badge variants) ───────────────
const STATUS_META: Record<CampaignStatus, { variant: 'active' | 'completed' | 'pending' | 'risk'; label: string }> = {
  DRAFT:  { variant: 'pending',   label: 'Borrador' },
  OPEN:   { variant: 'active',    label: 'Abierta' },
  CLOSED: { variant: 'risk',      label: 'Cerrada' },
};

const inputStyle: React.CSSProperties = {
  background: 'var(--surface-2)',
  border: '1px solid var(--border)',
  color: 'var(--ink)',
};

export const SurveysView: React.FC = () => {
  const navigate = useNavigate();

  const [surveys, setSurveys] = useState<SurveySummary[]>([]);
  const [campaigns, setCampaigns] = useState<CampaignResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingTemplateId, setUsingTemplateId] = useState<number | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  // Campaign creation modal state
  const [modalSurvey, setModalSurvey] = useState<SurveySummary | null>(null);
  const [campaignName, setCampaignName] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(true);
  const [collectEmail, setCollectEmail] = useState(false);
  const [maxResponses, setMaxResponses] = useState('');
  const [closesAt, setClosesAt] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadSurveys = () =>
    apiClient.get<SurveySummary[]>('/surveys').then((res) => setSurveys(res.data));
  const loadCampaigns = () =>
    apiClient.get<CampaignResponse[]>('/campaigns').then((res) => setCampaigns(res.data));

  const refreshAll = () => Promise.all([loadSurveys(), loadCampaigns()]);

  useEffect(() => {
    refreshAll()
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const templateCount = useMemo(() => surveys.filter((s) => s.is_template).length, [surveys]);

  // ── Actions ────────────────────────────────────────────────────────────
  const handleUseTemplate = async (templateId: number) => {
    setUsingTemplateId(templateId);
    try {
      await apiClient.post(`/surveys/from-template/${templateId}`);
      await loadSurveys();
    } catch (e) {
      console.error(e);
    } finally {
      setUsingTemplateId(null);
    }
  };

  const openModal = (survey: SurveySummary) => {
    setModalSurvey(survey);
    setCampaignName('');
    setIsAnonymous(true);
    setCollectEmail(false);
    setMaxResponses('');
    setClosesAt('');
  };

  const closeModal = () => {
    if (submitting) return;
    setModalSurvey(null);
  };

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modalSurvey || !campaignName.trim()) return;
    setSubmitting(true);
    try {
      const body: Record<string, unknown> = {
        name: campaignName.trim(),
        is_anonymous: isAnonymous,
        collect_email: collectEmail,
      };
      if (maxResponses.trim()) body.max_responses = Number(maxResponses);
      if (closesAt) body.closes_at = new Date(closesAt).toISOString();

      await apiClient.post(`/surveys/${modalSurvey.id}/campaigns`, body);
      setModalSurvey(null);
      await loadCampaigns();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleStatus = async (campaign: CampaignResponse) => {
    const next: CampaignStatus = campaign.status === 'OPEN' ? 'CLOSED' : 'OPEN';
    setTogglingId(campaign.id);
    try {
      await apiClient.patch(`/campaigns/${campaign.id}/status`, { status: next });
      await loadCampaigns();
    } catch (e) {
      console.error(e);
    } finally {
      setTogglingId(null);
    }
  };

  const handleCopy = async (campaign: CampaignResponse) => {
    const url = `${window.location.origin}${campaign.public_path}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopiedId(campaign.id);
      window.setTimeout(() => setCopiedId((cur) => (cur === campaign.id ? null : cur)), 1800);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-4">
        <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
        <p className="text-sm text-[var(--muted)]">Cargando encuestas diagnósticas...</p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div
          className="p-2.5 rounded-xl text-white"
          style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
        >
          <ClipboardList size={24} />
        </div>
        <div>
          <h2 className="font-extrabold text-2xl">Encuestas Diagnósticas</h2>
          <p className="text-sm text-[var(--muted)]">
            {surveys.length} encuestas · {templateCount} plantillas · {campaigns.length} campañas
          </p>
        </div>
      </div>

      {/* ── Section A: Plantillas y encuestas ── */}
      <section className="space-y-4">
        <h3 className="font-bold text-lg text-[var(--ink)]">Plantillas y encuestas</h3>

        {surveys.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-[var(--muted)]">No hay encuestas ni plantillas disponibles.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {surveys.map((survey) => (
              <Card key={survey.id} className="p-0 overflow-hidden flex flex-col">
                <div
                  className="h-1.5 w-full"
                  style={{
                    background: survey.is_template
                      ? 'linear-gradient(135deg, #8b5cf6, #6366f1)'
                      : 'linear-gradient(135deg, #0ea5e9, #06b6d4)',
                  }}
                />
                <div className="p-5 flex flex-col flex-1">
                  <div className="flex items-start justify-between mb-3">
                    <div
                      className="p-2.5 rounded-xl text-white"
                      style={{
                        background: survey.is_template
                          ? 'linear-gradient(135deg, #8b5cf6, #6366f1)'
                          : 'linear-gradient(135deg, #0ea5e9, #06b6d4)',
                      }}
                    >
                      {survey.is_template ? <Layers size={22} /> : <FileText size={22} />}
                    </div>
                    <div className="flex flex-wrap gap-1.5 justify-end">
                      <span className="status-badge status-badge--pending">
                        {survey.question_count} preguntas
                      </span>
                    </div>
                  </div>

                  <h4 className="font-bold text-base text-[var(--ink)] leading-tight mb-1">
                    {survey.title}
                  </h4>
                  <p className="text-xs text-[var(--muted)] leading-relaxed flex-1">
                    {survey.description || 'Sin descripción.'}
                  </p>

                  <div className="flex items-center gap-2 mt-2 mb-4">
                    {survey.is_template ? (
                      <Badge variant="completed" label="Plantilla" />
                    ) : (
                      <Badge variant="active" label="Org" />
                    )}
                    {!survey.is_template && (
                      <span className="text-xs text-[var(--muted-2)]">
                        {survey.campaign_count} campañas
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2 mt-auto">
                    {survey.is_template && (
                      <button
                        type="button"
                        onClick={() => handleUseTemplate(survey.id)}
                        disabled={usingTemplateId === survey.id}
                        className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg transition-colors disabled:opacity-50"
                        style={{ background: 'var(--accent-tint)', color: 'var(--accent-strong)' }}
                      >
                        {usingTemplateId === survey.id ? (
                          <Loader2 size={14} className="animate-spin" />
                        ) : (
                          <Sparkles size={14} />
                        )}
                        Usar plantilla
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => openModal(survey)}
                      className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-white rounded-lg transition-colors"
                      style={{ background: 'var(--accent)' }}
                    >
                      <Plus size={14} />
                      Generar campaña
                    </button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* ── Section B: Campañas ── */}
      <section className="space-y-4">
        <h3 className="font-bold text-lg text-[var(--ink)]">Campañas</h3>

        {campaigns.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-[var(--muted)]">
              Aún no hay campañas. Genera una desde cualquier encuesta.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {campaigns.map((campaign) => {
              const meta = STATUS_META[campaign.status];
              const url = `${window.location.origin}${campaign.public_path}`;
              return (
                <Card key={campaign.id} className="p-5">
                  <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                    {/* Left: name + meta */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2.5 flex-wrap mb-1.5">
                        <h4 className="font-bold text-base text-[var(--ink)] truncate">
                          {campaign.name}
                        </h4>
                        <Badge variant={meta.variant} label={meta.label} />
                      </div>
                      <p className="text-xs text-[var(--muted)]">
                        {campaign.response_count} respuestas
                        {campaign.is_anonymous ? ' · anónima' : ''}
                        {campaign.max_responses ? ` · máx. ${campaign.max_responses}` : ''}
                      </p>

                      {/* Public link */}
                      <div className="flex items-center gap-2 mt-2 max-w-xl">
                        <input
                          readOnly
                          value={url}
                          className="flex-1 px-2.5 py-1.5 rounded-lg text-xs outline-none font-mono"
                          style={inputStyle}
                          onFocus={(e) => e.currentTarget.select()}
                        />
                        <button
                          type="button"
                          onClick={() => handleCopy(campaign)}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-colors shrink-0"
                          style={{ background: 'var(--surface-2)', color: 'var(--muted)' }}
                        >
                          {copiedId === campaign.id ? (
                            <>
                              <Check size={13} className="text-[var(--accent)]" />
                              ¡Copiado!
                            </>
                          ) : (
                            <>
                              <Copy size={13} />
                              Copiar
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Right: actions */}
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => handleToggleStatus(campaign)}
                        disabled={togglingId === campaign.id}
                        className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg transition-colors disabled:opacity-50"
                        style={
                          campaign.status === 'OPEN'
                            ? { background: 'var(--surface-2)', color: 'var(--muted)' }
                            : { background: 'var(--accent-tint)', color: 'var(--accent-strong)' }
                        }
                      >
                        {togglingId === campaign.id ? (
                          <Loader2 size={14} className="animate-spin" />
                        ) : campaign.status === 'OPEN' ? (
                          <Square size={14} />
                        ) : (
                          <Play size={14} />
                        )}
                        {campaign.status === 'OPEN' ? 'Cerrar' : 'Abrir'}
                      </button>
                      <button
                        type="button"
                        onClick={() => navigate(`/surveys/campaigns/${campaign.id}/results`)}
                        className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-white rounded-lg transition-colors"
                        style={{ background: 'var(--accent)' }}
                      >
                        <BarChart3 size={14} />
                        Ver resultados
                      </button>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      {/* ── Generar campaña MODAL ── */}
      {modalSurvey && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.4)' }}
          onClick={closeModal}
        >
          <div
            className="w-full max-w-md rounded-xl p-6 shadow-float relative"
            style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={closeModal}
              className="absolute top-4 right-4 transition-colors"
              style={{ color: 'var(--muted)' }}
            >
              <X size={20} />
            </button>
            <h3 className="font-bold text-lg mb-1" style={{ color: 'var(--ink)' }}>
              Generar campaña
            </h3>
            <p className="text-xs text-[var(--muted)] mb-4">{modalSurvey.title}</p>

            <form onSubmit={handleCreateCampaign} className="space-y-4">
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                  Nombre de la campaña
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ej. Diagnóstico Q3 2026"
                  value={campaignName}
                  onChange={(e) => setCampaignName(e.target.value)}
                  className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                  style={inputStyle}
                />
              </div>

              <div className="flex flex-col gap-2.5">
                <label className="flex items-center gap-2.5 text-sm cursor-pointer" style={{ color: 'var(--ink)' }}>
                  <input
                    type="checkbox"
                    checked={isAnonymous}
                    onChange={(e) => setIsAnonymous(e.target.checked)}
                    className="accent-[var(--accent)] w-4 h-4"
                  />
                  Respuestas anónimas
                </label>
                <label className="flex items-center gap-2.5 text-sm cursor-pointer" style={{ color: 'var(--ink)' }}>
                  <input
                    type="checkbox"
                    checked={collectEmail}
                    onChange={(e) => setCollectEmail(e.target.checked)}
                    className="accent-[var(--accent)] w-4 h-4"
                  />
                  Solicitar email
                </label>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                    Máx. respuestas
                  </label>
                  <input
                    type="number"
                    min={1}
                    placeholder="Sin límite"
                    value={maxResponses}
                    onChange={(e) => setMaxResponses(e.target.value)}
                    className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                    Cierre (opcional)
                  </label>
                  <input
                    type="datetime-local"
                    value={closesAt}
                    onChange={(e) => setClosesAt(e.target.value)}
                    className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                    style={inputStyle}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-xs font-medium rounded-lg transition-colors"
                  style={{ color: 'var(--muted)', background: 'var(--surface-2)' }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={submitting || !campaignName.trim()}
                  className="px-4 py-2 text-xs font-semibold text-white rounded-lg flex items-center gap-1 disabled:opacity-50"
                  style={{ background: 'var(--accent)' }}
                >
                  {submitting ? (
                    <>
                      <Loader2 size={12} className="animate-spin" />
                      <span>Creando...</span>
                    </>
                  ) : (
                    <span>Crear campaña</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SurveysView;
