from __future__ import annotations

import keyword
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

FieldType = Literal["str", "int", "float", "date", "bool", "list[str]"]


class FieldDefinition(BaseModel):
    """Definition of a single field to extract from a document."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description=(
            "Field name in snake_case, used as the attribute name on the "
            "resulting extracted object (e.g. 'invoice_number'). "
            "Should be a valid Python identifier and not a reserved keyword."
        )
    )
    type: FieldType = Field(
        description="Python type of the field's value.",
    )
    description: str = Field(
        description=(
            "Clear, unambiguous description of what to extract for this "
            "field - used later to guide extraction from a real document."
        )
    )
    required: bool = Field(
        default=True,
        description="If False, a missing value in the document becomes None instead of failing extraction.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v.isidentifier() or keyword.iskeyword(v):
            raise ValueError(
                f"Field name {v!r} must be a valid Python identifier and not a reserved keyword."
            )
        return v


class TemplateSpec(BaseModel):
    """Specification of a document-extraction template, generated from a user prompt."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description=(
            "Short, descriptive template name in snake_case (e.g. 'invoice', 'employment_contract'). "
            "Should be a valid Python identifier and not a reserved keyword."
        ),
    )
    fields: list[FieldDefinition] = Field(
        description="Fields to extract from the document.", min_length=1
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v.isidentifier() or keyword.iskeyword(v):
            raise ValueError(f"Template name {v!r} must be a valid Python identifier.")
        return v

    @model_validator(mode="after")
    def validate_unique_field_names(self) -> TemplateSpec:
        names = [f.name for f in self.fields]
        duplicates = {n for n in names if names.count(n) > 1}

        if duplicates:
            raise ValueError(f"Duplicate field names: {sorted(duplicates)}")
        return self
