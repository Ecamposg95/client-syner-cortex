import React, { useEffect, useState } from 'react';
import { Card } from '../ui/Card';
import { FileSearch, Loader2, AlertCircle } from 'lucide-react';
import apiClient from '../../api/client';

interface Finding {
  id: number;
  title: string;
  description: string;
  area: string;
  criticality: string;
  impact: string;
  recommendation: string;
}

export const FindingsView: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFindings = async () => {
      try {
        // Fetch engagements to get the ID, then findings. Simplified for MVP:
        const engRes = await apiClient.get('/clevel/engagements');
        if (engRes.data.length > 0) {
          const res = await apiClient.get(`/clevel/engagements/${engRes.data[0].id}/findings`);
          setFindings(res.data);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchFindings();
  }, []);

  const getCriticalityColor = (crit: string) => {
    switch(crit) {
      case 'CRITICAL': return 'text-red-500 bg-red-500/10';
      case 'HIGH': return 'text-orange-500 bg-orange-500/10';
      case 'MEDIUM': return 'text-yellow-500 bg-yellow-500/10';
      default: return 'text-blue-500 bg-blue-500/10';
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-[var(--accent)]" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h2 className="font-bold text-2xl">Findings & Diagnosis</h2>
        <p className="text-sm text-[var(--muted)]">Hallazgos estratégicos detectados por la consultoría</p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {findings.map((f) => (
          <Card key={f.id} className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <FileSearch className="text-[var(--accent)]" size={24} />
                <h3 className="font-bold text-lg text-[var(--ink)]">{f.title}</h3>
              </div>
              <span className={`px-2 py-1 rounded-md text-xs font-bold ${getCriticalityColor(f.criticality)}`}>
                {f.criticality}
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
              <div>
                <p className="font-semibold mb-1 text-[var(--ink-2)]">Descripción</p>
                <p className="text-[var(--muted)]">{f.description}</p>
              </div>
              <div>
                <p className="font-semibold mb-1 text-[var(--ink-2)]">Impacto</p>
                <p className="text-[var(--muted)]">{f.impact}</p>
              </div>
              <div className="md:col-span-2 p-4 rounded-lg bg-[var(--surface-2)] mt-2">
                <p className="font-semibold text-[var(--accent-strong)] flex items-center gap-2 mb-1">
                  <AlertCircle size={16} /> Recomendación Syner
                </p>
                <p className="text-[var(--ink)]">{f.recommendation}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
