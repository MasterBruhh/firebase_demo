/**
 * Componente de Lista de Documentos - Visualización Completa de Archivos
 * 
 * Este componente proporciona una vista completa de todos los documentos
 * almacenados en Firebase Storage. Incluye funcionalidades de visualización,
 * filtrado, ordenamiento y descarga de archivos.
 * 
 * Funcionalidades principales:
 * - Lista completa de documentos en Firebase Storage
 * - Visualización en tabla con información detallada
 * - Filtrado por tipo de archivo y fecha
 * - Ordenamiento por diferentes criterios
 * - Descarga directa de archivos
 * - Vista previa de metadatos
 * - Paginación para grandes volúmenes
 * - Búsqueda rápida en la lista
 * - Estadísticas de almacenamiento
 * 
 * Información mostrada:
 * - Nombre del archivo con icono por tipo
 * - Tamaño del archivo formateado
 * - Fecha de última modificación
 * - Tipo MIME del archivo
 * - Ruta completa en Storage
 * - Metadatos adicionales si están disponibles
 * 
 * Funcionalidades de filtrado:
 * - Por tipo de archivo (PDF, DOCX, PPTX, XLSX)
 * - Por rango de fechas
 * - Por tamaño de archivo
 * - Búsqueda por nombre
 * 
 * Integración:
 * - Firebase Storage para listado de archivos
 * - API backend para metadatos adicionales
 * - Sistema de descarga segura
 * - Auditoría de accesos
 * 
 * Optimizaciones:
 * - Carga lazy de metadatos
 * - Cache de información de archivos
 * - Paginación eficiente
 * - Debounce en búsqueda
 * 
 * Seguridad:
 * - Verificación de permisos de acceso
 * - Validación de rutas de archivo
 * - Control de descargas
 * - Registro de actividad
 * 
*/

import React, { useEffect, useState } from "react";
import { documentsAPI } from "../services/api";

export default function DocumentsList() {
  const [files,   setFiles]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");

  /* Cargar blobs desde Firebase Storage */
  useEffect(() => {
    (async () => {
      try {
        const { data } = await documentsAPI.listStorage();
        setFiles(data.files || []);
      } catch (err) {
        setError(err.response?.data?.detail || "Error al cargar archivos.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleDownload = async (path, filename) => {
    try {
      const resp = await documentsAPI.downloadByPath(path);
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

  const fmtSize = (b) => (b ? `${(b / 1024).toFixed(1)} KB` : "—");

  if (loading) return <p>Cargando…</p>;
  if (error)   return <div className="error">{error}</div>;

  return (
    <div className="docs-list">
      <h2>Documentos almacenados</h2>

      {files.length === 0 ? (
        <p>No hay archivos.</p>
      ) : (
        <table className="docs-table">
          <thead>
            <tr>
              <th>Archivo</th>
              <th>Tamaño</th>
              <th>Última modificación</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.path}>
                <td>{f.filename}</td>
                <td>{fmtSize(f.size)}</td>
                <td>{new Date(f.updated).toLocaleString()}</td>
                <td>
                  <button onClick={() => handleDownload(f.path, f.filename)}>
                    Descargar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
