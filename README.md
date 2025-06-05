# Gemini Indexer Demo

A full-stack application for uploading, indexing, and searching documents using Google Gemini AI, Firebase, and Meilisearch.

## Project Structure

```
demo_firebase/
├── backend/                    # Python FastAPI backend
├── frontend/                   # React + Vite frontend
├── meilisearch-server/         # Meilisearch binary and data
├── meilisearch-data/           # Meilisearch data directory (git-ignored)
├── .gitignore                  # Main git ignore file
└── README.md                   # This file
```

## Features

- **Authentication**: Firebase Authentication with admin/user roles
- **Document Upload**: File upload and processing
- **AI Indexing**: Google Gemini AI for document analysis
- **Search**: Meilisearch for fast, typo-tolerant search
- **Audit Logging**: Comprehensive activity logging

## Prerequisites

- Python 3.11+
- Node.js 18+
- Google Cloud Project with Gemini API access
- Firebase project with Authentication and Firestore

## Setup Instructions

### 1. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

### 3. Environment Configuration
Create a `.env` file in the `backend/` directory with your configuration.

### 4. Start Services
1. Start Meilisearch server
2. Start backend: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
3. Start frontend: `npm run dev`

## Default Admin User
- Email: admin@example.com
- Password: adminpassword

## Tech Stack

- **Backend**: FastAPI, Python
- **Frontend**: React, Vite
- **Database**: Firebase Firestore
- **Authentication**: Firebase Auth
- **Search**: Meilisearch
- **AI**: Google Gemini API
