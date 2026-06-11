import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../ui/Card';
import {
  Search, Landmark, Settings, Activity, Monitor, Shield, Users,
  Briefcase, DollarSign, Rocket, Loader2, ChevronRight, Wrench
} from 'lucide-react';
import apiClient from '../../../api/client';

const TOOLKIT_ICONS: Record<string, React.ReactNode> = {
  'search': <Search size={28} />,
  'landmark': <Landmark size={28} />,
  'settings': <Settings size={28} />,
  'activity': <Activity size={28} />,
  'monitor': <Monitor size={28} />,
  'shield': <Shield size={28} />,
  'users': <Users size={28} />,
  'briefcase': <Briefcase size={28} />,
  'dollar-sign': <DollarSign size={28} />,
  'rocket': <Rocket size={28} />,
};

const TOOLKIT_GRADIENTS = [
  'linear-gradient(135deg, #6366f1, #8b5cf6)',
  'linear-gradient(135deg, #0ea5e9, #06b6d4)',
  'linear-gradient(135deg, #f97316, #ef4444)',
  'linear-gradient(135deg, #10b981, #059669)',
  'linear-gradient(135deg, #f59e0b, #d97706)',
  'linear-gradient(135deg, #ec4899, #be185d)',
  'linear-gradient(135deg, #8b5cf6, #7c3aed)',
  'linear-gradient(135deg, #14b8a6, #0d9488)',
  'linear-gradient(135deg, #64748b, #475569)',
  'linear-gradient(135deg, #f43f5e, #e11d48)',
];

interface Toolkit {
  id: number;
  name: string;
  description: string;
  icon: string;
}

export const ToolkitsPage: React.FC = () => {
  const [toolkits, setToolkits] = useState<Toolkit[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    apiClient.get('/toolkits')
      .then(res => setToolkits(res.data))
      .catch(e => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-4">
        <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
        <p className="text-sm text-[var(--muted)]">Cargando catálogo de metodologías...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl text-white" style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}>
            <Wrench size={24} />
          </div>
          <div>
            <h2 className="font-extrabold text-2xl">Cortex Consulting Toolkit</h2>
            <p className="text-sm text-[var(--muted)]">
              {toolkits.length} metodologías disponibles · Herramientas asistidas por IA
            </p>
          </div>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {toolkits.map((tk, idx) => (
          <Card
            key={tk.id}
            className="p-0 overflow-hidden cursor-pointer group hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5"
            onClick={() => navigate(`/toolkits/${tk.id}/tools`)}
          >
            {/* Color bar */}
            <div className="h-1.5 w-full" style={{ background: TOOLKIT_GRADIENTS[idx % TOOLKIT_GRADIENTS.length] }} />

            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div
                  className="p-3 rounded-xl text-white"
                  style={{ background: TOOLKIT_GRADIENTS[idx % TOOLKIT_GRADIENTS.length] }}
                >
                  {TOOLKIT_ICONS[tk.icon] || <Search size={28} />}
                </div>
                <ChevronRight
                  size={20}
                  className="text-[var(--muted-2)] group-hover:text-[var(--accent)] group-hover:translate-x-1 transition-all"
                />
              </div>

              <h3 className="font-bold text-base text-[var(--ink)] mb-1 leading-tight">{tk.name}</h3>
              <p className="text-xs text-[var(--muted)] leading-relaxed">{tk.description}</p>
            </div>
          </Card>
        ))}
      </div>

      {toolkits.length === 0 && (
        <div className="text-center py-16">
          <p className="text-[var(--muted)]">No hay toolkits registrados aún.</p>
        </div>
      )}
    </div>
  );
};
