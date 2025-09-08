"""
Configuration settings for Project Synapse - Fixed for Pydantic v2
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic.types import SecretStr


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    app_name: str = "Project Synapse"
    app_version: str = "1.0.0"
    debug: bool = Field(default=True, env="DEBUG")
    
    # LLM Provider Settings
    groq_api_key: Optional[SecretStr] = Field(default=None, env="GROQ_API_KEY")
    openai_api_key: Optional[SecretStr] = Field(default=None, env="OPENAI_API_KEY")
    
    # Basic settings
    primary_model: str = Field(default="groq", env="PRIMARY_MODEL")
    enable_cot_display: bool = Field(default=True, env="ENABLE_COT_DISPLAY")
    default_city: str = Field(default="mumbai", env="DEFAULT_CITY")
    
    # API Keys for tools
    mappls_api_key: Optional[str] = Field(default=None, env="MAPPLS_API_KEY")
    tomtom_api_key: Optional[str] = Field(default=None, env="TOMTOM_API_KEY")
    
    class Config:
        extra = "allow"  # This allows extra fields from .env
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def validate_config():
    """Validate that required configuration is present"""
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is required. Please add it to your .env file")
    return True


def get_llm_config():
    """Get LLM configuration"""
    return {
        "provider": "groq",
        "api_key": settings.groq_api_key.get_secret_value() if settings.groq_api_key else None,
        "model": "llama-3.1-70b-versatile",
        "temperature": 0.1,
        "max_tokens": 2048
    }
