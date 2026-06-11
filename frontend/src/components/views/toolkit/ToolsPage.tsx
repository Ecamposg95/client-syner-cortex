import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card } from '../../ui/Card';
import { ArrowLeft, Play, Loader2, FileText, ChevronRight } from 'lucide-react';
import apiClient from '../../../api/client';

interface Tool {
  id: number;
  name: string;
  description: string;
  toolkit_id: number;
}

export const ToolsPage: React.FC = () => {
  const { toolkitId } = useParams();
  const navigate = useNavigate();
  const [tools, setTools] = useState<Tool[]>([]);
  const [toolkitName, setToolkitName] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [toolsRes, toolkitsRes] = await Promise.all([
          apiClient.get(`/toolkits/${toolkitId}/tools`),
          apiClient.get('/toolkits'),
        ]);
        setTools(toolsRes.data);
        const tk = toolkitsRes.data.find((t: any) => t.id === Number(toolkitId));
        if (tk) setToolkitName(tk.name);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [toolkitId]);

  if (loading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center gap-4">
        <Loader2 size={36} className="animate-spin text-[var(--accent)]" />
        <p className="text-sm text-[var(--muted)]">Cargando herramientas...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate('/toolkits')}
        className="flex items-center gap-2 text-sm text-[var(--muted)] hover:text-[var(--ink)] transition-colors"
      >
        <ArrowLeft size={16} /> Volver a Toolkits
      </button>

      <div className="flex flex-col gap-1">
        <h2 className="font-extrabold text-2xl">{toolkitName}</h2>
        <p className="text-sm text-[var(--muted)]">
          {tools.length} herramienta{tools.length !== 1 ? 's' : ''} disponible{tools.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {tools.map((tool) => (
          <Card
            key={tool.id}
            className="p-6 cursor-pointer group hover:border-[var(--accent)] transition-all duration-200"
            onClick={() => navigate(`/tools/${tool.id}/run`)}
          >
            <div className="flex items-start justify-between">
              <div className="flex gap-4 items-start">
                <div className="p-3 rounded-xl bg-[var(--surface-2)] text-[var(--accent)] group-hover:bg-[var(--accent)] group-hover:text-white transition-colors">
                  <FileText size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-[var(--ink)] mb-1">{tool.name}</h3>
                  <p className="text-sm text-[var(--muted)] leading-relaxed">{tool.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-[var(--muted-2)] group-hover:text-[var(--accent)] transition-colors flex-shrink-0 mt-1">
                <Play size={16} />
                <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {tools.length === 0 && (
        <Card className="p-12 text-center">
          <p className="text-[var(--muted)]">Este toolkit aún no tiene herramientas configuradas.</p>
          <p className="text-xs text-[var(--muted-2)] mt-2">Las herramientas se irán desbloqueando conforme avance la consultoría.</p>
        </Card>
      )}
    </div>
  );
};
