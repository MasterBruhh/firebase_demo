import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { auditAPI } from "../services/api";

export default function AuditLogs() {
  const { isAdmin } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect if not admin
    if (!isAdmin) {
      navigate("/dashboard");
      return;
    }

    // Load audit logs
    const loadLogs = async () => {
      try {
        setLoading(true);
        const response = await auditAPI.getLogs(100);
        setLogs(response.data.logs || []);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load audit logs");
        console.error("Error loading audit logs:", err);
      } finally {
        setLoading(false);
      }
    };

    loadLogs();
  }, [isAdmin, navigate]);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return "N/A";
    
    // Handle Firestore timestamp format
    if (timestamp._seconds) {
      return new Date(timestamp._seconds * 1000).toLocaleString();
    }
    
    // Handle regular date string
    return new Date(timestamp).toLocaleString();
  };

  const formatDetails = (details) => {
    if (!details || Object.keys(details).length === 0) return "No details";
    return JSON.stringify(details, null, 2);
  };

  if (loading) {
    return (
      <div className="audit-logs">
        <h1>Audit Logs</h1>
        <p>Loading logs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="audit-logs">
        <h1>Audit Logs</h1>
        <div className="error">{error}</div>
        <button onClick={() => navigate("/dashboard")}>Back to Dashboard</button>
      </div>
    );
  }

  return (
    <div className="audit-logs">
      <header className="audit-header">
        <h1>Audit Logs</h1>
        <button onClick={() => navigate("/dashboard")}>Back to Dashboard</button>
      </header>

      <div className="logs-container">
        {logs.length === 0 ? (
          <p>No audit logs found.</p>
        ) : (
          <table className="logs-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>User ID</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id || Math.random()}>
                  <td>{formatTimestamp(log.timestamp)}</td>
                  <td>
                    <span className={`event-type ${log.event_type?.toLowerCase()}`}>
                      {log.event_type}
                    </span>
                  </td>
                  <td>{log.user_id || "System"}</td>
                  <td>
                    <pre className="details">{formatDetails(log.details)}</pre>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
} 