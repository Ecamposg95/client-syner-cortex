import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useWorkspaceStore } from '../../store/workspaceStore';
import { Badge } from '../ui/Badge';
import { ProgressBar } from '../ui/ProgressBar';
import { project } from '../../data/mockData';
import {
  LayoutGrid,
  TrendingUp,
  Calendar,
  FolderClosed,
  Clock,
  ChevronDown,
  LogOut,
  Building,
  Menu,
  X,
  Plus,
  Loader2,
  Bell,
  Settings,
  ChevronRight,
} from 'lucide-react';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const { user, organizations, currentOrgRelation, logout, selectOrganization } = useAuthStore();
  const { workspaces, activeWorkspace, selectWorkspace, createWorkspace, fetchWorkspaces, isLoading } = useWorkspaceStore();

  const navigate = useNavigate();

  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isOrgDropdownOpen, setIsOrgDropdownOpen] = useState(false);
  const [isWorkspaceDropdownOpen, setIsWorkspaceDropdownOpen] = useState(false);
  const [showNewWorkspaceModal, setShowNewWorkspaceModal] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [newWorkspaceDesc, setNewWorkspaceDesc] = useState('');
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);

  useEffect(() => {
    if (currentOrgRelation) {
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
    { name: 'Overview',     path: '/dashboard',   icon: LayoutGrid },
    { name: 'KPIs',         path: '/kpis',        icon: TrendingUp },
    { name: 'Roadmap',      path: '/roadmap',     icon: Calendar },
    { name: 'Entregables',  path: '/entregables', icon: FolderClosed },
    { name: 'Bitácora',     path: '/bitacora',    icon: Clock },
  ];

  return (
    <div className="min-h-screen flex font-sans" style={{ background: 'var(--bg)', color: 'var(--ink)' }}>

      {/* ── MOBILE TOP BAR ── */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-14 flex items-center justify-between px-4 z-40"
           style={{ background: 'var(--surface)', borderBottom: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-white text-xs"
               style={{ background: 'var(--accent)' }}>
            SH
          </div>
          <span className="font-bold text-base tracking-wide" style={{ color: 'var(--ink)' }}>
            Syner Hub
          </span>
        </div>
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="p-2 rounded-lg transition-colors"
          style={{ color: 'var(--muted)' }}
        >
          {isSidebarOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* ── SIDEBAR (200px) ── */}
      <aside
        className={`fixed lg:sticky top-0 left-0 bottom-0 z-50 w-[220px] flex flex-col transition-transform duration-300 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0 lg:h-screen pt-14 lg:pt-0`}
        style={{
          background: 'var(--surface-2)',
          borderRight: '1px solid var(--border)',
        }}
      >
        {/* Logo */}
        <div className="p-5 flex items-center gap-3" style={{ borderBottom: '1px solid var(--border)' }}>
          <div className="w-9 h-9 rounded-lg flex items-center justify-center font-extrabold text-white text-sm"
               style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}>
            SH
          </div>
          <div>
            <h1 className="font-extrabold text-base tracking-wide" style={{ color: 'var(--ink)' }}>
              Syner Hub
            </h1>
            <span className="font-mono text-[9px] uppercase tracking-widest" style={{ color: 'var(--muted-2)' }}>
              Transformación
            </span>
          </div>
        </div>

        {/* Organization Selector */}
        <div className="px-4 py-3 relative" style={{ borderBottom: '1px solid var(--border)' }}>
          <label className="font-mono text-[9px] uppercase tracking-widest block mb-1.5 px-1"
                 style={{ color: 'var(--muted-2)' }}>
            Organización
          </label>
          <button
            onClick={() => { setIsOrgDropdownOpen(!isOrgDropdownOpen); setIsWorkspaceDropdownOpen(false); }}
            className="w-full flex items-center justify-between p-2 rounded-lg text-left text-sm font-medium transition-all duration-200"
            style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              color: 'var(--ink-2)',
            }}
          >
            <div className="flex items-center gap-2 truncate">
              <Building size={14} style={{ color: 'var(--accent)' }} />
              <span className="truncate">{currentOrgRelation?.organization?.name || 'Cargando...'}</span>
            </div>
            <ChevronDown size={14} className={`transition-transform ${isOrgDropdownOpen ? 'rotate-180' : ''}`} style={{ color: 'var(--muted-2)' }} />
          </button>

          {isOrgDropdownOpen && (
            <div className="absolute top-full left-4 right-4 rounded-lg shadow-float py-1 z-30 max-h-48 overflow-y-auto"
                 style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
              {organizations.map((relation) => (
                <button
                  key={relation.organization_id}
                  onClick={() => { selectOrganization(relation.organization_id); setIsOrgDropdownOpen(false); }}
                  className="w-full text-left px-3 py-2 text-sm transition-colors hover:bg-[var(--accent-tint)]"
                  style={{
                    color: relation.organization_id === currentOrgRelation?.organization_id ? 'var(--accent-strong)' : 'var(--ink-2)',
                    fontWeight: relation.organization_id === currentOrgRelation?.organization_id ? 600 : 400,
                  }}
                >
                  {relation.organization.name}
                  <span className="block font-mono text-[9px] uppercase" style={{ color: 'var(--muted-2)' }}>
                    {relation.role}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Workspace Selector */}
        <div className="px-4 py-3 relative" style={{ borderBottom: '1px solid var(--border)' }}>
          <label className="font-mono text-[9px] uppercase tracking-widest block mb-1.5 px-1"
                 style={{ color: 'var(--muted-2)' }}>
            Proyecto
          </label>
          <button
            onClick={() => { setIsWorkspaceDropdownOpen(!isWorkspaceDropdownOpen); setIsOrgDropdownOpen(false); }}
            className="w-full flex items-center justify-between p-2 rounded-lg text-left text-sm font-medium transition-all duration-200"
            style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              color: 'var(--ink-2)',
            }}
          >
            <div className="flex items-center gap-2 truncate">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: 'var(--accent)' }} />
              <span className="truncate">{activeWorkspace ? activeWorkspace.name : 'Sin proyectos'}</span>
            </div>
            <ChevronDown size={14} className={`transition-transform ${isWorkspaceDropdownOpen ? 'rotate-180' : ''}`} style={{ color: 'var(--muted-2)' }} />
          </button>

          {isWorkspaceDropdownOpen && (
            <div className="absolute top-full left-4 right-4 rounded-lg shadow-float py-1 z-30 max-h-48 overflow-y-auto"
                 style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
              {workspaces.map((w) => (
                <button
                  key={w.id}
                  onClick={() => { selectWorkspace(w.id); setIsWorkspaceDropdownOpen(false); }}
                  className="w-full text-left px-3 py-2 text-sm transition-colors hover:bg-[var(--accent-tint)]"
                  style={{
                    color: activeWorkspace && w.id === activeWorkspace.id ? 'var(--accent-strong)' : 'var(--ink-2)',
                    fontWeight: activeWorkspace && w.id === activeWorkspace.id ? 600 : 400,
                  }}
                >
                  {w.name}
                </button>
              ))}
              <div style={{ borderTop: '1px solid var(--border)' }} className="mt-1 pt-1">
                <button
                  onClick={() => { setIsWorkspaceDropdownOpen(false); setShowNewWorkspaceModal(true); }}
                  className="w-full text-left px-3 py-2 text-xs flex items-center gap-1 transition-colors hover:bg-[var(--accent-tint)]"
                  style={{ color: 'var(--muted)' }}
                >
                  <Plus size={12} />
                  <span>Crear proyecto</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setIsSidebarOpen(false)}
                className={({ isActive }) =>
                  `sidebar-tab ${isActive ? 'sidebar-tab--active' : ''}`
                }
              >
                <Icon size={18} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Footer User */}
        <div className="p-4 flex items-center justify-between" style={{ borderTop: '1px solid var(--border)', background: 'var(--surface)' }}>
          <div className="flex items-center gap-2.5 truncate">
            <div className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs text-white"
                 style={{ background: 'linear-gradient(135deg, var(--accent-strong), var(--accent))' }}>
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold truncate" style={{ color: 'var(--ink)' }}>
                {user?.full_name || 'Cargando...'}
              </p>
              <p className="font-mono text-[9px] truncate" style={{ color: 'var(--muted-2)' }}>
                {user?.email || ''}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            title="Cerrar sesión"
            className="p-1.5 rounded-lg transition-colors"
            style={{ color: 'var(--muted)' }}
            onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--neg)')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--muted)')}
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* ── MAIN CONTENT ── */}
      <main className="flex-1 flex flex-col min-w-0 pt-14 lg:pt-0 overflow-y-auto">
        {/* Header Bar */}
        <header className="hidden lg:flex items-center justify-between px-8 py-4"
                style={{ borderBottom: '1px solid var(--border)', background: 'var(--surface)' }}>
          <div>
            <div className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--muted-2)' }}>
              <span>Workspace</span>
              <ChevronRight size={12} />
              <span style={{ color: 'var(--muted)' }}>{project.client}</span>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <h2 className="font-extrabold text-xl" style={{ color: 'var(--ink)' }}>
                {project.name}
              </h2>
              <span className="font-mono text-xs" style={{ color: 'var(--muted-2)' }}>· {project.quarter}</span>
              <Badge variant="active" label={project.status} />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex flex-col items-end mr-2">
              <span className="font-mono text-[9px] uppercase tracking-widest" style={{ color: 'var(--muted-2)' }}>
                Progreso global
              </span>
              <span className="font-bold text-sm" style={{ color: 'var(--accent-strong)' }}>
                {project.progress}%
              </span>
            </div>
            <div className="w-32">
              <ProgressBar percent={project.progress} />
            </div>
            <button className="p-2 rounded-lg transition-colors" style={{ color: 'var(--muted)' }}>
              <Bell size={18} />
            </button>
            <button className="p-2 rounded-lg transition-colors" style={{ color: 'var(--muted)' }}>
              <Settings size={18} />
            </button>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </div>
      </main>

      {/* ── NEW WORKSPACE MODAL ── */}
      {showNewWorkspaceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.4)' }}>
          <div className="w-full max-w-md rounded-xl p-6 shadow-float relative"
               style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
            <button
              onClick={() => setShowNewWorkspaceModal(false)}
              className="absolute top-4 right-4 transition-colors"
              style={{ color: 'var(--muted)' }}
            >
              <X size={20} />
            </button>
            <h3 className="font-bold text-lg mb-4" style={{ color: 'var(--ink)' }}>
              Crear nuevo proyecto
            </h3>
            <form onSubmit={handleCreateWorkspace} className="space-y-4">
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                  Nombre del proyecto
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ej. Transformación Q4 2026"
                  value={newWorkspaceName}
                  onChange={(e) => setNewWorkspaceName(e.target.value)}
                  className="w-full p-2.5 rounded-lg text-sm transition-all outline-none"
                  style={{
                    background: 'var(--surface-2)',
                    border: '1px solid var(--border)',
                    color: 'var(--ink)',
                  }}
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                  Descripción (opcional)
                </label>
                <textarea
                  placeholder="Propósito del proyecto..."
                  value={newWorkspaceDesc}
                  onChange={(e) => setNewWorkspaceDesc(e.target.value)}
                  rows={3}
                  className="w-full p-2.5 rounded-lg text-sm resize-none transition-all outline-none"
                  style={{
                    background: 'var(--surface-2)',
                    border: '1px solid var(--border)',
                    color: 'var(--ink)',
                  }}
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewWorkspaceModal(false)}
                  className="px-4 py-2 text-xs font-medium rounded-lg transition-colors"
                  style={{ color: 'var(--muted)', background: 'var(--surface-2)' }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isCreatingWorkspace}
                  className="px-4 py-2 text-xs font-semibold text-white rounded-lg flex items-center gap-1 disabled:opacity-50"
                  style={{ background: 'var(--accent)' }}
                >
                  {isCreatingWorkspace ? (
                    <>
                      <Loader2 size={12} className="animate-spin" />
                      <span>Creando...</span>
                    </>
                  ) : (
                    <span>Crear</span>
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
