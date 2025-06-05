// frontend/src/components/UploadDocument.jsx
import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { documentsAPI } from "../services/api";

export default function UploadDocument() {
  const { currentUser } = useAuth();
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setMsg("");
    try {
      const { data } = await documentsAPI.upload(file);
      setMsg(`✅ Subido: ${data.filename || data.file_name}`);
      setFile(null);
    } catch (err) {
      setMsg(
        `❌ Error: ${err.response?.data?.detail || err.message || "desconocido"}`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page upload-page">
      <h2>Upload Document</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".pdf,.docx,.pptx,.xlsx"
          onChange={(e) => setFile(e.target.files[0] || null)}
        />
        <button type="submit" disabled={!file || loading}>
          {loading ? "Uploading…" : "Upload"}
        </button>
      </form>
      <p>{msg}</p>
      <p>User: {currentUser?.email}</p>
    </div>
  );
}
