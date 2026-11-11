"""
Core Settings module using Pydantic Settings.
Manages environment variables, API key configurations, and application settings.
"""

from functools import lru_cache
from typing import Literal, Optional
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings configuration loader.
    Reads values from environment variables or .env file.
    """
    # Project Identity
    PROJECT_NAME: str = "Autonomous Multi-Agent Research & Fact Verification System"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # LLM API Configuration
    OPENAI_API_KEY: Optional[SecretStr] = Field(default=None, description="OpenAI API Key")
    ANTHROPIC_API_KEY: Optional[SecretStr] = Field(default=None, description="Anthropic API Key")
    GOOGLE_API_KEY: Optional[SecretStr] = Field(default=None, description="Google Gemini API Key")
    GROQ_API_KEY: Optional[SecretStr] = Field(default=None, description="Groq API Key")
    LLM_PROVIDER: Optional[str] = Field(default=None, description="LLM provider alias")
    DEFAULT_LLM_PROVIDER: Literal["claude", "openai", "gemini", "groq"] = Field(
        default="groq", description="Primary LLM provider to use for agent reasoning"
    )
    CLAUDE_MODEL_NAME: str = Field(default="claude-3-5-sonnet-20241022", description="Claude model identifier")
    OPENAI_MODEL: Optional[str] = Field(default=None, description="OpenAI model identifier alias")
    OPENAI_MODEL_NAME: str = Field(default="gpt-4o", description="OpenAI model identifier")
    GEMINI_MODEL_NAME: str = Field(default="gemini-2.5-flash", description="Gemini model identifier")
    GEMINI_MODEL: Optional[str] = Field(default=None, description="Gemini model identifier alias")
    GROQ_MODEL: Optional[str] = Field(default=None, description="Groq model identifier alias")
    GROQ_MODEL_NAME: str = Field(default="openai/gpt-oss-120b", description="Groq model identifier")

    # Search Provider
    TAVILY_API_KEY: Optional[SecretStr] = Field(default=None, description="Tavily API Key for live web search")

    # Vector Embedding Model
    EMBEDDING_MODEL_NAME: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="SentenceTransformers local embedding model name",
    )

    # MongoDB Atlas Database Configuration
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string URI",
    )
    MONGODB_DB_NAME: str = Field(default="fact_verification_db", description="Database name")
    MONGODB_COLLECTION_NAME: str = Field(
        default="research_analyses", description="Unified collection for research job documents"
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def anthropic_api_key_str(self) -> Optional[str]:
        """Returns Anthropic API key as plain string if set."""
        return self.ANTHROPIC_API_KEY.get_secret_value() if self.ANTHROPIC_API_KEY else None

    @property
    def openai_api_key_str(self) -> Optional[str]:
        """Returns OpenAI API key as plain string if set."""
        return self.OPENAI_API_KEY.get_secret_value() if self.OPENAI_API_KEY else None

    @property
    def google_api_key_str(self) -> Optional[str]:
        """Returns Google API key as plain string if set."""
        return self.GOOGLE_API_KEY.get_secret_value() if self.GOOGLE_API_KEY else None

    @property
    def tavily_api_key_str(self) -> Optional[str]:
        """Returns Tavily API key as plain string if set."""
        return self.TAVILY_API_KEY.get_secret_value() if self.TAVILY_API_KEY else None

    @property
    def groq_api_key_str(self) -> Optional[str]:
        """Returns Groq API key as plain string if set."""
        return self.GROQ_API_KEY.get_secret_value() if self.GROQ_API_KEY else None

    @property
    def effective_provider(self) -> str:
        """Returns active LLM provider ('groq', 'openai', 'gemini', 'claude')."""
        return (self.LLM_PROVIDER or self.DEFAULT_LLM_PROVIDER or "groq").lower().strip()

    @property
    def effective_groq_model(self) -> str:
        """Returns Groq model identifier."""
        return (self.GROQ_MODEL or self.GROQ_MODEL_NAME or "openai/gpt-oss-120b").strip()

    @property
    def effective_openai_model(self) -> str:
        """Returns OpenAI model name."""
        return (self.OPENAI_MODEL or self.OPENAI_MODEL_NAME or "gpt-4o").strip()

    @property
    def effective_gemini_model(self) -> str:
        """Returns normalized Gemini model name without 'models/' prefix."""
        raw = self.GEMINI_MODEL or self.GEMINI_MODEL_NAME or "gemini-2.5-flash"
        return raw.replace("models/", "").strip()


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached singleton instance of Settings.
    """
    return Settings()


# Convenient direct export of singleton settings instance
settings: Settings = get_settings()
