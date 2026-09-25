from pathlib import Path

from pydantic import ValidationError

from auto_schema_data_extraction.schema.meta_models import TemplateSpec


class TemplateStoreError(Exception):
    """Base class for template store errors."""


class TemplateNotFoundError(TemplateStoreError):
    def __init__(self, name: str, templates_dir: Path) -> None:
        self.name = name
        self.templates_dir = templates_dir
        super().__init__(f"Template {name!r} not found in {templates_dir}.")


class TemplateAlreadyExistsError(TemplateStoreError):
    def __init__(self, name: str, templates_dir: Path) -> None:
        self.name = name
        self.templates_dir = templates_dir
        super().__init__(
            f"Template {name!r} already exists in {templates_dir}. "
            "Pass overwrite=True to replace it."
        )


class TemplateCorruptedError(TemplateStoreError):
    def __init__(self, name: str, path: Path, cause: Exception) -> None:
        self.name = name
        self.path = path
        super().__init__(f"Template file {path} is corrupted or invalid: {cause}")


def _template_path(name: str, templates_dir: Path) -> Path:
    return templates_dir / f"{name}.json"


def save_template(
    spec: TemplateSpec, templates_dir: Path, *, overwrite: bool = False
) -> Path:
    templates_dir.mkdir(parents=True, exist_ok=True)
    path = _template_path(spec.name, templates_dir)

    if path.exists() and not overwrite:
        raise TemplateAlreadyExistsError(spec.name, templates_dir)

    path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_template(name: str, templates_dir: Path) -> TemplateSpec:
    path = _template_path(name, templates_dir)

    if not path.exists():
        raise TemplateNotFoundError(name, templates_dir)

    try:
        return TemplateSpec.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise TemplateCorruptedError(name, path, exc) from exc


def list_templates(templates_dir: Path) -> list[str]:
    if not templates_dir.exists():
        return []
    return sorted(p.stem for p in templates_dir.glob("*.json"))


def delete_template(name: str, templates_dir: Path) -> None:
    path = _template_path(name, templates_dir)

    if not path.exists():
        raise TemplateNotFoundError(name, templates_dir)

    path.unlink()
