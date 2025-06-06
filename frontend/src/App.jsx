/**
 * Componente principal de la aplicación Firebase Demo
 * 
 * Este componente configura el enrutamiento principal, la autenticación global,
 * y la estructura base de la aplicación. Incluye rutas protegidas,
 * control de acceso por roles, y configuración de navegación.
 * 
 * Características principales:
 * - Enrutamiento con React Router v6+
 * - Autenticación global con Context API
 * - Rutas protegidas con verificación de roles
 * - Lazy loading de componentes para optimización
 * - Redirecciones inteligentes
 * - Manejo de errores de navegación
 * 
 * Estructura de rutas:
 * - /login, /signup: Autenticación pública
 * - /dashboard: Panel principal (usuarios autenticados)
 * - /search, /documents: Búsqueda y listado (usuarios autenticados)
 * - /upload, /audit: Funciones administrativas (solo admins)
 * 
 * @component
 * @author Firebase Demo Project
 * @version 1.0.0
 * @since 2024
 */

import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider }  from "./contexts/AuthContext";
import PrivateRoute      from "./components/PrivateRoute";

import Login             from "./components/Login";
import Signup            from "./components/Signup";
import Dashboard         from "./components/Dashboard";
import AuditLogs         from "./components/AuditLogs";
import UploadDocument    from "./components/UploadDocument";
import SearchDocuments   from "./components/SearchDocuments";
import DocumentsList     from "./components/DocumentsList";

import "./App.css";

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* Panel principal (cualquier usuario autenticado) */}
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />

          {/* Sólo administradores */}
          <Route
            path="/upload"
            element={
              <PrivateRoute requireAdmin>
                <UploadDocument />
              </PrivateRoute>
            }
          />
          <Route
            path="/audit"
            element={
              <PrivateRoute requireAdmin>
                <AuditLogs />
              </PrivateRoute>
            }
          />

          {/* Disponibles para todos los usuarios autenticados */}
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

          {/* Redirección por defecto */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}
