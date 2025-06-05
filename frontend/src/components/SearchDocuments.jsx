// frontend/src/components/SearchDocuments.jsx
import React, { useState } from "react";
import { documentsAPI } from "../services/api";
import { useAuth } from "../contexts/AuthContext";

export default function SearchDocuments() {
  const { currentUser } = useAuth();
  const [query, setQuery]   = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  // ------------------------------------------------------------
  // Buscar en los JSON locales
  // ------------------------------------------------------------
  const handleSearch = async () => {
    const q = query.trim().toLowerCase();
    if (!q) return;

    setLoading(true);
    setError("");
    try {
      const { data } = await documentsAPI.list();        // ← lee solo los JSON locales
      const docs = data.documents || [];

      const matched = docs.filter((d) => {
        const textBank = [
          d.filename || d.file_name,
          d.title,
          d.summary,
          ...(d.keywords || []),
        ]
          .join(" ")
          .toLowerCase();
        return textBank.includes(q);
      });

      setResults(matched);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // ------------------------------------------------------------
  // Descargar binario por su id (file_stem)
  // ------------------------------------------------------------
  const handleDownload = async (id, filename) => {
    try {
      const resp = await documentsAPI.download(id);
      const url = URL.createObjectURL(new Blob([resp.data]));
      const a   = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.response?.data?.detail || "Download failed.");
    }
  };

  // ------------------------------------------------------------
  // Render
  // ------------------------------------------------------------
  return (
    <div className="page search-page">
      <h2>Search Local Documents</h2>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="keyword…"
        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
      />
      <button onClick={handleSearch} disabled={loading}>
        {loading ? "Searching…" : "Search"}
      </button>

      {error && <p className="error">{error}</p>}

      {results.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>File</th>
              <th>Title</th>
              <th>Date</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {results.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.filename || doc.file_name}</td>
                <td>{doc.title}</td>
                <td>{doc.date}</td>
                <td>
                  <button
                    onClick={() =>
                      handleDownload(doc.id, doc.filename || doc.file_name)
                    }
                  >
                    Download
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {results.length === 0 && !loading && <p>No matches.</p>}

      <p>User: {currentUser?.email}</p>
    </div>
  );
}
