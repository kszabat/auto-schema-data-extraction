from pathlib import Path


class DocumentLoadError(Exception):
    """Base class for document loading errors."""


class DocumentNotFoundError(DocumentLoadError):
    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Document not found: {path}")


class UnsupportedFileTypeError(DocumentLoadError):
    def __init__(self, path: Path, hint: str | None = None) -> None:
        self.path = path
        message = f"Unsupported file type: {path.suffix!r} ({path})."
        if hint:
            message += f" {hint}"
        super().__init__(message)


class DocumentConversionError(DocumentLoadError):
    """Raised when docling fails to convert a document."""

    def __init__(self, path: Path, errors: list[str]) -> None:
        self.path = path
        self.errors = errors
        details = "; ".join(errors) if errors else "unknown error"
        super().__init__(f"Failed to convert {path}: {details}")
