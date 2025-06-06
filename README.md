# Demo de Indexador con Gemini

Aplicación *full-stack* para subir, indexar y buscar documentos usando Google Gemini AI, Firebase y Meilisearch.

## Estructura del proyecto

```
demo_firebase/
├── backend/                    # Backend Python FastAPI
├── frontend/                   # Frontend React + Vite
├── meilisearch-server/         # Binario y datos de Meilisearch
├── meilisearch-data/           # Directorio de datos de Meilisearch (git-ignored)
├── .gitignore                  # Archivo principal de exclusiones
└── README.md                   # Este archivo
```

## Funcionalidades

* **Autenticación**: Firebase Auth con roles de administrador/usuario
* **Subida de documentos**: Carga y procesamiento de archivos
* **Indexación IA**: Análisis de documentos con Google Gemini AI
* **Búsqueda**: Meilisearch para búsquedas rápidas y tolerantes a errores
* **Auditoría**: Registro completo de actividades

## Requisitos previos

* Python 3.11 o superior
* Node.js 18 o superior
* Proyecto de Google Cloud con acceso a la API de Gemini
* Proyecto Firebase con Authentication y Firestore habilitados

## Pasos de configuración

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### 2. Frontend

```bash
cd frontend
npm install
```

### 3. Variables de entorno

Crea un archivo `.env` dentro de `backend/` con tu configuración (claves de API, bucket de Storage, etc.).

### 4. Arranque de servicios

1. Inicia el servidor de Meilisearch.
2. Levanta el backend:

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
3. Inicia el frontend:

   ```bash
   npm run dev
   ```

## Usuario administrador por defecto

* **Correo**: [admin@example.com](mailto:admin@example.com)
* **Contraseña**: adminpassword

## Tecnologías empleadas

| Capa              | Tecnología         |
| ----------------- | ------------------ |
| **Backend**       | FastAPI, Python    |
| **Frontend**      | React, Vite        |
| **Base de datos** | Firebase Firestore |
| **Autenticación** | Firebase Auth      |
| **Búsqueda**      | Meilisearch        |
| **IA**            | Google Gemini API  |

---
