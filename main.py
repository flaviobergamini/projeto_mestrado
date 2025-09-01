from fastapi import FastAPI
from api import auth_routes, routes
from api.routes import router as api_router
from api.auth_routes import router as auth_router
from core.kernel.container import Container

container = Container()
container.config.database.url.from_env("DATABASE_URL")
container.wire(modules=[routes, auth_routes])

app = FastAPI(
    title="Agente IA TEA",
    version="1.0.0",
    description="API para o Mestrado"
)
app.container = container

app.include_router(api_router)
app.include_router(auth_router)


@app.get("/health", tags=["Health"])
def read_root():
    return {"status": "ok", "message": "TEA AI Agent API is running"}