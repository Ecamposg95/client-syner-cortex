import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
// New Syner Hub Views
import { Overview } from './components/views/Overview';
import { KPIs } from './components/views/KPIs';
import { RoadmapView } from './components/views/RoadmapView';
import { Deliverables } from './components/views/Deliverables';
import { Changelog } from './components/views/Changelog';
import { DashboardLayout } from './components/layout/DashboardLayout';

// Guard component for authenticated private views
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, fetchUser, fetchOrganizations } = useAuthStore();

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

  return <DashboardLayout>{children}</DashboardLayout>;
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
          path="/kpis"
          element={
            <PrivateRoute>
              <KPIs />
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
          path="/entregables"
          element={
            <PrivateRoute>
              <Deliverables />
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

        {/* CATCH-ALL REDIRECT ROUTING */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
        
      </Routes>
    </BrowserRouter>
  );
};
export default App;
