from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from auto_schema_data_extraction.agents.extraction_agent import (
    build_extraction_agent,
    extract_from_document,
)
from auto_schema_data_extraction.config import ExtractionMode, LLModelConfig
from auto_schema_data_extraction.documents.loader import load_document
from auto_schema_data_extraction.documents.models import ExtractedText
from auto_schema_data_extraction.models.factory import build_model as build_llm_model
from auto_schema_data_extraction.schema.builder import build_model as build_output_model
from auto_schema_data_extraction.schema.meta_models import TemplateSpec


@dataclass(frozen=True, slots=True)
class ExtractionResult[OutputModelT: BaseModel]:
    data: OutputModelT
    partial: bool = False


async def run_extraction(
    document_path: Path,
    spec: TemplateSpec,
    *,
    model_config: LLModelConfig,
    extraction_mode: ExtractionMode,
) -> ExtractionResult[BaseModel]:
    output_model = build_output_model(spec)
    model = build_llm_model(model_config)
    agent = build_extraction_agent(model, output_model)

    content = load_document(document_path, mode=extraction_mode)

    if isinstance(content, ExtractedText):
        prompt_content, partial = content.text, content.partial
    else:
        prompt_content, partial = content, False

    result = await extract_from_document(prompt_content, agent=agent)

    return ExtractionResult(data=result.output, partial=partial)
