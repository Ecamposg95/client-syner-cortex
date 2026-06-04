import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useWorkspaceStore } from '../../store/workspaceStore';
import {
  LayoutDashboard,
  FolderKanban,
  MessageSquare,
  Activity,
  Milestone,
  FileText,
  ChevronDown,
  LogOut,
  Building,
  Menu,
  X,
  Plus,
  Loader2
} from 'lucide-react';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const { user, organizations, currentOrgRelation, logout, selectOrganization } = useAuthStore();
  const { workspaces, activeWorkspace, selectWorkspace, createWorkspace, fetchWorkspaces, isLoading } = useWorkspaceStore();
  
  const navigate = useNavigate();
  const location = useLocation();
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isOrgDropdownOpen, setIsOrgDropdownOpen] = useState(false);
  const [isWorkspaceDropdownOpen, setIsWorkspaceDropdownOpen] = useState(false);
  const [showNewWorkspaceModal, setShowNewWorkspaceModal] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [newWorkspaceDesc, setNewWorkspaceDesc] = useState('');
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);

  useEffect(() => {
    if (currentOrgRelation) {
      // Re-fetch workspaces when organization changes
      fetchWorkspaces();
    }
  }, [currentOrgRelation, fetchWorkspaces]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWorkspaceName.trim()) return;

    setIsCreatingWorkspace(true);
    const success = await createWorkspace(newWorkspaceName, newWorkspaceDesc);
    setIsCreatingWorkspace(false);
    
    if (success) {
      setNewWorkspaceName('');
      setNewWorkspaceDesc('');
      setShowNewWorkspaceModal(false);
    }
  };

  const navItems = [
    { name: 'Boardroom', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Cortex Vault', path: '/vault', icon: FolderKanban },
    { name: 'Cortex Chat', path: '/chat', icon: MessageSquare },
    { name: 'Cortex Diagnose', path: '/diagnose', icon: Activity },
    { name: 'Cortex Roadmap', path: '/roadmap', icon: Milestone },
    { name: 'Executive Reports', path: '/reports', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-[#080B11] text-[#F8FAFC] flex font-sans">
      
      {/* BACKGROUND GLOW BLOBS */}
      <div className="bg-blob-violet top-10 left-10" />
      <div className="bg-blob-indigo bottom-10 right-10" />

      {/* MOBILE HEADER BAR */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-[#0E1524]/90 backdrop-blur-md border-b border-white/5 flex items-center justify-between px-4 z-40">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-glow">
            SC
          </div>
          <span className="font-display font-bold text-lg tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
            SYNER CORTEX
          </span>
        </div>
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/5"
        >
          {isSidebarOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* COLLAPSIBLE SIDEBAR */}
      <aside
        className={`fixed lg:sticky top-0 left-0 bottom-0 z-50 w-72 bg-[#0C1220]/95 lg:bg-[#0C1220]/60 backdrop-blur-xl border-r border-white/5 flex flex-col transition-transform duration-300 transform ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0 lg:h-screen pt-16 lg:pt-0`}
      >
        {/* LOGO SECTION */}
        <div className="p-6 border-b border-white/5 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 via-indigo-500 to-pink-500 flex items-center justify-center font-bold text-white shadow-glow">
            SC
          </div>
          <div>
            <h1 className="font-display font-extrabold text-xl tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-300">
              Syner Cortex
            </h1>
            <span className="text-[10px] text-violet-400 font-medium tracking-widest uppercase">
              AI OS Consulting
            </span>
          </div>
        </div>

        {/* ORGANIZATION SELECTOR */}
        <div className="p-4 border-b border-white/5 relative">
          <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest block mb-2 px-1">
            Active Tenant
          </label>
          <button
            onClick={() => {
              setIsOrgDropdownOpen(!isOrgDropdownOpen);
              setIsWorkspaceDropdownOpen(false);
            }}
            className="w-full flex items-center justify-between p-2.5 rounded-lg bg-white/5 border border-white/5 hover:border-violet-500/30 text-left transition-all duration-200"
          >
            <div className="flex items-center space-x-2.5 truncate">
              <Building size={16} className="text-violet-400 flex-shrink-0" />
              <span className="font-medium text-sm text-slate-200 truncate">
                {currentOrgRelation?.organization?.name || 'Loading organization...'}
              </span>
            </div>
            <ChevronDown size={16} className={`text-slate-400 transition-transform ${isOrgDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isOrgDropdownOpen && (
            <div className="absolute top-[calc(100%-8px)] left-4 right-4 bg-[#141C2E] border border-white/10 rounded-lg shadow-xl py-1 z-30 max-h-48 overflow-y-auto">
              {organizations.map((relation) => (
                <button
                  key={relation.organization_id}
                  onClick={() => {
                    selectOrganization(relation.organization_id);
                    setIsOrgDropdownOpen(false);
                  }}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-white/5 transition-colors ${
                    relation.organization_id === currentOrgRelation?.organization_id ? 'text-violet-400 font-semibold' : 'text-slate-300'
                  }`}
                >
                  {relation.organization.name}
                  <span className="block text-[10px] text-slate-500 font-normal">
                    Role: {relation.role}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* WORKSPACE SELECTOR */}
        <div className="p-4 border-b border-white/5 relative">
          <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest block mb-2 px-1">
            Workspace Project
          </label>
          <button
            onClick={() => {
              setIsWorkspaceDropdownOpen(!isWorkspaceDropdownOpen);
              setIsOrgDropdownOpen(false);
            }}
            className="w-full flex items-center justify-between p-2.5 rounded-lg bg-white/5 border border-white/5 hover:border-indigo-500/30 text-left transition-all duration-200"
          >
            <div className="flex items-center space-x-2.5 truncate">
              <span className="w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0" />
              <span className="font-medium text-sm text-slate-200 truncate">
                {activeWorkspace ? activeWorkspace.name : 'No Workspaces Found'}
              </span>
            </div>
            <ChevronDown size={16} className={`text-slate-400 transition-transform ${isWorkspaceDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isWorkspaceDropdownOpen && (
            <div className="absolute top-[calc(100%-8px)] left-4 right-4 bg-[#141C2E] border border-white/10 rounded-lg shadow-xl py-1 z-30 max-h-48 overflow-y-auto">
              {workspaces.map((w) => (
                <button
                  key={w.id}
                  onClick={() => {
                    selectWorkspace(w.id);
                    setIsWorkspaceDropdownOpen(false);
                  }}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-white/5 transition-colors ${
                    activeWorkspace && w.id === activeWorkspace.id ? 'text-indigo-400 font-semibold' : 'text-slate-300'
                  }`}
                >
                  {w.name}
                </button>
              ))}
              <div className="border-t border-white/5 mt-1 pt-1">
                <button
                  onClick={() => {
                    setIsWorkspaceDropdownOpen(false);
                    setShowNewWorkspaceModal(true);
                  }}
                  className="w-full text-left px-4 py-2 text-xs text-slate-400 hover:text-white hover:bg-white/5 flex items-center space-x-1"
                >
                  <Plus size={12} />
                  <span>Create Workspace</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* NAVIGATION LINKS */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                    isActive
                      ? 'bg-gradient-to-r from-violet-600/20 to-indigo-500/10 text-white border-l-2 border-violet-500 shadow-glow'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                  }`
                }
              >
                <Icon size={18} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* FOOTER USER PROFILE */}
        <div className="p-4 border-t border-white/5 bg-[#0A0E1A]/40 flex items-center justify-between">
          <div className="flex items-center space-x-3 truncate">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-violet-500 to-indigo-500 flex items-center justify-center font-bold text-xs text-white">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold text-white truncate">
                {user?.full_name || 'Loading user...'}
              </p>
              <p className="text-[10px] text-slate-500 truncate">
                {user?.email || ''}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="Log Out"
            className="p-1.5 text-slate-400 hover:text-red-400 rounded-lg hover:bg-white/5 transition-colors"
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* MAIN CONTAINER CONTENT */}
      <main className="flex-1 flex flex-col min-w-0 pt-16 lg:pt-0 overflow-y-auto">
        <div className="flex-1 p-6 md:p-10 max-w-7xl w-full mx-auto">
          {children}
        </div>
      </main>

      {/* NEW WORKSPACE MODAL */}
      {showNewWorkspaceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-[#111827] border border-white/10 rounded-2xl p-6 shadow-2xl relative">
            <button
              onClick={() => setShowNewWorkspaceModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X size={20} />
            </button>
            <h3 className="font-display font-bold text-xl text-white mb-4">
              Create New Workspace
            </h3>
            <form onSubmit={handleCreateWorkspace} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">
                  Workspace Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Q3 Sales Consulting"
                  value={newWorkspaceName}
                  onChange={(e) => setNewWorkspaceName(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">
                  Description (Optional)
                </label>
                <textarea
                  placeholder="Purpose of this workspace..."
                  value={newWorkspaceDesc}
                  onChange={(e) => setNewWorkspaceDesc(e.target.value)}
                  rows={3}
                  className="w-full p-2.5 rounded-lg bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 text-sm resize-none"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewWorkspaceModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white rounded-lg bg-white/5 hover:bg-white/10"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreatingWorkspace}
                  className="px-4 py-2 text-xs font-semibold text-white rounded-lg bg-violet-600 hover:bg-violet-500 flex items-center space-x-1 disabled:opacity-55"
                >
                  {isCreatingWorkspace ? (
                    <>
                      <Loader2 size={12} className="animate-spin" />
                      <span>Creating...</span>
                    </>
                  ) : (
                    <span>Create</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
