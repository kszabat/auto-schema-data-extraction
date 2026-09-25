from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ModelConfig(BaseModel):
    name: str = "gemini-3-flash-preview"
    api_key: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        if isinstance(v, str) and "/" in v:
            return v.replace("/", ":", 1)
        return v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="forbid",
    )

    use_same_model: bool = False
    gen_model: ModelConfig = ModelConfig()
    extr_model: ModelConfig = ModelConfig()

    output_dir: Path = _PROJECT_ROOT / "output"

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        v = v.expanduser().resolve()
        if v.exists() and not v.is_dir():
            raise ValueError(f"output_dir already exists as a file: {v}")
        return v

    @model_validator(mode="after")
    def sync_extr_model(self):
        if self.use_same_model:
            self.extr_model = self.gen_model.model_copy()
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
