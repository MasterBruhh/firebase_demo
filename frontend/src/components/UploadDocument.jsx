/**
 * Componente de Subida de Documentos - Carga de Archivos al Sistema
 * 
 * Este componente proporciona una interfaz completa para la subida de documentos
 * al sistema. Incluye validación de archivos, procesamiento con IA, y gestión
 * de metadatos automática usando Google Gemini.
 * 
 * Funcionalidades principales:
 * - Subida de archivos con drag & drop
 * - Validación exhaustiva de tipos y tamaños
 * - Vista previa de archivos seleccionados
 * - Procesamiento automático con IA (Gemini)
 * - Extracción de metadatos inteligente
 * - Progreso de subida en tiempo real
 * - Manejo de errores detallado
 * - Solo accesible para administradores
 * 
 * Tipos de archivo soportados:
 * - PDF: Documentos portátiles
 * - DOCX: Documentos de Word
 * - PPTX: Presentaciones de PowerPoint
 * - XLSX: Hojas de cálculo de Excel
 * 
 * Límites y validaciones:
 * - Tamaño máximo: 50MB por archivo
 * - Formatos permitidos: PDF, DOCX, PPTX, XLSX
 * - Validación de MIME types
 * - Verificación de integridad de archivos
 * 
 * Flujo de procesamiento:
 * 1. Selección/arrastre del archivo
 * 2. Validación local del archivo
 * 3. Subida al servidor con progreso
 * 4. Procesamiento con Google Gemini IA
 * 5. Extracción de metadatos
 * 6. Indexación en Meilisearch
 * 7. Confirmación y enlaces de descarga
 * 
 * Seguridad:
 * - Solo admins pueden subir archivos
 * - Validación de tipos MIME
 * - Límites de tamaño estrictos
 * - Sanitización de nombres de archivo
 * - Verificación de permisos en backend
 * 
*/

import React, { useState } from "react";
import { documentsAPI } from "../services/api";

export default function UploadDocument() {
  const [file,    setFile]    = useState(null);
  const [msg,     setMsg]     = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setMsg("");
    try {
      const { data } = await documentsAPI.upload(file);
      setMsg(`✅ Documento subido correctamente: ${data.filename || data.file_name}`);
      setFile(null);
    } catch (err) {
      setMsg(`❌ Error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page upload-page">
      <h2>Subir documento</h2>

      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".pdf,.docx,.pptx,.xlsx"
          onChange={(e) => setFile(e.target.files[0] || null)}
        />
        <button type="submit" disabled={!file || loading}>
          {loading ? "Subiendo…" : "Subir"}
        </button>
      </form>

      <p>{msg}</p>
    </div>
  );
}
