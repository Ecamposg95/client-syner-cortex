import React, { useEffect, useRef, useState } from 'react';
import { useWorkspaceStore } from '../store/workspaceStore';
import {
  Upload,
  File,
  Trash2,
  Loader2,
  CheckCircle,
  AlertCircle,
  FolderKanban,
  FileText
} from 'lucide-react';

export const Vault: React.FC = () => {
  const { activeWorkspace, documents, fetchDocuments, uploadDocument, deleteDocument, isUploading, isLoading, error } = useWorkspaceStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    if (activeWorkspace) {
      fetchDocuments();
    }
  }, [activeWorkspace, fetchDocuments]);

  // Periodic polling for processing documents (every 5 seconds)
  useEffect(() => {
    let interval: NodeJS.Timeout;
    const hasProcessingDocs = documents.some(doc => doc.status === 'PROCESSING');
    
    if (activeWorkspace && hasProcessingDocs) {
      interval = setInterval(() => {
        fetchDocuments();
      }, 5000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [documents, activeWorkspace, fetchDocuments]);

  if (!activeWorkspace) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
        <FolderKanban size={48} className="text-violet-500 mb-4 animate-pulse" />
        <h3 className="text-xl font-bold text-white mb-2">No Workspace Selected</h3>
        <p className="text-sm text-slate-400 max-w-sm">
          Please select or create a project workspace from the sidebar menu to view your document vaults.
        </p>
      </div>
    );
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await handleFileUpload(e.target.files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    const success = await uploadDocument(file);
    if (success) {
      setSuccessMsg(`Document '${file.name}' successfully uploaded! Processing started.`);
      setTimeout(() => setSuccessMsg(''), 4000);
    }
  };

  const handleDelete = async (docId: number) => {
    if (window.confirm("Are you sure you want to delete this document? All parsed knowledge chunks will be removed from context.")) {
      await deleteDocument(docId);
    }
  };

  return (
    <div className="space-y-8">
      
      {/* PAGE HEADER */}
      <div>
        <h2 className="font-display font-extrabold text-3xl tracking-tight text-white">
          Cortex Knowledge Vault
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Upload and index internal documentation (PDFs, TXT, MD) to train the workspace RAG context.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* FILE UPLOAD DROPZONE */}
        <div className="lg:col-span-1 space-y-4">
          <h3 className="font-display font-bold text-lg text-white">Upload Documents</h3>
          
          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`h-64 border-2 border-dashed rounded-3xl flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-all duration-300 ${
              dragActive
                ? 'border-violet-500 bg-violet-600/5'
                : 'border-white/10 hover:border-violet-500/50 hover:bg-white/5 bg-[#0C1220]/40'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.txt,.md"
              className="hidden"
            />
            {isUploading ? (
              <div className="space-y-3">
                <Loader2 size={36} className="text-violet-500 animate-spin mx-auto" />
                <p className="text-sm font-semibold text-white">Uploading file...</p>
                <p className="text-xs text-slate-500">Wait, processing RAG chunks</p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-xl bg-violet-600/10 flex items-center justify-center mx-auto text-violet-400">
                  <Upload size={24} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-200">
                    Drag and drop file here, or click to browse
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Supports PDF, TXT, or Markdown (Max 10MB)
                  </p>
                </div>
              </div>
            )}
          </div>

          {successMsg && (
            <div className="p-3 bg-emerald-950/30 border border-emerald-500/20 text-emerald-300 text-xs rounded-xl flex items-start space-x-2 animate-pulse">
              <CheckCircle size={16} className="mt-0.5 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-950/30 border border-red-500/20 text-red-300 text-xs rounded-xl flex items-start space-x-2">
              <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* DOCUMENTS LIST */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="font-display font-bold text-lg text-white">Indexed Documents</h3>
          
          {isLoading && documents.length === 0 ? (
            <div className="glass-panel rounded-2xl p-8 text-center">
              <Loader2 size={32} className="text-violet-500 animate-spin mx-auto mb-2" />
              <p className="text-sm text-slate-400">Loading vault records...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="glass-panel rounded-2xl p-10 text-center flex flex-col items-center justify-center space-y-2">
              <File size={36} className="text-slate-600" />
              <h4 className="text-sm font-semibold text-white">No documents uploaded</h4>
              <p className="text-xs text-slate-500 max-w-xs">
                To ask questions about your operations or run context-aware consultations, upload corporate documents first.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div key={doc.id} className="glass-panel rounded-2xl p-4 flex items-center justify-between transition-all">
                  <div className="flex items-center space-x-3.5 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-indigo-600/10 flex items-center justify-center text-indigo-400 flex-shrink-0">
                      <FileText size={20} />
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-sm font-semibold text-white truncate pr-4">
                        {doc.name}
                      </h4>
                      <p className="text-xs text-slate-500 uppercase tracking-widest mt-0.5">
                        {doc.file_type} • Ingested {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    {/* Status Badge */}
                    {doc.status === 'PROCESSING' ? (
                      <span className="px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[10px] font-semibold tracking-wider flex items-center space-x-1">
                        <Loader2 size={10} className="animate-spin" />
                        <span>PROCESSING</span>
                      </span>
                    ) : doc.status === 'COMPLETED' ? (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-semibold tracking-wider flex items-center space-x-1">
                        <CheckCircle size={10} />
                        <span>READY</span>
                      </span>
                    ) : (
                      <span
                        title={doc.error_message || 'Indexing failed'}
                        className="px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-[10px] font-semibold tracking-wider flex items-center space-x-1"
                      >
                        <AlertCircle size={10} />
                        <span>FAILED</span>
                      </span>
                    )}

                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-1.5 text-slate-500 hover:text-red-400 rounded-lg hover:bg-white/5 transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

    </div>
  );
};
export default Vault;
