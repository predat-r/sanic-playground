import logging

from pydantic import ValidationError
from sanic import Blueprint, Request
from sanic.response import HTTPResponse, json

from app.infrastructure.openrouter import PresentationGenerationError
from app.presentations.schemas import PresentationRequest


logger = logging.getLogger(__name__)


presentation_blueprint = Blueprint(
    "presentations",
    url_prefix="/api/v1/presentations",
)


@presentation_blueprint.post("/content")
async def generate_presentation_content(request: Request) -> HTTPResponse:
    if len(request.body) > request.app.ctx.settings.max_input_bytes:
        return _error_response("Request body is too large", status=413)

    try:
        payload = PresentationRequest.model_validate(request.json)
    except ValidationError as exc:
        return json(
            {
                "error": "Invalid request body",
                "details": exc.errors(include_input=False, include_url=False),
            },
            status=400,
        )

    try:
        content = await request.app.ctx.presentation_client.generate(payload)
    except PresentationGenerationError as exc:
        logger.warning("Presentation generation failed: %s", exc)
        return _error_response("Presentation generation failed", status=502)

    return json(content.model_dump(mode="json"))


def _error_response(message: str, status: int) -> HTTPResponse:
    return json({"error": message}, status=status)
