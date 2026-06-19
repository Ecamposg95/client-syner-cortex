import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card } from '../../ui/Card';
import { CheckCircle, ArrowLeft, Loader2, Save, FileJson, Share2 } from 'lucide-react';
import apiClient from '../../../api/client';
import { useAuthStore } from '../../../store/authStore';

export const ToolRunReviewPage: React.FC = () => {
  const { runId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [run, setRun] = useState<any>(null);
  const [jsonText, setJsonText] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRun = async () => {
      try {
        const res = await apiClient.get(`/tool-runs/${runId}`);
        setRun(res.data);
        if (res.data.outputs && res.data.outputs.length > 0) {
          setJsonText(JSON.stringify(res.data.outputs[0].content_json, null, 2));
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchRun();
  }, [runId]);

  const handleSaveAndApprove = async () => {
    setError(null);
    try {
      const parsed = JSON.parse(jsonText);
      setSaving(true);
      
      // Save output
      await apiClient.post(`/tool-runs/${runId}/outputs`, {
        content_json: parsed
      });

      // Update status
      await apiClient.patch(`/tool-runs/${runId}/status`, { status: 'APPROVED' });
      
      // Update local state
      setRun({ ...run, status: 'APPROVED' });
      alert('Revisión guardada y aprobada correctamente.');
      navigate(-1);
    } catch (e: any) {
      setError('JSON inválido o error al guardar: ' + e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleShare = async () => {
    setError(null);
    setSaving(true);
    try {
      // Crew-only transition gated by SHARE_WITH_CLIENT in the backend.
      await apiClient.patch(`/tool-runs/${runId}/status`, { status: 'CLIENT_SHARED' });
      setRun({ ...run, status: 'CLIENT_SHARED' });
      alert('Entregable compartido con el cliente. Ahora es visible en su portal.');
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'No se pudo compartir con el cliente.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 flex justify-center">
        <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  if (!run) {
    return <div className="p-8 text-[var(--muted)]">ToolRun no encontrado.</div>;
  }

  return (
    <div className="space-y-6">
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-sm text-[var(--muted)] hover:text-[var(--ink)] transition-colors">
        <ArrowLeft size={16} /> Volver
      </button>

      <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
        <div>
          <h2 className="font-extrabold text-2xl flex items-center gap-2">
            <FileJson className="text-[var(--accent)]" /> Revisión de Consultor
          </h2>
          <p className="text-sm text-[var(--muted)] mt-1">Ajusta el output generado de "{run.tool_name}" antes de entregarlo.</p>
        </div>
        
        <div className="flex items-center gap-2">
          {user?.user_type === 'SYNER_CREW' && run.status !== 'APPROVED' && run.status !== 'CLIENT_SHARED' && (
            <button
              onClick={handleSaveAndApprove}
              disabled={saving}
              className="px-4 py-2 text-sm font-semibold bg-green-500 text-white rounded-lg hover:opacity-90 flex items-center gap-2 disabled:opacity-50"
            >
              {saving ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle size={16} />}
              Guardar y Aprobar
            </button>
          )}
          {/* Once approved, crew can push the deliverable to the client portal. */}
          {user?.user_type === 'SYNER_CREW' && run.status === 'APPROVED' && (
            <button
              onClick={handleShare}
              disabled={saving}
              className="px-4 py-2 text-sm font-semibold text-white rounded-lg hover:opacity-90 flex items-center gap-2 disabled:opacity-50"
              style={{ background: 'var(--accent)' }}
            >
              {saving ? <Loader2 size={16} className="animate-spin" /> : <Share2 size={16} />}
              Compartir con cliente
            </button>
          )}
          {run.status === 'CLIENT_SHARED' && (
            <span className="px-3 py-1.5 text-xs font-bold rounded-lg bg-[var(--accent-tint,rgba(37,99,235,0.1))] text-[var(--accent-strong)] flex items-center gap-1.5">
              <Share2 size={13} /> Compartido con el cliente
            </span>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 text-red-500 border border-red-500/20 rounded-lg text-sm font-semibold">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Editor */}
        <div className="space-y-4">
          <h3 className="font-bold text-lg text-[var(--ink-2)]">Editor de Datos (JSON)</h3>
          <Card className="p-0 overflow-hidden border border-[var(--border)] h-[600px] flex flex-col">
            <div className="bg-[var(--surface-2)] px-4 py-2 text-xs font-mono text-[var(--muted)] border-b border-[var(--border)]">
              content.json
            </div>
            <textarea
              className="flex-1 w-full p-4 bg-[var(--surface)] text-[var(--ink)] font-mono text-sm resize-none outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-inset"
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
              disabled={run.status === 'APPROVED'}
              spellCheck={false}
            />
          </Card>
        </div>

        {/* Info */}
        <div className="space-y-4">
          <h3 className="font-bold text-lg text-[var(--ink-2)]">Detalles de la Ejecución</h3>
          <Card className="p-5 space-y-4">
            <div>
              <span className="block text-[10px] uppercase font-bold text-[var(--muted)] mb-1">Status Actual</span>
              <span className={`px-2.5 py-1 text-xs font-bold rounded-md ${
                run.status === 'APPROVED' ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500'
              }`}>
                {run.status}
              </span>
            </div>
            <div>
              <span className="block text-[10px] uppercase font-bold text-[var(--muted)] mb-1">Herramienta</span>
              <p className="font-semibold text-sm">{run.tool_name}</p>
            </div>
            <div>
              <span className="block text-[10px] uppercase font-bold text-[var(--muted)] mb-2">Inputs Recibidos</span>
              <div className="space-y-2">
                {run.inputs?.map((inp: any) => (
                  <div key={inp.id} className="bg-[var(--surface-2)] p-2 rounded text-xs">
                    <span className="font-bold text-[var(--accent)] capitalize">{inp.key.replace(/_/g, ' ')}:</span>
                    <span className="ml-2 text-[var(--muted)]">{inp.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
