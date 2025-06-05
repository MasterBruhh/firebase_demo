// frontend/src/components/DocumentsList.jsx
import React, { useEffect, useState } from "react";
import { documentsAPI } from "../services/api";
import { useAuth } from "../contexts/AuthContext";

export default function DocumentsList() {
  const { currentUser } = useAuth();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ---------- carga desde Firebase Storage ----------
  useEffect(() => {
    (async () => {
      try {
        const { data } = await documentsAPI.listStorage();
        setFiles(data.files || []);
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load storage files.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleDownload = async (path, filename) => {
    try {
      const resp = await documentsAPI.downloadByPath(path);
      const url = URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.response?.data?.detail || "Download failed.");
    }
  };

  const formatSize = (bytes) =>
    bytes ? `${(bytes / 1024).toFixed(1)} KB` : "—";

  if (loading) return <p>Loading…</p>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="docs-list">
      <h1>Files in Firebase Storage</h1>

      {files.length === 0 ? (
        <p>No files found.</p>
      ) : (
        <table className="docs-table">
          <thead>
            <tr>
              <th>Filename</th>
              <th>Size</th>
              <th>Updated</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.path}>
                <td>{f.filename}</td>
                <td>{formatSize(f.size)}</td>
                <td>{new Date(f.updated).toLocaleString()}</td>
                <td>
                  <button onClick={() => handleDownload(f.path, f.filename)}>
                    Download
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <footer>
        <small>Logged in as {currentUser?.email}</small>
      </footer>
    </div>
  );
}
