# backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

# Determina la ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# La ruta al archivo .env asumiendo que está en la misma carpeta que config.py
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding='utf-8',
        extra='ignore' # Ignorar variables en .env que no estén definidas aquí
    )

    FIREBASE_SERVICE_ACCOUNT_KEY_PATH: str = Field(..., description="Path to Firebase service account JSON file.")
    FIREBASE_STORAGE_BUCKET: str = Field(..., description="Firebase Storage bucket name.")
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API Key.")
    MEILISEARCH_HOST: str = Field(..., description="Meilisearch host URL.")
    MEILISEARCH_MASTER_KEY: str | None = Field(None, description="Meilisearch master key (optional).")
    SECRET_KEY: str = Field(..., description="Secret key for JWTs and other security features.")
    APP_ENV: str = Field("development", description="Application environment (e.g., development, production).")

# Instancia de las configuraciones para ser importada en otros módulos
settings = Settings()

if __name__ == "__main__":
    print("Cargando configuraciones desde .env:")
    print(f"Firebase Service Account Path: {settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH}")
    print(f"Firebase Storage Bucket: {settings.FIREBASE_STORAGE_BUCKET}")
    print(f"Gemini API Key: {settings.GEMINI_API_KEY[:5]}...") # Mostrar solo los primeros caracteres
    print(f"Meilisearch Host: {settings.MEILISEARCH_HOST}")
    print(f"Meilisearch Master Key: {settings.MEILISEARCH_MASTER_KEY if settings.MEILISEARCH_MASTER_KEY else 'N/A'}")
    print(f"Secret Key: {settings.SECRET_KEY[:5]}...")
    print(f"App Environment: {settings.APP_ENV}")