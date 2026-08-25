from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PresentationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    audience: str = Field(min_length=1, max_length=500)
    objective: str = Field(min_length=1, max_length=1_000)
    max_slides: int = Field(default=10, ge=1, le=30)
    financial_data: dict[str, Any] | list[Any]

    @field_validator("financial_data")
    @classmethod
    def financial_data_must_not_be_empty(
        cls, value: dict[str, Any] | list[Any]
    ) -> dict[str, Any] | list[Any]:
        if not value:
            raise ValueError("financial_data must not be empty")
        return value


class VisualSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["chart", "table", "metric", "timeline", "none"]
    title: str = Field(max_length=200)
    description: str = Field(max_length=1_000)


class SlideContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    key_message: str = Field(min_length=1, max_length=500)
    bullets: list[str] = Field(min_length=1, max_length=6)
    speaker_notes: str = Field(max_length=2_000)
    visual: VisualSuggestion
    source_references: list[str] = Field(default_factory=list, max_length=12)


class PresentationContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deck_title: str = Field(min_length=1, max_length=200)
    deck_subtitle: str = Field(max_length=300)
    executive_summary: str = Field(min_length=1, max_length=2_000)
    slides: list[SlideContent] = Field(min_length=1, max_length=30)
    disclaimer: str = Field(max_length=1_000)
