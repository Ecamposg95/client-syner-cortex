import React, { useEffect, useRef, useState } from 'react';
import { Card } from '../ui/Card';
import { FolderClosed, FileText, Loader2, Download, Upload, CheckCircle2 } from 'lucide-react';
import apiClient from '../../api/client';

interface Deliverable {
  id: number;
  title: string;
  type: string;
  status: string;
  executive_summary: string;
}

interface Workspace {
  id: number;
  name: string;
}

export const Deliverables: React.FC = () => {
  const [deliverables, setDeliverables] = useState<Deliverable[]>([]);
  const [loading, setLoading] = useState(true);
  const [workspaceId, setWorkspaceId] = useState<number | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchData = async () => {
    const engRes = await apiClient.get('/clevel/engagements');
    if (engRes.data.length > 0) {
      const res = await apiClient.get(`/clevel/engagements/${engRes.data[0].id}/deliverables`);
      setDeliverables(res.data);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const [wsRes] = await Promise.all([
          apiClient.get<Workspace[]>('/workspaces'),
          fetchData(),
        ]);
        if (wsRes.data && wsRes.data.length > 0) {
          setWorkspaceId(wsRes.data[0].id);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || workspaceId == null) return;
    setUploading(true);
    setUploadMsg(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('workspace_id', String(workspaceId));
      await apiClient.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadMsg(`"${file.name}" subido correctamente.`);
      await fetchData();
    } catch (err) {
      console.error(err);
      setUploadMsg('No se pudo subir el archivo.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-[var(--accent)]" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h2 className="font-bold text-2xl flex items-center gap-2"><FolderClosed className="text-[var(--accent)]"/> Deliverables Repository</h2>
          <p className="text-sm text-[var(--muted)]">Repositorio ejecutivo de entregables estratégicos</p>
        </div>
        <div className="flex flex-col items-start sm:items-end gap-1.5">
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleFileChange}
            disabled={uploading || workspaceId == null}
          />
          <button
            type="button"
            disabled={uploading || workspaceId == null}
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-semibold text-white transition-colors disabled:opacity-50"
            style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}
          >
            {uploading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
            Subir evidencia
          </button>
          {uploadMsg && (
            <span className="inline-flex items-center gap-1 text-xs text-[var(--muted)]">
              <CheckCircle2 size={12} className="text-[var(--pos)]" /> {uploadMsg}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {deliverables.map((del) => (
          <Card key={del.id} className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex gap-3 items-center">
                <div className="p-3 bg-[var(--surface-2)] rounded-lg text-[var(--ink)]">
                  <FileText size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-[var(--ink)]">{del.title}</h3>
                  <span className="text-xs font-mono text-[var(--muted-2)] uppercase">{del.type}</span>
                </div>
              </div>
              <span className={`px-2 py-1 text-xs font-bold rounded-md ${del.status === 'DELIVERED' ? 'bg-green-500/10 text-green-500' : 'bg-blue-500/10 text-blue-500'}`}>
                {del.status}
              </span>
            </div>
            
            <div className="p-4 bg-[var(--surface-2)] rounded-lg text-sm mb-4">
              <span className="font-semibold block text-[var(--ink-2)] mb-1">Resumen Ejecutivo:</span>
              <p className="text-[var(--muted)]">{del.executive_summary}</p>
            </div>

            <button className="w-full flex items-center justify-center gap-2 py-2 border border-[var(--border)] rounded-md hover:bg-[var(--surface-2)] transition-colors text-sm font-semibold">
              <Download size={16} /> Descargar
            </button>
          </Card>
        ))}
      </div>
    </div>
  );
};
