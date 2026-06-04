import React from 'react';
import { deliverables } from '../../data/mockData';
import { FileText, FileSpreadsheet, MonitorPlay, Download, FileArchive } from 'lucide-react';

const getFileIcon = (type: string) => {
  switch (type) {
    case 'PDF': return <FileText size={24} className="text-red-500" />;
    case 'XLSX': return <FileSpreadsheet size={24} className="text-emerald-500" />;
    case 'PPTX': return <MonitorPlay size={24} className="text-orange-500" />;
    case 'PBIX': return <FileArchive size={24} className="text-amber-500" />;
    case 'DOCX': return <FileText size={24} className="text-blue-500" />;
    default: return <FileText size={24} className="text-[var(--muted)]" />;
  }
};

export const Deliverables: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-bold text-2xl">Entregables y Evidencias</h2>
          <p className="text-sm text-[var(--muted)] mt-1">Archivos y documentos generados en el proyecto</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {deliverables.map((doc) => (
          <div 
            key={doc.id} 
            className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 transition-all duration-200 hover:shadow-card hover:border-[var(--accent)] group cursor-pointer flex flex-col h-full"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="p-2.5 bg-[var(--surface-2)] rounded-lg">
                {getFileIcon(doc.type)}
              </div>
              <button className="p-1.5 text-[var(--muted)] hover:text-[var(--accent)] hover:bg-[var(--accent-tint)] rounded-md opacity-0 group-hover:opacity-100 transition-all">
                <Download size={16} />
              </button>
            </div>
            
            <h3 className="font-semibold text-[var(--ink)] text-sm mb-1 flex-1 line-clamp-2" title={doc.name}>
              {doc.name}
            </h3>
            
            <div className="mt-4 pt-4 border-t border-[var(--border)] flex items-center justify-between text-[10px] font-mono uppercase text-[var(--muted)]">
              <div className="flex items-center gap-2">
                <span className="font-bold">{doc.type}</span>
                <span>•</span>
                <span>{doc.size}</span>
              </div>
              <span className="bg-[var(--surface-2)] px-1.5 py-0.5 rounded">Fase {doc.phase}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
