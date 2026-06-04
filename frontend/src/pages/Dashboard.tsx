import React, { useEffect } from 'react';
import { useWorkspaceStore as wsStore } from '../store/workspaceStore';
import { useDiagnosisStore as diagStore } from '../store/diagnosisStore';
import {
  TrendingUp,
  AlertCircle,
  Award,
  Milestone,
  CheckCircle,
  Star,
  Activity,
  ArrowRight,
  TrendingDown
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const { activeWorkspace } = wsStore();
  const { currentDiagnosis, currentRoadmap, fetchLatestDiagnosis, fetchLatestRoadmap, isLoading } = diagStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (activeWorkspace) {
      fetchLatestDiagnosis(activeWorkspace.id);
      fetchLatestRoadmap(activeWorkspace.id);
    }
  }, [activeWorkspace, fetchLatestDiagnosis, fetchLatestRoadmap]);

  if (!activeWorkspace) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
        <Activity size={48} className="text-violet-500 animate-pulse mb-4" />
        <h3 className="text-xl font-bold text-white mb-2">No Workspace Selected</h3>
        <p className="text-sm text-slate-400 max-w-sm">
          Please select or create a project workspace from the sidebar menu to view the boardroom executive dashboard.
        </p>
      </div>
    );
  }

  // Calculate stats from roadmap
  const totalTasks = currentRoadmap?.items.length || 0;
  const completedTasks = currentRoadmap?.items.filter(i => i.status === 'DONE').length || 0;
  const progressPercent = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  // Calculate average rating
  const dimensionsCount = currentDiagnosis?.dimensions.length || 0;
  const totalRating = currentDiagnosis?.dimensions.reduce((acc, dim) => acc + dim.rating, 0) || 0;
  const averageRating = dimensionsCount > 0 ? (totalRating / dimensionsCount).toFixed(1) : 'N/A';

  return (
    <div className="space-y-8">
      
      {/* PAGE HEADER */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
        <div>
          <h2 className="font-display font-extrabold text-3xl tracking-tight text-white">
            Boardroom Executive Overview
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Real-time intelligence and execution control panel for workspace: <span className="text-violet-400 font-semibold">{activeWorkspace.name}</span>
          </p>
        </div>
        {!currentDiagnosis && (
          <button
            onClick={() => navigate('/diagnose')}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-sm font-semibold text-white shadow-glow flex items-center space-x-1.5 transition-all duration-300"
          >
            <span>Run 360 Diagnosis</span>
            <ArrowRight size={16} />
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-violet-500" />
        </div>
      ) : currentDiagnosis ? (
        <>
          {/* TOP METRIC CARDS */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <div className="glass-panel rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-violet-500/5 rounded-full blur-xl" />
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-xl bg-violet-600/10 flex items-center justify-center text-violet-400">
                  <Award size={24} />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">
                    Consulting Score
                  </p>
                  <div className="flex items-baseline space-x-2 mt-1">
                    <span className="text-3xl font-extrabold text-white font-display">
                      {averageRating}
                    </span>
                    <span className="text-xs text-slate-500">/ 5.0</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="glass-panel rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-xl" />
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-xl bg-indigo-600/10 flex items-center justify-center text-indigo-400">
                  <Milestone size={24} />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">
                    Roadmap Completion
                  </p>
                  <div className="flex items-baseline space-x-2 mt-1">
                    <span className="text-3xl font-extrabold text-white font-display">
                      {progressPercent}%
                    </span>
                    <span className="text-xs text-slate-500">
                      ({completedTasks}/{totalTasks} Tasks)
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="glass-panel rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl" />
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-600/10 flex items-center justify-center text-emerald-400">
                  <CheckCircle size={24} />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">
                    Diagnosis Status
                  </p>
                  <div className="flex items-baseline space-x-2 mt-1">
                    <span className="text-lg font-bold text-emerald-400 uppercase tracking-wider">
                      Active
                    </span>
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* MAIN GRID */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* DIMENSION MATRICES */}
            <div className="lg:col-span-2 space-y-6">
              <h3 className="font-display font-bold text-xl text-white">
                Operational Dimension Health
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {currentDiagnosis.dimensions.map((dim) => (
                  <div key={dim.id} className="glass-panel glass-panel-hover rounded-2xl p-5 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start mb-3">
                        <h4 className="font-display font-semibold text-lg text-white">
                          {dim.name}
                        </h4>
                        <div className="flex items-center space-x-0.5">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              size={14}
                              className={i < dim.rating ? 'text-amber-400 fill-amber-400' : 'text-slate-700'}
                            />
                          ))}
                        </div>
                      </div>
                      
                      <p className="text-xs text-slate-400 line-clamp-3 mb-4">
                        {dim.findings}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-white/5 flex justify-between items-center text-xs">
                      <span className="text-slate-500">Action Recommendations</span>
                      <button
                        onClick={() => navigate('/diagnose')}
                        className="text-violet-400 hover:text-violet-300 font-medium flex items-center space-x-1"
                      >
                        <span>View Details</span>
                        <ArrowRight size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* QUICK ACTIONS & INSIGHT SUMMARY */}
            <div className="space-y-6">
              <h3 className="font-display font-bold text-xl text-white">
                Strategic Quick Wins
              </h3>

              <div className="glass-panel rounded-2xl p-6 space-y-4">
                <div className="p-4 bg-violet-600/10 border border-violet-500/20 rounded-xl space-y-1">
                  <div className="flex items-center space-x-2 text-violet-400">
                    <TrendingUp size={16} />
                    <span className="text-xs font-semibold uppercase tracking-wider">Top Priority Win</span>
                  </div>
                  <h4 className="text-sm font-bold text-white mt-1">Configure CRM Pipeline</h4>
                  <p className="text-xs text-slate-400 mt-1">
                    Centralize leads in Pipedrive/Hubspot to eliminate leaking opportunities.
                  </p>
                </div>

                <div className="p-4 bg-indigo-600/10 border border-indigo-500/20 rounded-xl space-y-1">
                  <div className="flex items-center space-x-2 text-indigo-400">
                    <Activity size={16} />
                    <span className="text-xs font-semibold uppercase tracking-wider">Operational Win</span>
                  </div>
                  <h4 className="text-sm font-bold text-white mt-1">Document Standard Operating Procedures</h4>
                  <p className="text-xs text-slate-400 mt-1">
                    Write simple SOP files for the top 3 high-friction recurring tasks.
                  </p>
                </div>

                <div className="pt-2 text-center">
                  <button
                    onClick={() => navigate('/roadmap')}
                    className="text-xs font-semibold text-slate-400 hover:text-white flex items-center justify-center space-x-1 mx-auto"
                  >
                    <span>Open Full 30/60/90 Roadmap</span>
                    <ArrowRight size={12} />
                  </button>
                </div>
              </div>
            </div>

          </div>
        </>
      ) : (
        /* NO DIAGNOSIS BANNER */
        <div className="glass-panel rounded-3xl p-10 text-center flex flex-col items-center justify-center max-w-xl mx-auto space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-violet-600/10 flex items-center justify-center text-violet-400 shadow-glow">
            <Activity size={32} />
          </div>
          <h3 className="font-display font-extrabold text-2xl text-white">
            Awaiting Corporate Diagnosis
          </h3>
          <p className="text-sm text-slate-400">
            To generate strategic KPIs, SWOT factors, and action plans, you need to execute a 360-degree company diagnosis.
          </p>
          <button
            onClick={() => navigate('/diagnose')}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 font-semibold text-white text-sm shadow-glow flex items-center space-x-2 transition-all duration-300"
          >
            <span>Start Business Diagnosis</span>
            <ArrowRight size={16} />
          </button>
        </div>
      )}

    </div>
  );
};
export default Dashboard;
