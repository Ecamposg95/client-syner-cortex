import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
// New Syner Hub Views
import { Overview } from './components/views/Overview';
import { EngagementsView } from './components/views/EngagementsView';
import { FindingsView } from './components/views/FindingsView';
import { InsightsView } from './components/views/InsightsView';
import { InitiativesView } from './components/views/InitiativesView';
import { Deliverables } from './components/views/Deliverables';
import { DecisionsView } from './components/views/DecisionsView';
import { ToolkitsPage } from './components/views/toolkit/ToolkitsPage';
import { ToolsPage } from './components/views/toolkit/ToolsPage';
import { ToolRunPage } from './components/views/toolkit/ToolRunPage';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { ToolRunReviewPage } from './components/views/toolkit/ToolRunReviewPage';
import { Changelog } from './components/views/Changelog';
import { KPIs } from './components/views/KPIs';
import { RoadmapView } from './components/views/RoadmapView';
import { AcademyView } from './components/views/AcademyView';
import { AuditorView } from './components/views/AuditorView';
import { GovernanceView } from './components/views/GovernanceView';
import { RaciMatrixView } from './components/views/RaciMatrixView';
import { SurveysView } from './components/views/SurveysView';
import { SurveyResultsView } from './components/views/SurveyResultsView';
import { PublicSurveyView } from './components/views/PublicSurveyView';
import { AdminClientsView } from './components/views/admin/AdminClientsView';
import { AdminClientDetailView } from './components/views/admin/AdminClientDetailView';
import { ChangePassword } from './pages/ChangePassword';
import { Vault } from './pages/Vault';
import { Chat } from './pages/Chat';
import { Diagnose } from './pages/Diagnose';
import { Reports } from './pages/Reports';

// Guard component for authenticated private views
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user, fetchUser, fetchOrganizations } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      // Refresh user details and organization memberships on mount
      fetchUser();
      fetchOrganizations();
    }
  }, [isAuthenticated, fetchUser, fetchOrganizations]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Force first-login password rotation before any dashboard route is shown.
  if (user?.must_change_password) {
    return <Navigate to="/change-password" replace />;
  }

  return <DashboardLayout>{children}</DashboardLayout>;
};

// Authenticated but layout-less guard (used by the forced password-change screen).
const AuthedBareRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

// Guard component for public login/signup views
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        
        {/* PUBLIC ROUTE CONFIGURATIONS */}
        {/* Anonymous survey response page — no auth, no dashboard layout */}
        <Route path="/r/:token" element={<PublicSurveyView />} />

        {/* Forced first-login password change — authenticated, no dashboard layout */}
        <Route
          path="/change-password"
          element={
            <AuthedBareRoute>
              <ChangePassword />
            </AuthedBareRoute>
          }
        />
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
        />

        {/* PRIVATE ROUTE CONFIGURATIONS (Syner Hub) */}
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Overview />
            </PrivateRoute>
          }
        />
        <Route
          path="/engagements"
          element={
            <PrivateRoute>
              <EngagementsView />
            </PrivateRoute>
          }
        />
        <Route
          path="/findings"
          element={
            <PrivateRoute>
              <FindingsView />
            </PrivateRoute>
          }
        />
        <Route
          path="/initiatives"
          element={
            <PrivateRoute>
              <InitiativesView />
            </PrivateRoute>
          }
        />
        <Route
          path="/insights"
          element={
            <PrivateRoute>
              <InsightsView />
            </PrivateRoute>
          }
        />
        <Route
          path="/deliverables"
          element={
            <PrivateRoute>
              <Deliverables />
            </PrivateRoute>
          }
        />
        <Route
          path="/decisions"
          element={
            <PrivateRoute>
              <DecisionsView />
            </PrivateRoute>
          }
        />
        <Route
          path="/toolkits"
          element={
            <PrivateRoute>
              <ToolkitsPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/toolkits/:toolkitId/tools"
          element={
            <PrivateRoute>
              <ToolsPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/tools/:toolId/run"
          element={
            <PrivateRoute>
              <ToolRunPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/roadmap"
          element={
            <PrivateRoute>
              <RoadmapView />
            </PrivateRoute>
          }
        />
        <Route
          path="/kpis"
          element={
            <PrivateRoute>
              <KPIs />
            </PrivateRoute>
          }
        />
        <Route
          path="/academy"
          element={
            <PrivateRoute>
              <AcademyView />
            </PrivateRoute>
          }
        />
        <Route
          path="/auditor"
          element={
            <PrivateRoute>
              <AuditorView />
            </PrivateRoute>
          }
        />
        <Route
          path="/bitacora"
          element={
            <PrivateRoute>
              <Changelog />
            </PrivateRoute>
          }
        />
        <Route
          path="/governance"
          element={
            <PrivateRoute>
              <GovernanceView />
            </PrivateRoute>
          }
        />
        <Route
          path="/raci"
          element={
            <PrivateRoute>
              <RaciMatrixView />
            </PrivateRoute>
          }
        />
        <Route path="/vault" element={<PrivateRoute><Vault /></PrivateRoute>} />
        <Route path="/chat" element={<PrivateRoute><Chat /></PrivateRoute>} />
        <Route path="/diagnose" element={<PrivateRoute><Diagnose /></PrivateRoute>} />
        <Route path="/reports" element={<PrivateRoute><Reports /></PrivateRoute>} />
        <Route
          path="/admin/clients"
          element={
            <PrivateRoute>
              <AdminClientsView />
            </PrivateRoute>
          }
        />
        <Route
          path="/admin/clients/:orgId"
          element={
            <PrivateRoute>
              <AdminClientDetailView />
            </PrivateRoute>
          }
        />
        <Route
          path="/surveys"
          element={
            <PrivateRoute>
              <SurveysView />
            </PrivateRoute>
          }
        />
        <Route
          path="/surveys/campaigns/:campaignId/results"
          element={
            <PrivateRoute>
              <SurveyResultsView />
            </PrivateRoute>
          }
        />
        <Route
          path="/runs/:runId/review"
          element={
            <PrivateRoute>
              <ToolRunReviewPage />
            </PrivateRoute>
          }
        />

        {/* CATCH-ALL REDIRECT ROUTING */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
        
      </Routes>
    </BrowserRouter>
  );
};
export default App;
