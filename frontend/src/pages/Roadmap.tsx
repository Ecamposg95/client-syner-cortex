import React, { useEffect, useState } from 'react';
import { useWorkspaceStore } from '../store/workspaceStore';
import { useDiagnosisStore } from '../store/diagnosisStore';
import {
  Milestone,
  CheckCircle,
  Calendar,
  User,
  Loader2,
  Clock,
  Briefcase
} from 'lucide-react';

export const Roadmap: React.FC = () => {
  const { activeWorkspace } = useWorkspaceStore();
  const { currentRoadmap, fetchLatestRoadmap, updateRoadmapItem, isLoading } = useDiagnosisStore();
  const [activePhase, setActivePhase] = useState<number>(30); // 30, 60, or 90

  useEffect(() => {
    if (activeWorkspace) {
      fetchLatestRoadmap(activeWorkspace.id);
    }
  }, [activeWorkspace, fetchLatestRoadmap]);

  if (!activeWorkspace) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
        <Milestone size={48} className="text-violet-500 mb-4 animate-pulse" />
        <h3 className="text-xl font-bold text-white mb-2">No Workspace Selected</h3>
        <p className="text-sm text-slate-400 max-w-sm">
          Please select or create a project workspace from the sidebar menu to view your roadmaps.
        </p>
      </div>
    );
  }

  // Filter tasks based on active phase tab
  const tasks = currentRoadmap?.items.filter((item) => item.phase === activePhase) || [];
  
  // Calculate completed task progress for the current phase
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((t) => t.status === 'DONE').length;
  const phaseProgress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const handleStatusChange = async (itemId: number, status: 'TODO' | 'IN_PROGRESS' | 'DONE') => {
    await updateRoadmapItem(itemId, { status });
  };

  const handleAssigneeChange = async (itemId: number, assigned_to: string) => {
    await updateRoadmapItem(itemId, { assigned_to });
  };

  const getDimensionBadgeStyles = (dimension: string) => {
    switch (dimension) {
      case 'Ventas':
        return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400';
      case 'Operaciones':
        return 'bg-violet-500/10 border-violet-500/20 text-violet-400';
      case 'Administracion':
        return 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400';
      case 'Recursos Humanos':
        return 'bg-rose-500/10 border-rose-500/20 text-rose-400';
      default:
        return 'bg-amber-500/10 border-amber-500/20 text-amber-400';
    }
  };

  return (
    <div className="space-y-8">
      
      {/* PAGE HEADER */}
      <div>
        <h2 className="font-display font-extrabold text-3xl tracking-tight text-white">
          Cortex Execution Roadmap
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Detailed action backlog mapped across 30, 60, and 90-day implementation horizons.
        </p>
      </div>

      {isLoading && !currentRoadmap ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 size={32} className="text-violet-500 animate-spin" />
        </div>
      ) : !currentRoadmap ? (
        <div className="glass-panel rounded-3xl p-10 text-center flex flex-col items-center justify-center max-w-xl mx-auto space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-violet-600/10 flex items-center justify-center text-violet-400 shadow-glow">
            <Milestone size={32} />
          </div>
          <h3 className="font-display font-bold text-xl text-white">Awaiting Execution Roadmap</h3>
          <p className="text-sm text-slate-400">
            Submit a 360-degree company diagnosis first to construct this execution backlog.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          
          {/* TABS SELECTOR */}
          <div className="flex space-x-4 border-b border-white/5 pb-2">
            {[30, 60, 90].map((phase) => (
              <button
                key={phase}
                onClick={() => setActivePhase(phase)}
                className={`pb-3 px-2 font-display text-sm font-semibold transition-all duration-300 relative ${
                  activePhase === phase ? 'text-violet-400' : 'text-slate-400 hover:text-white'
                }`}
              >
                <span>{phase === 30 ? '30 Days (Quick Wins)' : phase === 60 ? '60 Days (Integration)' : '90 Days (Strategic)'}</span>
                {activePhase === phase && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-violet-500 shadow-glow" />
                )}
              </button>
            ))}
          </div>

          {/* PROGRESS METRIC */}
          <div className="glass-panel rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest block">
                Phase Execution Status
              </span>
              <h4 className="text-sm font-bold text-white">
                {completedTasks} of {totalTasks} actions completed in this horizon
              </h4>
            </div>
            <div className="w-full md:w-72 space-y-1.5">
              <div className="flex justify-between text-xs text-slate-400">
                <span>Progress</span>
                <span>{phaseProgress}%</span>
              </div>
              <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-gradient-to-r from-violet-600 to-indigo-500 h-full transition-all duration-500"
                  style={{ width: `${phaseProgress}%` }}
                />
              </div>
            </div>
          </div>

          {/* ACTIONS LIST */}
          <div className="space-y-4">
            {tasks.length === 0 ? (
              <div className="glass-panel rounded-2xl p-8 text-center text-slate-500 text-xs">
                No active tasks found for this horizon.
              </div>
            ) : (
              tasks.map((task) => (
                <div key={task.id} className="glass-panel rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all">
                  
                  {/* LEFT DETAILS */}
                  <div className="space-y-2.5 min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`px-2 py-0.5 rounded border text-[9px] font-bold uppercase tracking-wider ${getDimensionBadgeStyles(task.dimension)}`}>
                        {task.dimension}
                      </span>
                      {task.due_date && (
                        <span className="flex items-center space-x-1 text-[10px] text-slate-500">
                          <Calendar size={10} />
                          <span>Due: {new Date(task.due_date).toLocaleDateString()}</span>
                        </span>
                      )}
                    </div>
                    <div className="space-y-1">
                      <h4 className="font-semibold text-white truncate pr-4">
                        {task.title}
                      </h4>
                      <p className="text-xs text-slate-400 leading-relaxed max-w-2xl">
                        {task.description}
                      </p>
                    </div>
                  </div>

                  {/* RIGHT CONTROLS */}
                  <div className="flex flex-wrap items-center gap-4 flex-shrink-0">
                    {/* Assigned To Input */}
                    <div className="flex items-center space-x-2 bg-white/5 border border-white/5 rounded-lg px-2.5 py-1.5">
                      <User size={12} className="text-slate-500" />
                      <input
                        type="text"
                        placeholder="Assign team member..."
                        value={task.assigned_to || ''}
                        onChange={(e) => handleAssigneeChange(task.id, e.target.value)}
                        className="bg-transparent text-xs text-slate-300 focus:outline-none w-28 placeholder-slate-600"
                      />
                    </div>

                    {/* Status Dropdown */}
                    <div className="relative">
                      <select
                        value={task.status}
                        onChange={(e) => handleStatusChange(task.id, e.target.value as any)}
                        className={`text-xs font-semibold px-3 py-2 rounded-lg border focus:outline-none appearance-none cursor-pointer pr-8 ${
                          task.status === 'DONE'
                            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                            : task.status === 'IN_PROGRESS'
                            ? 'bg-violet-500/10 border-violet-500/20 text-violet-400'
                            : 'bg-[#151D30] border-white/10 text-slate-300'
                        }`}
                      >
                        <option value="TODO" className="bg-[#111827] text-white">TODO</option>
                        <option value="IN_PROGRESS" className="bg-[#111827] text-white">IN PROGRESS</option>
                        <option value="DONE" className="bg-[#111827] text-white">DONE</option>
                      </select>
                      {/* Custom dropdown indicator chevron */}
                      <div className="absolute inset-y-0 right-0 flex items-center pr-2.5 pointer-events-none text-slate-500">
                        <Clock size={10} />
                      </div>
                    </div>
                  </div>

                </div>
              ))
            )}
          </div>

        </div>
      )}

    </div>
  );
};
export default Roadmap;
