from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="enterprise-workforce-agents")
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    cors_allowed_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ]
    )

    # Security
    jwt_secret_key: str = Field(default="enterprise-workforce-default-secret-key-change-in-prod")
    jwt_algorithm: str = Field(default="HS256")
    rate_limit_per_minute: int = Field(default=200)

    # Orchestration
    max_graph_steps: int = Field(default=15)
    execution_timeout_seconds: int = Field(default=30)
    hitl_approval_threshold_amount: float = Field(default=5000.00)
    checkpoint_dir: str = Field(default="data/checkpoints")

    # Database
    db_path: str = Field(default="data/enterprise_db.sqlite")
    max_query_rows: int = Field(default=100)
    query_timeout_seconds: float = Field(default=5.0)

    # LLM
    llm_provider: str = Field(default="deterministic")
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")
    ollama_base_url: str = Field(default="http://localhost:11434")

    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}

            flat: Dict[str, Any] = {}
            if "app" in raw:
                flat["app_name"] = raw["app"].get("name", "enterprise-workforce-agents")
                flat["app_env"] = raw["app"].get("environment", "development")
                flat["log_level"] = raw["app"].get("log_level", "INFO")
                if "cors_allowed_origins" in raw["app"]:
                    flat["cors_allowed_origins"] = raw["app"]["cors_allowed_origins"]
            if "security" in raw:
                flat["jwt_secret_key"] = raw["security"].get("jwt_secret_key", "enterprise-workforce-default-secret-key-change-in-prod")
                flat["jwt_algorithm"] = raw["security"].get("jwt_algorithm", "HS256")
                flat["rate_limit_per_minute"] = raw["security"].get("rate_limit_per_minute", 200)
            if "orchestration" in raw:
                flat["max_graph_steps"] = raw["orchestration"].get("max_graph_steps", 15)
                flat["execution_timeout_seconds"] = raw["orchestration"].get("execution_timeout_seconds", 30)
                flat["hitl_approval_threshold_amount"] = raw["orchestration"].get("hitl_approval_threshold_amount", 5000.0)
                flat["checkpoint_dir"] = raw["orchestration"].get("checkpoint_dir", "data/checkpoints")
            if "database" in raw:
                flat["db_path"] = raw["database"].get("db_path", "data/enterprise_db.sqlite")
                flat["max_query_rows"] = raw["database"].get("max_query_rows", 100)
                flat["query_timeout_seconds"] = raw["database"].get("query_timeout_seconds", 5.0)
            if "llm" in raw:
                flat["llm_provider"] = raw["llm"].get("provider", "deterministic")
                flat["openai_model"] = raw["llm"].get("openai_model", "gpt-4o-mini")
                flat["ollama_base_url"] = raw["llm"].get("ollama_base_url", "http://localhost:11434")

            return cls(**flat)
        return cls()

    def validate_production_security(self) -> None:
        if self.app_env.lower() in ["production", "prod"]:
            if "default-secret-key" in self.jwt_secret_key:
                raise ValueError(
                    "FATAL SECURITY VIOLATION: Cannot start application in production with default insecure "
                    "jwt_secret_key. Configure a cryptographically secure key via JWT_SECRET_KEY environment variable."
                )


settings = Settings()
