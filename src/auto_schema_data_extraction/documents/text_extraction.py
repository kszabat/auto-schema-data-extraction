from pathlib import Path

from docling.datamodel.base_models import ConversionStatus
from docling.document_converter import DocumentConverter

from auto_schema_data_extraction.documents.exceptions import (
    DocumentConversionError,
    DocumentNotFoundError,
)
from auto_schema_data_extraction.documents.models import ExtractedText

PLAIN_TEXT_SUFFIXES = {".txt", ".md"}

_converter = DocumentConverter()


def extract_text(path: Path) -> ExtractedText:
    if not path.exists():
        raise DocumentNotFoundError(path)

    if path.suffix.lower() in PLAIN_TEXT_SUFFIXES:
        return ExtractedText(
            text=path.read_text(encoding="utf-8"), source=path, partial=False
        )

    try:
        result = _converter.convert(path)
    except Exception as exc:
        raise DocumentConversionError(path, [str(exc)]) from exc

    if result.status == ConversionStatus.FAILURE:
        errors = [e.error_message for e in result.errors]
        raise DocumentConversionError(path, errors)

    return ExtractedText(
        text=result.document.export_to_markdown(),
        source=path,
        partial=result.status == ConversionStatus.PARTIAL_SUCCESS,
    )

