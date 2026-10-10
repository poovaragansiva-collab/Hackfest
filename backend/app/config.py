from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:3000,http://localhost:3000"
    
    # Active provider options: "automatic1111", "mock", "huggingface", "google", "openrouter", "openai", "stability"
    active_provider: str = "automatic1111"
    automatic1111_base_url: str = "http://127.0.0.1:7860"
    sd_webui_url: str = "http://127.0.0.1:7860"
    sd_timeout_seconds: int = 180
    
    # OpenRouter Provider Configuration (Riverflow V2 Fast)
    openrouter_api_key: str = ""
    openrouter_model: str = "sourceful/riverflow-v2-fast"
    openrouter_base_url: str = "https://openrouter.ai/api/v1/images"

    # Google Gemini Provider Configuration (official google-genai SDK)
    google_api_key: str = ""
    google_model: str = "gemini-2.5-flash-image"
    
    # Hugging Face Provider Configuration (InferenceClient via fal-ai)
    hf_token: str = ""
    hf_model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    hf_provider: str = "fal-ai"

    # Optional legacy provider keys
    openai_api_key: str = ""
    stability_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origin_list(self) -> List[str]:
        origins = set()
        for origin in self.cors_origins.split(","):
            cleaned = origin.strip().rstrip("/")
            if cleaned:
                origins.add(cleaned)
        # Always guarantee core local dev origins are included safely
        origins.update([
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ])
        return sorted(list(origins))


settings = Settings()
