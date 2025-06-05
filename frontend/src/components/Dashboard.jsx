// frontend/src/components/Dashboard.jsx
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

  /* ---------- carga información del usuario ---------- */
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

  /* ---------- logout ---------- */
  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  /* ---------- prueba ruta admin ---------- */
  const testAdminRoute = async () => {
    try {
      const { data } = await authAPI.testAdminRoute();
      alert(`Admin test successful: ${data.message}`);
    } catch (err) {
      alert(`Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  if (loading) return <div className="loading">Loading…</div>;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Gemini Indexer Demo</h1>
        <button onClick={handleLogout} className="logout-button">
          Log Out
        </button>
      </header>

      <div className="dashboard-content">
        {/* ---------- info usuario ---------- */}
        <div className="user-info">
          <h2>Welcome, {currentUser.email}</h2>
          <p><strong>UID:</strong> {currentUser.uid}</p>
          {userInfo && (
            <p><strong>Role:</strong> {isAdmin ? "Admin" : "User"}</p>
          )}
          {error && <div className="error-message">{error}</div>}
        </div>

        {/* ---------- acciones ---------- */}
        <div className="dashboard-actions">
          {/* bloque auth test (visibles a todos) */}
          <div className="action-section">
            <h3>Authentication Test</h3>
            <button onClick={testAdminRoute} className="test-button">
              Test Admin Route
            </button>
          </div>

          {/* gestión de documentos */}
          <div className="action-section">
            <h3>Document Management</h3>

            {/* Upload solo admins */}
            {isAdmin && (
              <button
                onClick={() => navigate("/upload")}
                className="action-button"
              >
                Upload Document
              </button>
            )}

            <button
              onClick={() => navigate("/search")}
              className="action-button"
            >
              Search Documents
            </button>
            <button
              onClick={() => navigate("/documents")}
              className="action-button"
            >
              View All Documents
            </button>
          </div>

          {/* herramientas admin */}
          {isAdmin && (
            <div className="action-section">
              <h3>Admin Tools</h3>
              <button
                onClick={() => navigate("/audit")}
                className="test-button"
              >
                Audit Logs
              </button>
            </div>
          )}
        </div>

        {/* ---------- token debug ---------- */}
        <div className="token-info">
          <h3>Current ID Token (debug):</h3>
          <textarea
            readOnly
            rows={3}
            className="token-display"
            value={idToken || "No token available"}
          />
        </div>
      </div>
    </div>
  );
}
