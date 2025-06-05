// frontend/src/App.jsx
import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import PrivateRoute from "./components/PrivateRoute";
import Login    from "./components/Login";
import Signup   from "./components/Signup";
import Dashboard from "./components/Dashboard";
import AuditLogs from "./components/AuditLogs";
import "./App.css";

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login"     element={<Login />} />
          <Route path="/signup"    element={<Signup />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/audit"
            element={
              <PrivateRoute>
                <AuditLogs />
              </PrivateRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}
