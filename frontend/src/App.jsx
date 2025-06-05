// frontend/src/App.jsx
import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import PrivateRoute from "./components/PrivateRoute";

import Login           from "./components/Login";
import Signup          from "./components/Signup";
import Dashboard       from "./components/Dashboard";
import AuditLogs       from "./components/AuditLogs";
import UploadDocument  from "./components/UploadDocument";
import SearchDocuments from "./components/SearchDocuments";
import DocumentsList   from "./components/DocumentsList";

import "./App.css";

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* --- Auth --- */}
          <Route path="/login"  element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* --- Dashboard (any authenticated user) --- */}
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />

          {/* --- Upload (admin only) --- */}
          <Route
            path="/upload"
            element={
              <PrivateRoute requireAdmin>
                <UploadDocument />
              </PrivateRoute>
            }
          />

          {/* --- Search & List (all authenticated users) --- */}
          <Route
            path="/search"
            element={
              <PrivateRoute>
                <SearchDocuments />
              </PrivateRoute>
            }
          />
          <Route
            path="/documents"
            element={
              <PrivateRoute>
                <DocumentsList />
              </PrivateRoute>
            }
          />

          {/* --- Audit (admin only) --- */}
          <Route
            path="/audit"
            element={
              <PrivateRoute requireAdmin>
                <AuditLogs />
              </PrivateRoute>
            }
          />

          {/* --- Home redirects to Dashboard --- */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}
