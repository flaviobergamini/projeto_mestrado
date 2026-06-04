from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import auth_routes
from api.auth_routes import router as auth_router
from core.kernel.container import Container

container = Container()
container.config.database.url.from_env("DATABASE_URL")
container.wire(modules=[auth_routes])

app = FastAPI(
    title="Agente IA TEA",
    version="1.0.0",
    description="API para o Mestrado",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.container = container
app.include_router(auth_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "TEA AI Agent API is running"}
