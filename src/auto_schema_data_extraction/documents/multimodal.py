from pathlib import Path

from pydantic_ai import BinaryContent

from auto_schema_data_extraction.documents.exceptions import (
    DocumentNotFoundError,
    UnsupportedFileTypeError,
)

_SUPPORTED_MEDIA_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def load_binary_content(path: Path) -> BinaryContent:
    if not path.exists():
        raise DocumentNotFoundError(path)

    media_type = _SUPPORTED_MEDIA_TYPES.get(path.suffix.lower())
    if media_type is None:
        raise UnsupportedFileTypeError(
            path,
            hint=f"Multimodal mode does not support files with the extension '{path.suffix}'. Supported extensions are: {', '.join(_SUPPORTED_MEDIA_TYPES.keys())}. Try using the text mode instead.",
        )

    return BinaryContent(data=path.read_bytes(), media_type=media_type)
