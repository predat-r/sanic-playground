import logging
import re

from pydantic import ValidationError
from sanic import Blueprint, Request
from sanic.response import HTTPResponse, json, raw

from app.infrastructure.openrouter import PresentationGenerationError
from app.presentations.pptx_renderer import PptxRenderError, PptxRenderer
from app.presentations.schemas import PresentationRequest


logger = logging.getLogger(__name__)


presentation_blueprint = Blueprint(
    "presentations",
    url_prefix="/api/v1/presentations",
)


@presentation_blueprint.post("/content")
async def generate_presentation_content(request: Request) -> HTTPResponse:
    payload, validation_error = _parse_request(request)
    if validation_error:
        return validation_error

    try:
        content = await request.app.ctx.presentation_client.generate(payload)
    except PresentationGenerationError as exc:
        logger.warning("Presentation generation failed: %s", exc)
        return _error_response("Presentation generation failed", status=502)

    return json(content.model_dump(mode="json"))


@presentation_blueprint.post("/pptx")
async def generate_presentation_pptx(request: Request) -> HTTPResponse:
    payload, validation_error = _parse_request(request)
    if validation_error:
        return validation_error

    try:
        content = await request.app.ctx.presentation_client.generate(payload)
        renderer = PptxRenderer()
        pptx_bytes = await renderer.render(content)
    except (PresentationGenerationError, PptxRenderError) as exc:
        logger.warning("PPTX generation failed: %s", exc)
        return _error_response("PPTX generation failed", status=502)

    filename = f"{_safe_filename(content.deck_title)}.pptx"
    return raw(
        pptx_bytes,
        content_type=(
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _parse_request(
    request: Request,
) -> tuple[PresentationRequest | None, HTTPResponse | None]:
    if len(request.body) > request.app.ctx.settings.max_input_bytes:
        return None, _error_response("Request body is too large", status=413)

    try:
        return PresentationRequest.model_validate(request.json), None
    except ValidationError as exc:
        return None, json(
            {
                "error": "Invalid request body",
                "details": exc.errors(include_input=False, include_url=False),
            },
            status=400,
        )


def _safe_filename(title: str) -> str:
    filename = re.sub(r"[^A-Za-z0-9._-]+", "-", title).strip("-.")
    return filename[:100] or "financial-presentation"


def _error_response(message: str, status: int) -> HTTPResponse:
    return json({"error": message}, status=status)
