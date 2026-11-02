/**
 * App.jsx
 * Root application component.
 * Defines all routes and wraps the app with AuthProvider.
 *
 * Route structure:
 *   /              → redirect to /dashboard (or /login if not auth)
 *   /login         → <Login />  (public)
 *   /signup        → <Signup /> (public)
 *   /dashboard     → <Dashboard /> (protected – requires auth)
 *
 * The <ChatBot /> widget is mounted here (inside AuthProvider) so it is
 * globally available on every page without re-mounting on navigation.
 * It renders only when the user is authenticated.
 */

import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';

import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import ChatBot from './components/ChatBot';   // Floating wellness chatbot

/**
 * ProtectedRoute – redirects to /login if the user is not authenticated.
 */
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

/**
 * PublicRoute – redirects to /dashboard if the user IS already authenticated.
 * Prevents logged-in users from seeing the login/signup pages.
 */
function PublicRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : children;
}

/**
 * AppRoutes – all page routes + the globally mounted ChatBot widget.
 * ChatBot uses useAuth() internally and only renders when isAuthenticated.
 */
function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/signup" element={<PublicRoute><Signup /></PublicRoute>} />

        {/* Protected route */}
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />

        {/* Default: root → dashboard (will bounce to /login if not authed) */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        {/* Catch-all: any unknown path → dashboard root */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>

      {/*
        Floating chatbot widget – rendered outside <Routes> so it persists
        across page navigations without unmounting.
        Only visible when the user is logged in.
      */}
      {isAuthenticated && <ChatBot />}
    </>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}
