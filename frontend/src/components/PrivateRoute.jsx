/**
 * Componente de Ruta Privada - Control de Acceso y Autenticación
 * 
 * Este componente actúa como un wrapper de protección para rutas que requieren
 * autenticación y/o autorización específica. Maneja la lógica de redirección
 * basada en el estado de autenticación del usuario y sus permisos.
 * 
 * Funcionalidades principales:
 * - Protección de rutas privadas que requieren autenticación
 * - Control de acceso basado en roles (admin/usuario)
 * - Redirección automática a login si no está autenticado
 * - Redirección a dashboard si no tiene permisos de admin
 * - Manejo de estados de carga durante la verificación
 * - Integración con el contexto de autenticación
 * 
 * Props:
 * - children: Componentes hijos a renderizar si tiene acceso
 * - requireAdmin: Booleano que indica si requiere permisos de administrador
 * 
 * Estados manejados:
 * - Verificación de usuario autenticado
 * - Verificación de permisos de administrador
 * - Estados de carga durante la autenticación
 * 
 * Casos de uso:
 * - Proteger rutas del dashboard general
 * - Proteger rutas administrativas específicas
 * - Controlar acceso a funcionalidades sensibles
 * 
 * Seguridad:
 * - Verificación en tiempo real del estado de autenticación
 * - Control granular de permisos por rol
 * - Redirecciones seguras sin exposición de datos
 * - Prevención de acceso no autorizado
 * 
*/

import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function PrivateRoute({ children, requireAdmin = false }) {
  const { currentUser, isAdmin } = useAuth();

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
