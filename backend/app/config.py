from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM (Gemini). Vertex AI con créditos GCP, o API key de AI Studio como alternativa.
    google_genai_use_vertexai: bool = True
    google_cloud_project: str | None = None
    google_cloud_location: str = "global"
    # JSON de service account. Si falta, se usan las credenciales por defecto (gcloud auth application-default login).
    google_application_credentials: Path | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3-flash-preview"
    # Solo modelos Gemini 3 (minimal, low, medium, high). "low" reduce la latencia a la mitad sin perder calidad.
    gemini_thinking_level: str | None = None

    workspace_dir: Path = Path("workspace")

    # Orígenes del frontend (Vite dev server por defecto). En .env: CORS_ORIGINS='["http://localhost:5173"]'
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Clustering: k se elige por silhouette dentro de este rango.
    # Mínimo 3 porque 2 segmentos rara vez sirven para marketing.
    k_min: int = 3
    k_max: int = 8

    # Agente
    max_query_rows: int = 50
    max_agent_steps: int = 6

    @property
    def llm_configured(self) -> bool:
        if self.google_genai_use_vertexai:
            return bool(self.google_cloud_project)
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
