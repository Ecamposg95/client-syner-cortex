import React, { useEffect, useState } from 'react';
import { Card } from '../ui/Card';
import { Briefcase, Calendar, Loader2 } from 'lucide-react';
import apiClient from '../../api/client';

interface Engagement {
  id: number;
  title: string;
  objective: string;
  status: string;
  start_date: string;
  end_date: string;
}

export const EngagementsView: React.FC = () => {
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEngagements = async () => {
      try {
        const res = await apiClient.get('/clevel/engagements');
        setEngagements(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchEngagements();
  }, []);

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-[var(--accent)]" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h2 className="font-bold text-2xl">Consulting Engagements</h2>
        <p className="text-sm text-[var(--muted)]">Proyectos y consultorías activas con Syner</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {engagements.map((eng) => (
          <Card key={eng.id} className="p-6 flex flex-col space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex gap-3">
                <div className="p-2 rounded-lg bg-[var(--surface-2)]">
                  <Briefcase size={24} className="text-[var(--ink)]" />
                </div>
                <div>
                  <h3 className="font-bold text-[var(--ink)]">{eng.title}</h3>
                  <span className="text-[10px] uppercase font-bold text-[var(--accent-strong)]">{eng.status}</span>
                </div>
              </div>
            </div>
            
            <p className="text-sm text-[var(--muted)]">{eng.objective}</p>
            
            <div className="flex items-center gap-4 text-xs font-mono text-[var(--muted-2)] pt-4 border-t border-[var(--border)]">
              <div className="flex items-center gap-1">
                <Calendar size={14} /> Inicio: {eng.start_date || 'N/A'}
              </div>
              <div className="flex items-center gap-1">
                <Calendar size={14} /> Fin: {eng.end_date || 'N/A'}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
