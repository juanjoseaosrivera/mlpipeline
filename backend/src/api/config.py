from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mlflow_tracking_uri: str = "http://localhost:5000"
    database_url: str = "postgresql://ai_user:securepassword@localhost:5432/mlops_db"
    model_name: str = "ProductionModel"
    model_uri: str = "models:/ProductionModel/latest"
    experiment_name: str = "intelligent-detection-platform"

    allowed_origins: tuple[str, ...] = ("http://localhost", "http://localhost:4200")
    enable_docs: bool = False


settings = Settings()
