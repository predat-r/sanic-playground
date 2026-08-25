from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from pydantic import ValidationError

from app.config import Settings
from app.presentations.prompts import SYSTEM_PROMPT, build_user_prompt
from app.presentations.schemas import PresentationContent, PresentationRequest


class PresentationGenerationError(RuntimeError):
    """Raised when presentation content cannot be generated safely."""


class OpenRouterPresentationClient:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.openrouter_model
        self._max_output_tokens = settings.max_output_tokens
        self._client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=settings.ai_timeout_seconds,
            default_headers=_build_optional_headers(settings),
        )

    async def generate(
        self, request: PresentationRequest
    ) -> PresentationContent:
        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(request)},
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=self._max_output_tokens,
            )
        except (APIConnectionError, APITimeoutError) as exc:
            raise PresentationGenerationError(
                "The AI provider could not be reached"
            ) from exc
        except APIStatusError as exc:
            raise PresentationGenerationError(
                f"The AI provider returned status {exc.status_code}"
            ) from exc

        if not completion.choices:
            raise PresentationGenerationError("The AI provider returned no choices")

        choice = completion.choices[0]
        finish_reason = choice.finish_reason
        content = choice.message.content
        if not isinstance(content, str) or not content.strip():
            raise PresentationGenerationError("The AI provider returned no content")

        try:
            presentation = PresentationContent.model_validate_json(content)
        except ValidationError as exc:
            if finish_reason == "length":
                raise PresentationGenerationError(
                    "The AI provider truncated its response at the output limit"
                ) from exc
            raise PresentationGenerationError(
                "The AI provider returned invalid presentation content"
            ) from exc

        if len(presentation.slides) > request.max_slides:
            raise PresentationGenerationError(
                "The AI provider exceeded the requested slide limit"
            )

        return presentation


def _build_optional_headers(settings: Settings) -> dict[str, str]:
    headers: dict[str, str] = {}
    if settings.openrouter_http_referer:
        headers["HTTP-Referer"] = settings.openrouter_http_referer
    if settings.openrouter_app_title:
        headers["X-OpenRouter-Title"] = settings.openrouter_app_title
    return headers
