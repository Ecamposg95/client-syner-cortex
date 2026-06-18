import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card } from '../../ui/Card';
import {
  Bot, Save, Play, CheckCircle, Loader2, ArrowLeft, PenTool,
  Download, AlertCircle, Plus
} from 'lucide-react';
import apiClient from '../../../api/client';
import { useAuthStore } from '../../../store/authStore';
import { useWorkspaceStore } from '../../../store/workspaceStore';

interface ToolDetail {
  id: number;
  name: string;
  description: string;
  toolkit_name: string;
  has_template: boolean;
  template: {
    id: number;
    system_prompt: string;
    user_prompt_template: string;
    json_schema_output: any;
  } | null;
}

export const ToolRunPage: React.FC = () => {
  const { toolId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { activeWorkspace } = useWorkspaceStore();

  const [tool, setTool] = useState<ToolDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [status, setStatus] = useState('DRAFT');
  const [inputFields, setInputFields] = useState<Record<string, string>>({});
  const [outputData, setOutputData] = useState<any>(null);
  const [currentRunId, setCurrentRunId] = useState<number | null>(null);

  // Parse input field names from the user_prompt_template
  const parseInputFields = (template: string): string[] => {
    const matches = template.match(/\{(\w+)\}/g);
    if (!matches) return [];
    return [...new Set(matches.map(m => m.replace(/[{}]/g, '')))];
  };

  useEffect(() => {
    const fetchTool = async () => {
      try {
        const res = await apiClient.get(`/tools/${toolId}`);
        setTool(res.data);
        if (res.data.template) {
          const fields = parseInputFields(res.data.template.user_prompt_template);
          const initial: Record<string, string> = {};
          fields.forEach(f => { initial[f] = ''; });
          setInputFields(initial);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchTool();
  }, [toolId]);

  const handleGenerate = async () => {
    if (!toolId) return;
    setGenerating(true);

    try {
      // 1. Create the ToolRun
      const runRes = await apiClient.post('/tool-runs', {
        tool_id: parseInt(toolId),
        workspace_id: activeWorkspace?.id || null,
      });
      const runId = runRes.data.id;
      setCurrentRunId(runId);

      // 2. Submit all inputs
      const fieldNames = Object.keys(inputFields);
      for (const key of fieldNames) {
        await apiClient.post(`/tool-runs/${runId}/inputs`, {
          key,
          value: inputFields[key]
        });
      }

      // 3. Execute Tool (this calls the backend LLM logic)
      const execRes = await apiClient.post(`/tool-runs/${runId}/execute`);
      setStatus('AI_GENERATED');

      // 4. Fetch the full run details to get the output
      const detailRes = await apiClient.get(`/tool-runs/${runId}`);
      if (detailRes.data.outputs && detailRes.data.outputs.length > 0) {
        setOutputData(detailRes.data.outputs[0].content_json);
      }
    } catch (e) {
      console.error(e);
      alert('Error al generar el entregable.');
    } finally {
      setGenerating(false);
    }
  };

  const handleReview = () => {
    if (currentRunId) {
      navigate(`/runs/${currentRunId}/review`);
    }
  };

  const handleExportMarkdown = () => {
    if (!outputData || !tool) return;
    const md = jsonToMarkdown(tool.name, outputData);
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${tool.name.replace(/\s+/g, '_')}.md`;
    a.click();
  };

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-4">
        <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  if (!tool) {
    return <div className="p-8 text-[var(--muted)]">Herramienta no encontrada.</div>;
  }

  const fieldNames = Object.keys(inputFields);

  return (
    <div className="space-y-6">
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-[var(--muted)] hover:text-[var(--ink)] transition-colors">
        <ArrowLeft size={16} /> Volver
      </button>

      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="font-extrabold text-2xl flex items-center gap-2">
              <PenTool className="text-[var(--accent)]" /> {tool.name}
            </h2>
            <span className={`px-2.5 py-1 text-[10px] uppercase font-bold rounded-md ${
              status === 'DRAFT' ? 'bg-[var(--surface-2)] text-[var(--muted)]' :
              status === 'AI_GENERATED' ? 'bg-yellow-500/10 text-yellow-500' :
              'bg-green-500/10 text-green-500'
            }`}>
              {status}
            </span>
          </div>
          <p className="text-sm text-[var(--muted)] mt-1">{tool.toolkit_name}</p>
        </div>

        <div className="flex gap-3">
          {outputData && (
            <button onClick={handleExportMarkdown} className="px-4 py-2 text-sm font-semibold border border-[var(--border)] rounded-lg hover:bg-[var(--surface-2)] flex items-center gap-2">
              <Download size={16} /> Exportar MD
            </button>
          )}
          {status === 'AI_GENERATED' && user?.user_type === 'SYNER_CREW' && (
            <button onClick={handleReview} className="px-4 py-2 text-sm font-semibold bg-blue-500 text-white rounded-lg hover:opacity-90 flex items-center gap-2">
              <CheckCircle size={16} /> Revisar Output
            </button>
          )}
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* LEFT: Inputs */}
        <div className="space-y-4">
          <h3 className="font-bold text-lg text-[var(--ink-2)]">Inputs del Consultor / Cliente</h3>
          <Card className="p-5 space-y-4">
            {fieldNames.map((field) => (
              <div key={field}>
                <label className="block text-sm font-semibold mb-2 text-[var(--ink)] capitalize">
                  {field.replace(/_/g, ' ')}
                </label>
                <textarea
                  rows={3}
                  className="w-full p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-lg text-sm outline-none focus:border-[var(--accent)] transition-colors resize-none"
                  placeholder={`Ingresa ${field.replace(/_/g, ' ')}...`}
                  value={inputFields[field]}
                  onChange={e => setInputFields({ ...inputFields, [field]: e.target.value })}
                  disabled={status === 'APPROVED'}
                />
              </div>
            ))}

            {status !== 'APPROVED' && (
              <button
                onClick={handleGenerate}
                disabled={generating || fieldNames.some(f => !inputFields[f].trim())}
                className="w-full py-3 bg-[var(--accent)] text-white rounded-lg font-bold flex items-center justify-center gap-2 disabled:opacity-50 hover:opacity-90 transition-opacity"
              >
                {generating ? <Loader2 className="animate-spin" size={18} /> : <Bot size={18} />}
                {generating ? 'Procesando con Cortex AI...' : 'Generar con IA'}
              </button>
            )}
          </Card>
        </div>

        {/* RIGHT: Output */}
        <div className="space-y-4">
          <h3 className="font-bold text-lg text-[var(--ink-2)]">Cortex AI Output</h3>
          <Card className="p-5 min-h-[400px] flex flex-col relative overflow-hidden">
            {!outputData && !generating && (
              <div className="flex-1 flex flex-col items-center justify-center text-[var(--muted)] opacity-40">
                <Bot size={56} className="mb-4" />
                <p className="text-sm">El resultado aparecerá aquí</p>
                <p className="text-xs mt-1">Completa los inputs y presiona "Generar con IA"</p>
              </div>
            )}

            {generating && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-[var(--surface)] z-10">
                <Loader2 size={48} className="animate-spin text-[var(--accent)] mb-4" />
                <p className="text-sm text-[var(--muted)] animate-pulse">Analizando datos y generando entregable...</p>
              </div>
            )}

            {outputData && <DynamicOutputRenderer toolName={tool.name} data={outputData} />}
          </Card>
        </div>
      </div>
    </div>
  );
};

// ─── Dynamic Output Renderer ──────────────────────────────────────

const DynamicOutputRenderer: React.FC<{ toolName: string; data: any }> = ({ toolName, data }) => {
  const name = toolName.toLowerCase();

  if (name.includes('foda')) return <FODARenderer data={data} />;
  if (name.includes('hallazgos')) return <HallazgosRenderer data={data} />;
  if (name.includes('raci')) return <RACIRenderer data={data} />;
  if (name.includes('macroflujo')) return <MacroflujoRenderer data={data} />;
  if (name.includes('kpi')) return <KPIBookRenderer data={data} />;
  if (name.includes('roadmap')) return <RoadmapRenderer data={data} />;
  if (name.includes('journey')) return <CoreJourneyRenderer data={data} />;
  if (name.includes('sop')) return <SOPCardRenderer data={data} />;
  if (name.includes('academia')) return <AcademiaRenderer data={data} />;
  if (name.includes('gobernanza') || name.includes('organigrama')) return <GobernanzaRenderer data={data} />;
  if (name.includes('quick')) return <QuickWinsRenderer data={data} />;
  if (name.includes('ehs')) return <EHSRenderer data={data} />;
  if (name.includes('costos') || name.includes('costo')) return <CostosRenderer data={data} />;
  if (name.includes('visual')) return <VisualMgmtRenderer data={data} />;
  if (name.includes('manual')) return <ManualMaestroRenderer data={data} />;

  // Fallback: render JSON
  return <pre className="text-xs overflow-auto whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre>;
};

// ─── FODA ─────────────────────────────────────────────────────────

const FODARenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="grid grid-cols-2 gap-3 h-full">
    {[
      { key: 'fortalezas', label: 'Fortalezas', color: '#22c55e' },
      { key: 'oportunidades', label: 'Oportunidades', color: '#3b82f6' },
      { key: 'debilidades', label: 'Debilidades', color: '#ef4444' },
      { key: 'amenazas', label: 'Amenazas', color: '#f97316' },
    ].map(q => (
      <div key={q.key} className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface-2)]">
        <h4 className="font-bold text-sm mb-2 pb-2 border-b border-[var(--border)]" style={{ color: q.color }}>
          {q.label}
        </h4>
        <ul className="list-disc pl-4 text-xs text-[var(--ink)] space-y-1">
          {(data[q.key] || []).map((item: string, i: number) => <li key={i}>{item}</li>)}
        </ul>
      </div>
    ))}
  </div>
);

// ─── Hallazgos y Oportunidades ────────────────────────────────────

const HallazgosRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4 overflow-y-auto max-h-[500px]">
    <h4 className="font-bold text-sm text-red-500">Hallazgos</h4>
    {(data.hallazgos || []).map((h: any, i: number) => (
      <div key={i} className="p-3 bg-[var(--surface-2)] rounded-lg border-l-4 border-red-500 text-xs space-y-1">
        <div className="flex justify-between"><strong>{h.titulo}</strong><span className="px-1.5 py-0.5 bg-red-500/10 text-red-500 rounded text-[10px] font-bold">{h.impacto}</span></div>
        <p className="text-[var(--muted)]">{h.descripcion}</p>
        <p className="text-[var(--accent)]"><AlertCircle size={12} className="inline mr-1" />{h.recomendacion}</p>
      </div>
    ))}
    <h4 className="font-bold text-sm text-blue-500 pt-2">Oportunidades</h4>
    {(data.oportunidades || []).map((o: any, i: number) => (
      <div key={i} className="p-3 bg-[var(--surface-2)] rounded-lg border-l-4 border-blue-500 text-xs space-y-1">
        <strong>{o.titulo}</strong> <span className="text-[var(--muted)]">({o.area})</span>
        <p>{o.accion_sugerida}</p>
      </div>
    ))}
  </div>
);

// ─── RACI ─────────────────────────────────────────────────────────

const RACIRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="overflow-x-auto">
    <table className="w-full text-xs border-collapse">
      <thead>
        <tr className="bg-[var(--surface-2)]">
          <th className="p-2 text-left border border-[var(--border)] font-bold text-[var(--ink)]">Proceso</th>
          {(data.roles || []).map((r: string, i: number) => (
            <th key={i} className="p-2 text-center border border-[var(--border)] font-bold text-[var(--ink)]">{r}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {(data.procesos || []).map((p: any, i: number) => (
          <tr key={i}>
            <td className="p-2 border border-[var(--border)] font-medium">{p.proceso}</td>
            {(data.roles || []).map((r: string, j: number) => {
              const val = p.asignaciones?.[r] || '';
              const colors: Record<string, string> = { R: '#3b82f6', A: '#ef4444', C: '#f59e0b', I: '#6b7280' };
              return (
                <td key={j} className="p-2 border border-[var(--border)] text-center font-bold" style={{ color: colors[val] || 'inherit' }}>
                  {val}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// ─── Macroflujo ───────────────────────────────────────────────────

const MacroflujoRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-3 overflow-y-auto max-h-[500px]">
    <h4 className="font-bold text-sm text-[var(--ink)]">{data.proceso_nombre}</h4>
    {(data.fases || []).map((f: any, i: number) => (
      <div key={i} className="p-3 bg-[var(--surface-2)] rounded-lg border border-[var(--border)] text-xs relative">
        <div className="absolute -left-3 top-3 w-6 h-6 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-[10px] font-bold">
          {f.orden}
        </div>
        <div className="ml-4">
          <strong className="text-[var(--ink)]">{f.nombre}</strong>
          <span className="text-[var(--muted)] ml-2">· {f.actor_responsable}</span>
          <p className="text-[var(--muted)] mt-1">{f.descripcion}</p>
        </div>
      </div>
    ))}
  </div>
);

// ─── KPI Book ─────────────────────────────────────────────────────

const KPIBookRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="overflow-x-auto">
    <table className="w-full text-xs border-collapse">
      <thead>
        <tr className="bg-[var(--surface-2)]">
          {['KPI', 'Área', 'Fórmula', 'Frecuencia', 'Meta'].map(h => (
            <th key={h} className="p-2 text-left border border-[var(--border)] font-bold">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {(data.kpis || []).map((k: any, i: number) => (
          <tr key={i}>
            <td className="p-2 border border-[var(--border)] font-semibold text-[var(--accent)]">{k.nombre}</td>
            <td className="p-2 border border-[var(--border)]">{k.area}</td>
            <td className="p-2 border border-[var(--border)] font-mono text-[10px]">{k.formula}</td>
            <td className="p-2 border border-[var(--border)]">{k.frecuencia}</td>
            <td className="p-2 border border-[var(--border)] font-bold">{k.meta}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// ─── Roadmap 30/60/90 ─────────────────────────────────────────────

const RoadmapRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4 overflow-y-auto max-h-[500px]">
    {[
      { key: 'horizonte_30', label: '30 Días', color: '#22c55e' },
      { key: 'horizonte_60', label: '60 Días', color: '#f59e0b' },
      { key: 'horizonte_90', label: '90 Días', color: '#6366f1' },
    ].map(h => (
      <div key={h.key}>
        <h4 className="font-bold text-sm mb-2 flex items-center gap-2">
          <span className="w-3 h-3 rounded-full" style={{ background: h.color }} />
          {h.label}
        </h4>
        <div className="space-y-2">
          {(data[h.key] || []).map((item: any, i: number) => (
            <div key={i} className="p-3 bg-[var(--surface-2)] rounded-lg text-xs border-l-4" style={{ borderLeftColor: h.color }}>
              <strong>{item.accion}</strong>
              <div className="flex gap-4 mt-1 text-[var(--muted)]">
                <span>👤 {item.responsable}</span>
                <span>📦 {item.entregable}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
);

// ─── Core Journey ─────────────────────────────────────────────────

const JOURNEY_COLORS = ['#6366f1', '#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#a855f7'];

const CoreJourneyRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4 overflow-y-auto max-h-[520px]">
    <h4 className="font-bold text-sm text-[var(--ink)]">{data.journey_nombre}</h4>
    <div className="space-y-3">
      {(data.fases || []).map((fase: any, fi: number) => {
        const color = JOURNEY_COLORS[fi % JOURNEY_COLORS.length];
        return (
          <div key={fi} className="rounded-lg border border-[var(--border)] overflow-hidden">
            <div className="px-3 py-1.5 text-[11px] font-bold uppercase tracking-wide text-white" style={{ background: color }}>
              {fase.fase}
            </div>
            <div className="p-3 flex flex-wrap gap-2 bg-[var(--surface-2)]">
              {(fase.etapas || []).map((e: any, ei: number) => (
                <div key={ei} className="flex-1 min-w-[140px] p-2.5 rounded-lg bg-[var(--surface)] border border-[var(--border)]">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold text-white" style={{ background: color }}>{e.codigo}</span>
                    <strong className="text-xs text-[var(--ink)]">{e.nombre}</strong>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-snug">{e.descripcion}</p>
                  <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-[var(--muted-2)]">
                    {e.responsable && <span>👤 {e.responsable}</span>}
                    {e.kpi && <span>📊 {e.kpi}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  </div>
);

// ─── SOP Card ─────────────────────────────────────────────────────

const SOPChips: React.FC<{ label: string; items: string[]; color: string }> = ({ label, items, color }) => (
  <div>
    <p className="text-[10px] uppercase font-bold tracking-wide mb-1" style={{ color }}>{label}</p>
    <div className="flex flex-wrap gap-1">
      {(items || []).map((it, i) => (
        <span key={i} className="px-2 py-0.5 rounded text-[10px] bg-[var(--surface-2)] text-[var(--ink-2)] border border-[var(--border)]">{it}</span>
      ))}
    </div>
  </div>
);

const SOPCardRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4 overflow-y-auto max-h-[520px]">
    <div className="rounded-lg border border-[var(--border)] p-4 bg-[var(--surface-2)]">
      <div className="flex items-center gap-2 mb-1">
        <span className="px-2 py-0.5 rounded text-[10px] font-bold text-white bg-[var(--accent)]">{data.codigo}</span>
        <h4 className="font-bold text-[var(--ink)]">{data.titulo}</h4>
      </div>
      <p className="text-xs text-[var(--muted)]">{data.objetivo}</p>
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[11px] text-[var(--muted-2)]">
        {data.alcance && <span><strong>Alcance:</strong> {data.alcance}</span>}
        {data.responsable && <span><strong>Responsable:</strong> {data.responsable}</span>}
      </div>
    </div>
    <div className="space-y-2">
      {(data.pasos || []).map((p: any, i: number) => (
        <div key={i} className="flex gap-3 items-start">
          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-[11px] font-bold">{p.n ?? i + 1}</span>
          <div className="text-xs">
            <strong className="text-[var(--ink)]">{p.accion}</strong>
            {p.detalle && <p className="text-[var(--muted)] mt-0.5">{p.detalle}</p>}
          </div>
        </div>
      ))}
    </div>
    <div className="grid grid-cols-2 gap-3 pt-2 border-t border-[var(--border)]">
      <SOPChips label="Entradas" items={data.entradas} color="#3b82f6" />
      <SOPChips label="Salidas" items={data.salidas} color="#22c55e" />
      <SOPChips label="KPIs" items={data.kpis} color="#a855f7" />
      <SOPChips label="Riesgos" items={data.riesgos} color="#ef4444" />
    </div>
  </div>
);

// ─── Academia (Course Module) ─────────────────────────────────────

const AcademiaRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4 overflow-y-auto max-h-[520px]">
    <div>
      <p className="text-[11px] uppercase font-bold tracking-wide text-[var(--accent)]">{data.curso}</p>
      <h4 className="font-bold text-[var(--ink)]">{data.modulo}</h4>
      <div className="flex flex-wrap gap-2 mt-1.5">
        {data.duracion && <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[var(--surface-2)] text-[var(--ink-2)]">⏱ {data.duracion}</span>}
        {data.publico && <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[var(--surface-2)] text-[var(--ink-2)]">👥 {data.publico}</span>}
      </div>
    </div>
    {data.objetivo_aprendizaje && (
      <div className="p-3 rounded-lg bg-[var(--accent-tint,rgba(99,102,241,0.08))] border-l-4 border-[var(--accent)] text-xs">
        <strong className="text-[var(--accent-strong)]">Objetivo de aprendizaje</strong>
        <p className="text-[var(--ink)] mt-0.5">{data.objetivo_aprendizaje}</p>
      </div>
    )}
    <div className="space-y-2">
      {(data.lecciones || []).map((l: any, i: number) => (
        <div key={i} className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-xs">
          <div className="flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-[10px] font-bold">{i + 1}</span>
            <strong className="text-[var(--ink)]">{l.titulo}</strong>
          </div>
          {l.contenido && <p className="text-[var(--muted)] mt-1">{l.contenido}</p>}
          {l.actividad && <p className="text-[var(--accent)] mt-1">🎯 {l.actividad}</p>}
        </div>
      ))}
    </div>
    <div className="grid grid-cols-2 gap-3 pt-2 border-t border-[var(--border)]">
      <SOPChips label="Evaluación" items={data.evaluacion} color="#f59e0b" />
      <SOPChips label="Recursos" items={data.recursos} color="#0ea5e9" />
    </div>
  </div>
);

// ─── Gobernanza ───────────────────────────────────────────────────

const GobernanzaRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4 overflow-y-auto max-h-[520px]">
    <div className="text-center p-3 rounded-lg text-white font-bold text-sm" style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}>
      {data.organo_maximo}
    </div>
    <div>
      <p className="text-[11px] uppercase font-bold tracking-wide text-[var(--muted-2)] mb-2">Comités</p>
      <div className="grid grid-cols-1 gap-2">
        {(data.comites || []).map((c: any, i: number) => (
          <div key={i} className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-xs">
            <div className="flex items-center justify-between">
              <strong className="text-[var(--ink)]">{c.nombre}</strong>
              {c.frecuencia && <span className="px-1.5 py-0.5 rounded text-[10px] bg-[var(--surface)] text-[var(--muted)]">{c.frecuencia}</span>}
            </div>
            {c.proposito && <p className="text-[var(--muted)] mt-1">{c.proposito}</p>}
            {c.integrantes?.length > 0 && <p className="text-[var(--muted-2)] mt-1">{c.integrantes.join(' · ')}</p>}
          </div>
        ))}
      </div>
    </div>
    <div>
      <p className="text-[11px] uppercase font-bold tracking-wide text-[var(--muted-2)] mb-2">Roles clave</p>
      <div className="space-y-1.5">
        {(data.roles || []).map((r: any, i: number) => (
          <div key={i} className="p-2.5 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-xs">
            <div className="flex items-center gap-2">
              <strong className="text-[var(--ink)]">{r.titulo}</strong>
              {r.reporta_a && <span className="text-[10px] text-[var(--muted-2)]">→ reporta a {r.reporta_a}</span>}
            </div>
            {r.responsabilidades?.length > 0 && (
              <p className="text-[var(--muted)] mt-0.5">{r.responsabilidades.join(' · ')}</p>
            )}
          </div>
        ))}
      </div>
    </div>
    {data.cadencia?.length > 0 && (
      <div className="flex flex-wrap gap-1 pt-2 border-t border-[var(--border)]">
        {data.cadencia.map((c: string, i: number) => (
          <span key={i} className="px-2 py-0.5 rounded text-[10px] bg-[var(--surface-2)] text-[var(--ink-2)] border border-[var(--border)]">🗓 {c}</span>
        ))}
      </div>
    )}
  </div>
);

// ─── Quick Wins ───────────────────────────────────────────────────

const LEVEL_BADGE: Record<string, string> = {
  ALTO: 'text-red-500 bg-red-500/10',
  MEDIO: 'text-yellow-500 bg-yellow-500/10',
  BAJO: 'text-blue-500 bg-blue-500/10',
};

const QuickWinsRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4 overflow-y-auto max-h-[520px]">
    {data.contexto && <p className="text-xs text-[var(--muted)] italic">{data.contexto}</p>}
    <div className="space-y-2">
      {(data.quick_wins || []).map((q: any, i: number) => (
        <div key={i} className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-xs">
          <div className="flex items-start justify-between gap-2">
            <strong className="text-[var(--ink)]">{q.titulo}</strong>
            <div className="flex gap-1 flex-shrink-0">
              {q.impacto && <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${LEVEL_BADGE[q.impacto] || ''}`}>Imp {q.impacto}</span>}
              {q.esfuerzo && <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${LEVEL_BADGE[q.esfuerzo] || ''}`}>Esf {q.esfuerzo}</span>}
            </div>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-0.5 mt-1.5 text-[10px] text-[var(--muted-2)]">
            {q.responsable && <span>👤 {q.responsable}</span>}
            {q.plazo && <span>⏱ {q.plazo}</span>}
          </div>
        </div>
      ))}
    </div>
    {data.proximos_pasos?.length > 0 && (
      <div>
        <p className="text-[11px] uppercase font-bold tracking-wide text-[var(--muted-2)] mb-1.5">Próximos pasos</p>
        <ul className="space-y-1">
          {data.proximos_pasos.map((p: string, i: number) => (
            <li key={i} className="flex items-start gap-2 text-xs text-[var(--ink-2)]">
              <span className="text-[var(--accent)] font-bold">{i + 1}.</span>{p}
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
);

// ─── EHS ──────────────────────────────────────────────────────────

const EHSRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4 overflow-y-auto max-h-[520px]">
    <div>
      <h4 className="font-bold text-[var(--ink)]">{data.titulo}</h4>
      {data.alcance && <p className="text-xs text-[var(--muted)] mt-0.5">{data.alcance}</p>}
    </div>
    <div className="space-y-1.5">
      {(data.peligros || []).map((p: any, i: number) => (
        <div key={i} className="flex items-start gap-2 p-2.5 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-xs">
          <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase flex-shrink-0 ${LEVEL_BADGE[p.nivel] || ''}`}>{p.nivel}</span>
          <div>
            <strong className="text-[var(--ink)]">{p.peligro}</strong>
            {p.control && <p className="text-[var(--muted)] mt-0.5">🛡 {p.control}</p>}
          </div>
        </div>
      ))}
    </div>
    <SOPChips label="EPP requerido" items={data.epp} color="#0ea5e9" />
    {data.procedimientos?.length > 0 && (
      <div>
        <p className="text-[10px] uppercase font-bold tracking-wide text-[var(--muted-2)] mb-1">Procedimientos</p>
        <div className="space-y-1">
          {data.procedimientos.map((pr: any, i: number) => (
            <div key={i} className="text-xs"><strong className="text-[var(--ink)]">{pr.nombre}.</strong> <span className="text-[var(--muted)]">{pr.descripcion}</span></div>
          ))}
        </div>
      </div>
    )}
    <div className="grid grid-cols-2 gap-3 pt-2 border-t border-[var(--border)]">
      <SOPChips label="Normativa" items={data.normativa} color="#a855f7" />
      <SOPChips label="Responsables" items={data.responsables} color="#22c55e" />
    </div>
  </div>
);

// ─── Análisis de Costos ───────────────────────────────────────────

const CostosRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4 overflow-y-auto max-h-[520px]">
    <div>
      <h4 className="font-bold text-[var(--ink)]">{data.titulo}</h4>
      {data.periodo && <p className="text-xs text-[var(--muted-2)]">Periodo: {data.periodo}</p>}
    </div>
    <div className="space-y-2">
      {(data.categorias || []).map((c: any, i: number) => (
        <div key={i} className="text-xs">
          <div className="flex justify-between mb-0.5">
            <span className="text-[var(--ink)]">{c.categoria}</span>
            <span className="font-semibold text-[var(--ink-2)]">{c.monto}{c.porcentaje != null ? ` · ${c.porcentaje}%` : ''}</span>
          </div>
          <div className="h-2 rounded-full bg-[var(--surface-2)] overflow-hidden">
            <div className="h-full rounded-full bg-[var(--accent)]" style={{ width: `${c.porcentaje || 0}%` }} />
          </div>
        </div>
      ))}
    </div>
    {data.hallazgos?.length > 0 && (
      <div>
        <p className="text-[10px] uppercase font-bold tracking-wide text-[var(--muted-2)] mb-1">Hallazgos</p>
        <ul className="list-disc pl-4 text-xs text-[var(--muted)] space-y-0.5">
          {data.hallazgos.map((h: string, i: number) => <li key={i}>{h}</li>)}
        </ul>
      </div>
    )}
    {data.ahorros_potenciales?.length > 0 && (
      <div>
        <p className="text-[10px] uppercase font-bold tracking-wide text-green-500 mb-1">Ahorros potenciales</p>
        <div className="space-y-1.5">
          {data.ahorros_potenciales.map((a: any, i: number) => (
            <div key={i} className="p-2.5 rounded-lg bg-[var(--surface-2)] border-l-4 border-green-500 text-xs">
              <div className="flex justify-between"><strong className="text-[var(--ink)]">{a.concepto}</strong><span className="text-green-500 font-bold">{a.ahorro_estimado}</span></div>
              {a.accion && <p className="text-[var(--muted)] mt-0.5">{a.accion}</p>}
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
);

// ─── Visual Management Pack ───────────────────────────────────────

const VisualMgmtRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4 overflow-y-auto max-h-[520px]">
    <h4 className="font-bold text-[var(--ink)]">{data.titulo}</h4>
    <div className="space-y-2">
      {(data.tableros || []).map((t: any, i: number) => (
        <div key={i} className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-xs">
          <div className="flex items-center justify-between">
            <strong className="text-[var(--ink)]">📊 {t.nombre}</strong>
            {t.frecuencia && <span className="px-1.5 py-0.5 rounded text-[10px] bg-[var(--surface)] text-[var(--muted)]">{t.frecuencia}</span>}
          </div>
          {t.proposito && <p className="text-[var(--muted)] mt-1">{t.proposito}</p>}
          {t.metricas?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {t.metricas.map((m: string, j: number) => (
                <span key={j} className="px-1.5 py-0.5 rounded text-[10px] bg-[var(--surface)] text-[var(--ink-2)] border border-[var(--border)]">{m}</span>
              ))}
            </div>
          )}
          {t.ubicacion && <p className="text-[10px] text-[var(--muted-2)] mt-1">📍 {t.ubicacion}</p>}
        </div>
      ))}
    </div>
    <SOPChips label="Elementos 5S" items={data.elementos_5s} color="#f59e0b" />
    {data.rutinas?.length > 0 && (
      <div>
        <p className="text-[10px] uppercase font-bold tracking-wide text-[var(--muted-2)] mb-1">Rutinas</p>
        <div className="space-y-1">
          {data.rutinas.map((r: any, i: number) => (
            <div key={i} className="text-xs flex flex-wrap gap-x-3 text-[var(--muted)]">
              <strong className="text-[var(--ink)]">{r.nombre}</strong>
              {r.cadencia && <span>🗓 {r.cadencia}</span>}
              {r.responsable && <span>👤 {r.responsable}</span>}
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
);

// ─── Manual Maestro ───────────────────────────────────────────────

const ManualMaestroRenderer: React.FC<{ data: any }> = ({ data }) => (
  <div className="space-y-4 overflow-y-auto max-h-[520px]">
    <div>
      <div className="flex items-center gap-2">
        <h4 className="font-bold text-[var(--ink)]">{data.titulo}</h4>
        {data.version && <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[var(--accent)] text-white">{data.version}</span>}
      </div>
      {data.proposito && <p className="text-xs text-[var(--muted)] mt-0.5">{data.proposito}</p>}
      {data.audiencia && <p className="text-[10px] text-[var(--muted-2)] mt-0.5">👥 {data.audiencia}</p>}
    </div>
    <div className="space-y-2">
      {(data.secciones || []).map((s: any, i: number) => (
        <div key={i} className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-xs">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-md bg-[var(--accent)] text-white flex items-center justify-center text-[11px] font-bold flex-shrink-0">{s.numero}</span>
            <strong className="text-[var(--ink)]">{s.titulo}</strong>
          </div>
          {s.descripcion && <p className="text-[var(--muted)] mt-1">{s.descripcion}</p>}
          {s.contenido_clave?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {s.contenido_clave.map((c: string, j: number) => (
                <span key={j} className="px-1.5 py-0.5 rounded text-[10px] bg-[var(--surface)] text-[var(--ink-2)] border border-[var(--border)]">{c}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  </div>
);

// ─── Json to Markdown Converter ───────────────────────────────────
const jsonToMarkdown = (title: string, data: any): string => {
  let md = `# ${title}\n\n`;
  md += `> Generado por Cortex AI · ${new Date().toLocaleDateString()}\n\n`;

  const render = (obj: any, depth: number = 2): string => {
    let result = '';
    for (const [key, value] of Object.entries(obj)) {
      const heading = '#'.repeat(Math.min(depth, 4));
      if (Array.isArray(value)) {
        result += `${heading} ${key.replace(/_/g, ' ').toUpperCase()}\n\n`;
        value.forEach((item, i) => {
          if (typeof item === 'string') {
            result += `- ${item}\n`;
          } else if (typeof item === 'object') {
            result += `**${i + 1}.** `;
            result += Object.entries(item).map(([k, v]) => `${k}: ${v}`).join(' | ');
            result += '\n\n';
          }
        });
        result += '\n';
      } else if (typeof value === 'object' && value !== null) {
        result += `${heading} ${key}\n\n`;
        result += render(value, depth + 1);
      } else {
        result += `**${key}**: ${value}\n\n`;
      }
    }
    return result;
  };

  md += render(data);
  return md;
};
