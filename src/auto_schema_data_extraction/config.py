from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_and_ensure_dir(v: Path) -> Path:
    v = v.expanduser().resolve()
    if v.exists() and not v.is_dir():
        raise ValueError(f"{v} already exists as a file, expected a directory.")
    v.mkdir(parents=True, exist_ok=True)
    return v


class LLMModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "google:gemini-3-flash-preview"
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
    schema_model: LLMModelConfig = Field(default_factory=LLMModelConfig)
    extraction_model: LLMModelConfig = Field(default_factory=LLMModelConfig)

    output_dir: Path = _PROJECT_ROOT / "output"
    templates_dir: Path = _PROJECT_ROOT / "templates"

    @field_validator("output_dir", "templates_dir")
    @classmethod
    def validate_dirs(cls, v: Path) -> Path:
        return _resolve_and_ensure_dir(v)

    @model_validator(mode="after")
    def sync_extr_model(self):
        if self.use_same_model:
            self.extraction_model = self.schema_model.model_copy()
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


if __name__ == "__main__":
    settings = get_settings()
    print(settings.model_dump_json(indent=2))
