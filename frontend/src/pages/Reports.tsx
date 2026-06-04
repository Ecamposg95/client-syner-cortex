import React, { useEffect, useState } from 'react';
import { useWorkspaceStore } from '../store/workspaceStore';
import apiClient from '../api/client';
import {
  FileText,
  Loader2,
  AlertCircle,
  Download,
  Copy,
  Printer,
  Sparkles,
  TrendingUp
} from 'lucide-react';

export const Reports: React.FC = () => {
  const { activeWorkspace } = useWorkspaceStore();
  const [report, setReport] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);

  const fetchReport = async (wsId: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/reports/executive-brief', {
        params: { workspace_id: wsId }
      });
      setReport(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to compile report. Make sure a business diagnosis is complete.');
      setReport(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (activeWorkspace) {
      fetchReport(activeWorkspace.id);
    }
  }, [activeWorkspace]);

  if (!activeWorkspace) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
        <FileText size={48} className="text-violet-500 mb-4 animate-pulse" />
        <h3 className="text-xl font-bold text-white mb-2">No Workspace Selected</h3>
        <p className="text-sm text-slate-400 max-w-sm">
          Please select or create a project workspace from the sidebar menu to compile executive reports.
        </p>
      </div>
    );
  }

  const handleCopy = () => {
    if (!report) return;
    
    // Format JSON report to Markdown text for clipboard
    let text = `# SYNER CORTEX EXECUTIVE BRIEF\n`;
    text += `Workspace: ${report.workspace_name}\n`;
    text += `Organization: ${report.organization}\n`;
    text += `Compiled: ${new Date(report.generated_at).toLocaleString()}\n\n`;
    
    text += `## 1. 360-DEGREE DIAGNOSIS DIMENSIONS\n`;
    report.dimensions.forEach((d: any) => {
      text += `### ${d.name} (Rating: ${d.rating}/5)\n`;
      text += `* Findings: ${d.findings}\n`;
      text += `* Recommendation: ${d.recommendations}\n\n`;
    });
    
    text += `## 2. ROADMAP ITEMS\n`;
    report.roadmap.items.forEach((item: any) => {
      text += `* [${item.status}] [${item.dimension}] ${item.title} (Phase: ${item.phase}-day, Due: ${item.due_date || 'N/A'})\n`;
      text += `  Description: ${item.description || ''}\n\n`;
    });

    navigator.clipboard.writeText(text).then(() => {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 3000);
    });
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-8">
      
      {/* PAGE HEADER */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
        <div>
          <h2 className="font-display font-extrabold text-3xl tracking-tight text-white">
            Executive Report Compiler
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Consolidate 360 findings, SWOT parameters, and roadmaps into a boardroom-ready deliverable.
          </p>
        </div>
        
        {report && (
          <div className="flex items-center space-x-3">
            <button
              onClick={handleCopy}
              className="px-4 py-2 text-xs font-semibold text-white rounded-xl bg-white/5 border border-white/10 hover:border-violet-500/20 flex items-center space-x-1.5 transition-all"
            >
              <Copy size={12} />
              <span>{copySuccess ? 'Copied!' : 'Copy Markdown'}</span>
            </button>
            <button
              onClick={handlePrint}
              className="px-4 py-2 text-xs font-semibold text-white rounded-xl bg-violet-600 hover:bg-violet-500 flex items-center space-x-1.5 transition-all shadow-glow"
            >
              <Printer size={12} />
              <span>Print Brief</span>
            </button>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 size={32} className="text-violet-500 animate-spin" />
        </div>
      ) : error ? (
        <div className="glass-panel rounded-2xl p-8 max-w-lg mx-auto text-center space-y-4">
          <AlertCircle size={32} className="text-red-400 mx-auto" />
          <h4 className="font-semibold text-white">Cannot Compile Report</h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            {error}
          </p>
        </div>
      ) : report ? (
        
        /* REPORT PREVIEW CARD */
        <div className="glass-panel rounded-3xl p-6 md:p-8 space-y-8 bg-[#0C1220]/60 max-w-4xl mx-auto print:bg-white print:text-black print:border-none print:shadow-none">
          
          {/* HEADER EMBLEM */}
          <div className="flex justify-between items-start pb-6 border-b border-white/5 print:border-black/10">
            <div>
              <span className="text-[10px] font-bold text-violet-400 uppercase tracking-widest block">
                Deliverable
              </span>
              <h3 className="font-display font-extrabold text-2xl text-white print:text-black">
                Syner Cortex Executive Brief
              </h3>
              <p className="text-xs text-slate-400 print:text-black mt-1">
                Workspace Project: {report.workspace_name} • Organization: {report.organization}
              </p>
            </div>
            <span className="text-right text-[10px] text-slate-500 print:text-black">
              Generated: {new Date(report.generated_at).toLocaleDateString()}
            </span>
          </div>

          {/* DIAGNOSIS SECTION */}
          <div className="space-y-6">
            <h4 className="font-display font-bold text-lg text-white border-b border-white/5 pb-2 print:text-black print:border-black/10 flex items-center space-x-2">
              <Sparkles size={16} className="text-violet-400" />
              <span>1. 360-Degree Operational Diagnosis</span>
            </h4>
            
            <div className="space-y-5">
              {report.dimensions.map((dim: any, idx: number) => (
                <div key={idx} className="space-y-1.5">
                  <h5 className="font-semibold text-sm text-white print:text-black flex justify-between">
                    <span>{dim.name}</span>
                    <span className="text-xs font-normal text-slate-400">Score: {dim.rating}/5</span>
                  </h5>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="p-3 bg-white/5 border border-white/5 rounded-xl text-slate-300 print:text-black">
                      <span className="font-semibold text-slate-400 block mb-1">Findings</span>
                      {dim.findings}
                    </div>
                    <div className="p-3 bg-violet-600/10 border border-violet-500/20 rounded-xl text-slate-200 print:text-black">
                      <span className="font-semibold text-violet-400 block mb-1">Recommendation</span>
                      {dim.recommendations}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ROADMAP SECTION */}
          <div className="space-y-6">
            <h4 className="font-display font-bold text-lg text-white border-b border-white/5 pb-2 print:text-black print:border-black/10 flex items-center space-x-2">
              <TrendingUp size={16} className="text-indigo-400" />
              <span>2. Mapped Execution Roadmap</span>
            </h4>
            
            {report.roadmap.items.length === 0 ? (
              <p className="text-xs text-slate-500">No roadmap items generated.</p>
            ) : (
              <div className="space-y-3">
                {report.roadmap.items.map((item: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-center p-3.5 bg-white/5 border border-white/5 rounded-xl text-xs print:text-black">
                    <div>
                      <h5 className="font-semibold text-white print:text-black">{item.title}</h5>
                      <p className="text-slate-400 mt-0.5 leading-relaxed">{item.description}</p>
                      <span className="text-[10px] text-slate-500 uppercase tracking-widest mt-1 block">
                        {item.dimension} • Phase: {item.phase}-day
                      </span>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      item.status === 'DONE' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                    }`}>
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      ) : (
        <div className="text-center py-10 text-slate-500 text-xs">
          Loading report...
        </div>
      )}

    </div>
  );
};
export default Reports;
