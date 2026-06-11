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
