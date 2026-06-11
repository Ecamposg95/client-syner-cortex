import React, { useEffect, useState } from 'react';
import { Card } from '../ui/Card';
import { AlertTriangle, Scale, Loader2, Check, X } from 'lucide-react';
import apiClient from '../../api/client';
import { useAuthStore } from '../../store/authStore';

interface Risk {
  id: number;
  description: string;
  category: string;
  probability: string;
  impact: string;
  status: string;
}

interface Decision {
  id: number;
  title: string;
  context: string;
  syner_recommendation: string;
  status: string;
  deadline: string;
}

export const DecisionsView: React.FC = () => {
  const user = useAuthStore((s) => s.user);
  const [risks, setRisks] = useState<Risk[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);
  const [patchingId, setPatchingId] = useState<number | null>(null);

  const fetchDecisions = async () => {
    const dRes = await apiClient.get('/clevel/decisions');
    setDecisions(dRes.data);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [rRes, dRes] = await Promise.all([
          apiClient.get('/clevel/risks'),
          apiClient.get('/clevel/decisions')
        ]);
        setRisks(rRes.data);
        setDecisions(dRes.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleDecision = async (id: number, status: 'APPROVED' | 'REJECTED') => {
    setPatchingId(id);
    try {
      await apiClient.patch(`/clevel/decisions/${id}`, { status });
      await fetchDecisions();
    } catch (e) {
      console.error(e);
    } finally {
      setPatchingId(null);
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-[var(--accent)]" /></div>;

  return (
    <div className="space-y-8">
      
      {/* Decisions Log */}
      <div className="space-y-4">
        <div className="flex flex-col gap-1">
          <h2 className="font-bold text-2xl flex items-center gap-2"><Scale className="text-[var(--accent)]"/> Decision Log</h2>
          <p className="text-sm text-[var(--muted)]">Resoluciones pendientes para la junta directiva</p>
        </div>
        <div className="grid grid-cols-1 gap-4">
          {decisions.map(d => (
            <Card key={d.id} className="p-5 border-l-4" style={{ borderLeftColor: d.status === 'PENDING' ? 'var(--warn)' : 'var(--pos)' }}>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-lg text-[var(--ink)]">{d.title}</h3>
                  <p className="text-sm text-[var(--muted)] mt-1">{d.context}</p>
                </div>
                <span className="px-2 py-1 text-xs font-bold rounded-md bg-[var(--surface-2)]">
                  {d.status}
                </span>
              </div>
              <div className="mt-4 p-3 bg-[var(--surface-2)] rounded-lg text-sm">
                <span className="font-semibold block text-[var(--accent-strong)] mb-1">Recomendación Syner:</span>
                <p>{d.syner_recommendation}</p>
              </div>

              {d.status === 'PENDING' && (
                <div className="mt-4 flex items-center gap-3">
                  <button
                    type="button"
                    disabled={patchingId === d.id}
                    onClick={() => handleDecision(d.id, 'APPROVED')}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-semibold text-white transition-colors disabled:opacity-50"
                    style={{ background: 'var(--pos)' }}
                  >
                    {patchingId === d.id ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
                    Aprobar
                  </button>
                  <button
                    type="button"
                    disabled={patchingId === d.id}
                    onClick={() => handleDecision(d.id, 'REJECTED')}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-semibold transition-colors disabled:opacity-50 border border-[var(--border)] text-[var(--ink)] hover:bg-[var(--surface-2)]"
                  >
                    {patchingId === d.id ? <Loader2 size={14} className="animate-spin" /> : <X size={14} />}
                    Rechazar
                  </button>
                  {user?.user_type === 'CLIENT_USER' && (
                    <span className="text-[10px] text-[var(--muted-2)] uppercase tracking-wide">Decisión del cliente</span>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      </div>

      {/* Risk Register */}
      <div className="space-y-4 pt-4 border-t border-[var(--border)]">
        <div className="flex flex-col gap-1">
          <h2 className="font-bold text-2xl flex items-center gap-2"><AlertTriangle className="text-red-500"/> Risk Register</h2>
          <p className="text-sm text-[var(--muted)]">Riesgos corporativos y operativos</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {risks.map(r => (
            <Card key={r.id} className="p-5">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-[var(--ink)]">{r.description}</h3>
              </div>
              <div className="flex gap-2 mb-3">
                <span className="text-[10px] uppercase font-bold px-2 py-1 bg-red-500/10 text-red-500 rounded">Impacto: {r.impact}</span>
                <span className="text-[10px] uppercase font-bold px-2 py-1 bg-[var(--surface-2)] rounded">Prob: {r.probability}</span>
                <span className="text-[10px] uppercase font-bold px-2 py-1 bg-[var(--surface-2)] rounded">{r.category}</span>
              </div>
              <p className="text-sm text-[var(--muted)]">Status: <strong>{r.status}</strong></p>
            </Card>
          ))}
        </div>
      </div>

    </div>
  );
};
