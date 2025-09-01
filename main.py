from fastapi import FastAPI
from api import routes
from api.routes import router as api_router
from core.kernel.container import Container

container = Container()
container.config.database.url.from_env("DATABASE_URL")
container.wire(modules=[routes])

app = FastAPI(title="Agente IA TEA")
app.container = container

app.include_router(api_router)