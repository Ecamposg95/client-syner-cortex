import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { Vault } from './pages/Vault';
import { Chat } from './pages/Chat';
import { Diagnose } from './pages/Diagnose';
import { Roadmap } from './pages/Roadmap';
import { Reports } from './pages/Reports';
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

        {/* PRIVATE ROUTE CONFIGURATIONS */}
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          }
        />
        <Route
          path="/vault"
          element={
            <PrivateRoute>
              <Vault />
            </PrivateRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <PrivateRoute>
              <Chat />
            </PrivateRoute>
          }
        />
        <Route
          path="/diagnose"
          element={
            <PrivateRoute>
              <Diagnose />
            </PrivateRoute>
          }
        />
        <Route
          path="/roadmap"
          element={
            <PrivateRoute>
              <Roadmap />
            </PrivateRoute>
          }
        />
        <Route
          path="/reports"
          element={
            <PrivateRoute>
              <Reports />
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
