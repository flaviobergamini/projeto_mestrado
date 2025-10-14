from fastapi import FastAPI
from api import auth_routes, diary_routes, school_routes, health_plan_routes, beneficiary_routes, clinic_routes, professional_routes
from api.diary_routes import router as diary_router
from api.auth_routes import router as auth_router
from api.school_routes import router as school_router
from api.health_plan_routes import router as health_plan_router
from api.beneficiary_routes import router as beneficiary_router
from api.clinic_routes import router as clinic_router
from api.professional_routes import router as professional_router
from core.kernel.container import Container

container = Container()
container.config.database.url.from_env("DATABASE_URL")
container.wire(modules=[diary_routes, auth_routes, school_routes, health_plan_routes, beneficiary_routes, clinic_routes, professional_routes])

app = FastAPI(
    title="Agente IA TEA",
    version="1.0.0",
    description="API para o Mestrado"
)
app.container = container

app.include_router(diary_router)
app.include_router(auth_router)
app.include_router(school_router)
app.include_router(health_plan_router)
app.include_router(beneficiary_router)
app.include_router(clinic_router)
app.include_router(professional_router)


@app.get("/health", tags=["Health"])
def read_root():
    return {"status": "ok", "message": "TEA AI Agent API is running"}