/**
 * Componente Dashboard - Panel Principal de Control del Usuario
 * 
 * Este componente sirve como el punto central de navegación y control
 * de la aplicación después del login. Proporciona acceso a todas las
 * funcionalidades del sistema según los permisos del usuario.
 * 
 * Funcionalidades principales:
 * - Panel de bienvenida personalizado
 * - Navegación a funcionalidades principales
 * - Información del usuario actual
 * - Controles administrativos (solo para admins)
 * - Gestión de documentos
 * - Herramientas de auditoría
 * - Sistema de logout seguro
 * 
 * Estados manejados:
 * - userInfo: Información detallada del usuario
 * - loading: Estado de carga durante obtención de datos
 * - error: Mensajes de error de la API
 * - stats: Estadísticas del sistema (admin)
 * 
 * Permisos y roles:
 * - Usuario regular: Búsqueda y visualización de documentos
 * - Administrador: Subida de documentos, auditoría, gestión completa
 * 
 * Integración:
 * - Firebase Authentication para autenticación
 * - API backend para obtener información del usuario
 * - React Router para navegación
 * - Contexto de autenticación
 * 
 * Seguridad:
 * - Verificación de permisos en tiempo real
 * - Separación de funcionalidades por rol
 * - Manejo seguro de tokens
 * - Logout seguro con limpieza de estado
 * 
*/

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { authAPI } from "../services/api";

export default function Dashboard() {
  const { currentUser, isAdmin, logout, idToken } = useAuth();
  const [userInfo, setUserInfo] = useState(null);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");
  const navigate = useNavigate();

  /* Obtener información del usuario */
  useEffect(() => {
    if (!currentUser) return;

    (async () => {
      try {
        const { data } = await authAPI.getCurrentUser();
        setUserInfo(data);
        setError("");
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [currentUser]);

  /* Cerrar sesión */
  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  /* Probar ruta de administrador */
  const testAdminRoute = async () => {
    try {
      const { data } = await authAPI.testAdminRoute();
      alert(`✔️ ${data.message}`);
    } catch (err) {
      const status = err.response?.status;
      if (status === 403) {
        alert("⚠️ Necesitas permisos de administrador para usar esta función.");
      } else if (status === 401) {
        alert("⚠️ Sesión expirada. Vuelve a iniciar sesión.");
      } else {
        alert(`Error inesperado: ${err.response?.data?.detail || err.message}`);
      }
    }
  };

  if (loading) return <div className="loading">Cargando…</div>;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Demo Indexador Gemini</h1>
        <button onClick={handleLogout} className="logout-button">
          Cerrar sesión
        </button>
      </header>

      <div className="dashboard-content">
        {/* Información de usuario */}
        <div className="user-info">
          <h2>Bienvenido, {currentUser.email}</h2>
          <p><strong>UID:</strong> {currentUser.uid}</p>
          <p><strong>Rol:</strong> {isAdmin ? "Admin" : "Usuario"}</p>
          {error && <div className="error-message">{error}</div>}
        </div>

        {/* Acciones */}
        <div className="dashboard-actions">
          {/* Sección de pruebas */}
          <div className="action-section">
            <h3>Prueba de autenticación</h3>
            <button onClick={testAdminRoute} className="test-button">
              Probar ruta de administrador
            </button>
          </div>

          {/* Gestión de documentos */}
          <div className="action-section">
            <h3>Gestión de documentos</h3>
            {isAdmin && (
              <button onClick={() => navigate("/upload")} className="action-button">
                Subir documento
              </button>
            )}
            <button onClick={() => navigate("/search")}   className="action-button">
              Buscar documentos
            </button>
            <button onClick={() => navigate("/documents")} className="action-button">
              Ver documentos
            </button>
          </div>

          {/* Herramientas de administrador */}
          {isAdmin && (
            <div className="action-section">
              <h3>Herramientas de administrador</h3>
              <button onClick={() => navigate("/audit")} className="test-button">
                Registros de auditoría
              </button>
            </div>
          )}
        </div>

        {/* Token debug */}
        <div className="token-info">
          <h3>Token ID (debug)</h3>
          <textarea readOnly rows={3} value={idToken || "Sin token"} />
        </div>
      </div>
    </div>
  );
}

