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

  // ------------------------------------------------------------
  // Cargar la información del usuario — solo 1 llamada
  // ------------------------------------------------------------
  useEffect(() => {
    if (!currentUser) return;

    const loadUserInfo = async () => {
      try {
        const { data } = await authAPI.getCurrentUser();
        setUserInfo(data);
        setError("");
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
        console.error("Error loading user info:", err);
      } finally {
        setLoading(false);
      }
    };

    loadUserInfo();
  }, [currentUser]);

  // ------------------------------------------------------------
  // Logout
  // ------------------------------------------------------------
  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (error) {
      console.error("Error during logout:", error);
      // Even if logout fails, redirect to login
      navigate("/login");
    }
  };

  // ------------------------------------------------------------
  // Test admin route
  // ------------------------------------------------------------
  const testAdminRoute = async () => {
    try {
      const response = await authAPI.testAdminRoute();
      alert(`Admin test successful: ${response.data.message}`);
    } catch (err) {
      alert(`Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Gemini Indexer Demo</h1>
        <button onClick={handleLogout} className="logout-button">
          Log Out
        </button>
      </header>

      <div className="dashboard-content">
        <div className="user-info">
          <h2>Welcome, {currentUser?.email}</h2>
          <p><strong>UID:</strong> {currentUser?.uid}</p>
          {userInfo && (
            <p><strong>Role:</strong> {userInfo.is_admin ? 'Admin' : 'User'}</p>
          )}
          {error && <div className="error-message">{error}</div>}
        </div>

        <div className="dashboard-actions">
          <div className="action-section">
            <h3>Authentication Test</h3>
            <button onClick={testAdminRoute} className="test-button">
              Test Admin Route
            </button>
          </div>

          <div className="action-section">
            <h3>Document Management</h3>
            <button 
              onClick={() => navigate("/upload")} 
              className="action-button"
            >
              Upload Document
            </button>
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

        {/* Debug token display */}
        <div className="token-info">
          <h3>Current ID Token (for debugging):</h3>
          <textarea 
            readOnly 
            value={idToken || 'No token available'} 
            className="token-display"
            rows={3}
          />
          <p className="token-note">
            This token is automatically sent with API requests.
          </p>
        </div>
      </div>
    </div>
  );
}
