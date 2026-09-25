from pathlib import Path

from pydantic_ai import BinaryContent

from auto_schema_data_extraction.config import ExtractionMode
from auto_schema_data_extraction.documents.models import ExtractedText
from auto_schema_data_extraction.documents.multimodal import load_binary_content
from auto_schema_data_extraction.documents.text_extraction import extract_text


def load_document(path: Path, mode: ExtractionMode) -> ExtractedText | BinaryContent:
    match mode:
        case "text":
            return extract_text(path)
        case "multimodal":
            return load_binary_content(path)
        case _:
            raise ValueError(f"Unknown extraction mode: {mode!r}")
