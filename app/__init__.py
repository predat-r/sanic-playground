from sanic import Sanic
from sanic.response import text

from app.config import Settings
from app.infrastructure.openrouter import OpenRouterPresentationClient
from app.presentations.routes import presentation_blueprint


def create_app() -> Sanic:
    settings = Settings.from_environment()
    app = Sanic("FinancialPresentationAPI")
    app.config.REQUEST_MAX_SIZE = settings.max_input_bytes
    app.ctx.settings = settings
    app.ctx.presentation_client = OpenRouterPresentationClient(settings)
    app.blueprint(presentation_blueprint)

    @app.get("/")
    async def hello_world(request):
        return text("Hello, world!")

    return app
