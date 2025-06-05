import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { authAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const [userInfo, setUserInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { currentUser, logout, idToken } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchUserInfo() {
      if (idToken) {
        try {
          const response = await authAPI.getCurrentUser(idToken);
          setUserInfo(response.data);
        } catch (error) {
          setError('Failed to fetch user information');
          console.error('Error fetching user info:', error);
        }
      }
      setLoading(false);
    }

    fetchUserInfo();
  }, [idToken]);

  async function handleLogout() {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Failed to log out:', error);
    }
  }

  async function testAdminRoute() {
    if (idToken) {
      try {
        const response = await authAPI.testAdminRoute(idToken);
        alert('Admin route response: ' + response.data.message);
      } catch (error) {
        alert('Error: ' + (error.response?.data?.detail || 'Access denied'));
      }
    }
  }

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

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
          <h2>Welcome!</h2>
          <p><strong>Email:</strong> {currentUser?.email}</p>
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
              onClick={() => navigate('/upload')} 
              className="action-button"
            >
              Upload Document
            </button>
            <button 
              onClick={() => navigate('/search')} 
              className="action-button"
            >
              Search Documents
            </button>
            <button 
              onClick={() => navigate('/documents')} 
              className="action-button"
            >
              View All Documents
            </button>
          </div>
        </div>

        <div className="token-info">
          <h3>Current ID Token (for testing):</h3>
          <textarea 
            readOnly 
            value={idToken || 'No token available'} 
            className="token-display"
            rows={3}
          />
          <p className="token-note">
            This token is automatically sent with API requests to authenticate with the backend.
          </p>
        </div>
      </div>
    </div>
  );
} 