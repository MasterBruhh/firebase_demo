# backend/services/gemini_service.py
from __future__ import annotations

import io
import json
import mimetypes
import re  # <--- Importado para el parseo robusto de JSON
from datetime import datetime
from pathlib import Path
from typing import Dict, Callable

import pdfplumber
from docx import Document as DocxDocument
from pptx import Presentation
import openpyxl
from google.generativeai import GenerativeModel, configure

from config import settings

# ---------------------------------------------------------------------------
# Configura Gemini (usando la clave de settings)
configure(api_key=settings.GEMINI_API_KEY)
_GEMINI = GenerativeModel("gemini-1.5-flash-latest") # Se recomienda usar el modelo más reciente

# ---------------------------------------------------------------------------
# Funciones de extracción de texto (sin cambios, se mantienen como estaban)
def _text_from_pdf(b: bytes) -> str:
    # Agregamos manejo de errores por si el PDF está corrupto o es una imagen
    try:
        with pdfplumber.open(io.BytesIO(b)) as pdf:
            return "\n".join(page.extract_text(x_tolerance=1) or "" for page in pdf.pages)
    except Exception as e:
        print(f"Advertencia: No se pudo procesar el PDF con pdfplumber: {e}")
        return "" # Devolver vacío para que Gemini no procese un error

def _text_from_docx(b: bytes) -> str:
    doc = DocxDocument(io.BytesIO(b))
    return "\n".join(p.text for p in doc.paragraphs)

def _text_from_pptx(b: bytes) -> str:
    prs = Presentation(io.BytesIO(b))
    runs = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                runs.append(shape.text)
    return "\n".join(runs)

def _text_from_xlsx(b: bytes) -> str:
    wb = openpyxl.load_workbook(io.BytesIO(b), data_only=True)
    lines: list[str] = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            # Mejoramos la unión para evitar espacios extra
            lines.append(" ".join(str(c).strip() for c in row if c is not None and str(c).strip()))
    return "\n".join(lines)

_HANDLERS: dict[str, Callable[[bytes], str]] = {
    ".pdf": _text_from_pdf,
    ".docx": _text_from_docx,
    ".pptx": _text_from_pptx,
    ".xlsx": _text_from_xlsx,
}

# ---------------------------------------------------------------------------
def _extract_text(file_bytes: bytes, ext: str) -> str:
    handler = _HANDLERS.get(ext.lower())
    if handler:
        try:
            return handler(file_bytes)
        except Exception as e:
            print(f"Error al extraer texto con el handler para '{ext}': {e}")
            # Fallback a decodificación binaria ingenua
            return file_bytes.decode(errors="ignore")
    # Extensión no soportada → intento de decodificación directa
    return file_bytes.decode(errors="ignore")

# ---------------------------------------------------------------------------
# --- FUNCIÓN MODIFICADA ---
# Se adopta la lógica robusta de gemini_extractor.py
def _call_gemini(text: str) -> dict:
    """
    Llama a Gemini pidiendo JSON con título, resumen, keywords y fecha.
    Utiliza una lógica de parseo robusta para manejar varios formatos de respuesta.
    """
    # Usamos el prompt mejorado de gemini_extractor.py
    prompt = f"""
    Eres un asistente experto en extracción de metadatos de documentos.
    Lee el siguiente documento y extrae la siguiente información en formato JSON:
    - "title": El título principal o el tema central del documento.
    - "summary": Un resumen conciso (máximo 150 palabras) del contenido del documento.
    - "keywords": Una lista de 5 a 10 palabras clave relevantes.
    - "date": La fecha más relevante del documento (fecha de creación, publicación, última modificación, etc.).
      Debe estar en formato YYYY-MM-DD. Si hay múltiples fechas, elige la más representativa del contenido.
      Si no encuentras una fecha explícita, intenta inferirla del contexto del documento.
      Si aún así no es posible determinar una fecha, usa la cadena "Fecha no encontrada".

    Asegúrate de que la salida sea **SOLO** el objeto JSON. No incluyas texto adicional, ni bloques de Markdown (como ```json)
    ni ninguna otra cosa fuera del JSON. Si no puedes extraer una pieza de información, usa "No disponible" para cadenas, o [] para listas.

    Documento:
    {text[:8000]}
    """ # Se aumenta el límite de caracteres para dar más contexto a Gemini

    print(f"--- DEBUG: Enviando a Gemini (primeros 400 caracteres) ---\n{text[:400]}\n----------------------------------------------------")

    try:
        response = _GEMINI.generate_content(prompt, request_options={"timeout": 120})
        raw_text = response.text

        print(f"--- DEBUG: Respuesta cruda de Gemini ---\n{raw_text}\n-----------------------------------------")

        # Lógica de parseo robusta adoptada de gemini_extractor.py
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
        if json_match:
            json_string = json_match.group(1).strip()
        else:
            # Si no hay bloque de código, busca el JSON directamente
            start_brace = raw_text.find('{')
            end_brace = raw_text.rfind('}')
            if start_brace != -1 and end_brace != -1:
                json_string = raw_text[start_brace : end_brace + 1]
            else:
                raise json.JSONDecodeError("No se encontró un objeto JSON en la respuesta.", raw_text, 0)

        data = json.loads(json_string)
        if isinstance(data, dict):
            # Se asegura de que los campos clave existan para evitar errores posteriores
            return {
                "title": data.get("title", "Título no encontrado"),
                "summary": data.get("summary", "Resumen no disponible"),
                "keywords": data.get("keywords", []),
                "date": data.get("date", "Fecha no encontrada"),
            }
        
    except Exception as e:
        print(f"Error al llamar o parsear la respuesta de Gemini: {e}")
        # Fallback si la IA no respetó formato o hubo otro error
        return {
            "title": "Error al procesar con IA",
            "summary": "No se pudo generar el resumen debido a un error.",
            "keywords": [],
            "date": "Fecha no encontrada",
        }

    # Fallback final por si algo inesperado ocurre
    return {
        "title": "Título no encontrado",
        "summary": "Resumen no disponible",
        "keywords": [],
        "date": "Fecha no encontrada",
    }


# ---------------------------------------------------------------------------
# --- FUNCIÓN PRINCIPAL (sin cambios en su lógica de orquestación) ---
def extract_metadata(file_bytes: bytes, filename: str) -> Dict:
    """
    Orquesta la extracción de texto y metadatos con Gemini.
    Devuelve un dict con la metadata final.
    """
    path = Path(filename)
    ext = path.suffix.lower()

    # 1) Extraer texto del documento
    text_content = _extract_text(file_bytes, ext)
    if not text_content.strip():
        print(f"Advertencia: El contenido de '{filename}' está vacío o no pudo ser extraído.")
        text_content = "Contenido vacío o no extraíble." # Mensaje para Gemini

    # 2) Llamar a Gemini con la lógica mejorada
    gemini_meta = _call_gemini(text_content)

    # 3) Ensamblar el diccionario final, compatible con el modelo Pydantic
    return {
        "id": path.stem,
        "filename": filename,
        "file_extension": ext,
        "file_size_bytes": len(file_bytes),
        "title": gemini_meta.get("title"),
        "summary": gemini_meta.get("summary"),
        "keywords": gemini_meta.get("keywords"),
        "date": gemini_meta.get("date"),
    }