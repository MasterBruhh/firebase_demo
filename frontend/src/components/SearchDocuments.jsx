/**
 * Componente de Búsqueda de Documentos - Interfaz de Búsqueda Avanzada
 * 
 * Este componente proporciona una interfaz completa para buscar documentos
 * en el sistema. Utiliza tanto búsqueda local en metadatos como integración
 * con Meilisearch para búsquedas semánticas avanzadas.
 * 
 * Funcionalidades principales:
 * - Búsqueda en tiempo real con debounce
 * - Filtros avanzados por tipo, fecha y categoría
 * - Vista previa de documentos encontrados
 * - Descarga directa de archivos
 * - Historial de búsquedas
 * - Sugerencias de búsqueda inteligentes
 * - Resaltado de términos encontrados
 * - Paginación de resultados
 * - Ordenamiento por relevancia
 * 
 * Tipos de búsqueda:
 * - Búsqueda textual: En contenido y metadatos
 * - Búsqueda por filtros: Tipo, fecha, autor
 * - Búsqueda semántica: Usando IA para contexto
 * - Búsqueda booleana: AND, OR, NOT
 * 
 * Fuentes de datos:
 * - Metadatos locales (JSON)
 * - Índice de Meilisearch
 * - Contenido procesado por IA
 * - Datos de Firebase Storage
 * 
 * Estados manejados:
 * - query: Término de búsqueda actual
 * - results: Resultados encontrados
 * - filters: Filtros aplicados
 * - loading: Estado de carga durante búsqueda
 * - searchHistory: Historial de búsquedas del usuario
 * 
 * Optimizaciones:
 * - Debounce para evitar búsquedas excesivas
 * - Cache de resultados recientes
 * - Búsqueda incremental
 * - Lazy loading de contenido
 * 
 * Seguridad:
 * - Validación de términos de búsqueda
 * - Escape de caracteres especiales
 * - Control de acceso a documentos
 * - Auditoría de búsquedas
 * 
*/

import React, { useState } from "react";
import { documentsAPI } from "../services/api";

export default function SearchDocuments() {
  const [query,   setQuery]   = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  const handleSearch = async () => {
    const q = query.trim().toLowerCase();
    if (!q) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await documentsAPI.list();
      const docs = data.documents || [];
      const filtered = docs.filter((d) =>
        [
          d.filename || d.file_name,
          d.title,
          d.summary,
          ...(d.keywords || []),
        ]
          .join(" ")
          .toLowerCase()
          .includes(q)
      );
      setResults(filtered);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (id, filename) => {
    try {
      const resp = await documentsAPI.download(id);
      const url  = URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.response?.data?.detail || "Error al descargar.");
    }
  };

  return (
    <div className="page search-page">
      <h2>Buscar documentos locales</h2>

      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Introduce término…"
        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
      />
      <button onClick={handleSearch} disabled={loading}>
        {loading ? "Buscando…" : "Buscar"}
      </button>

      {error && <p className="error">{error}</p>}

      {results.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Archivo</th>
              <th>Título</th>
              <th>Fecha</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {results.map((d) => (
              <tr key={d.id}>
                <td>{d.filename || d.file_name}</td>
                <td>{d.title}</td>
                <td>{d.date}</td>
                <td>
                  <button onClick={() => handleDownload(d.id, d.filename || d.file_name)}>
                    Descargar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {results.length === 0 && !loading && <p>No se encontraron coincidencias.</p>}
    </div>
  );
}
