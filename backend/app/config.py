"""
Configuration settings loaded from environment variables
"""
from pydantic_settings import BaseSettings
from typing import List,Union
from pydantic import field_validator

class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: str = "azure_openai"  # Options: "openai", "azure_openai", "anthropic"
    openai_api_key: str = ""  # For regular OpenAI (not needed if using Azure OpenAI)
    azure_openai_api_key: str = ""  # Azure OpenAI API key
    azure_openai_endpoint: str = ""  # Azure OpenAI endpoint (e.g., https://your-resource.openai.azure.com/)
    azure_openai_deployment: str = ""  # Azure OpenAI deployment name (e.g., gpt-4-deployment)
    azure_openai_api_version: str = "2025-01-01-preview"  # Azure OpenAI API version
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4o"  # Reference only, actual model comes from Azure deployment
    
    # TTS Configuration
    tts_provider: str = "azure"
    azure_speech_key: str = ""
    azure_speech_region: str = "eastasia"
    azure_voice_male: str = "zh-HK-WanLungNeural"
    azure_voice_female: str = "zh-HK-HiuGaaiNeural"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: Union[str, List[str]] = "http://localhost:3000,http://localhost:3001"
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    # File Storage
    audio_storage_path: str = "./static/audio"
    max_pdf_pages: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

