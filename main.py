from fastapi import FastAPI
from api import auth_routes, diary_routes, school_routes, health_plan_routes, beneficiary_routes, clinic_routes, professional_routes, beneficiary_clinic_routes, autismia_routes, evaluation_routes, family_reunion_routes, school_feedback_routes, supervisor_routes, therapeutic_plan_routes, therapeutic_sessions_routes
from api.diary_routes import router as diary_router
from api.auth_routes import router as auth_router
from api.school_routes import router as school_router
from api.health_plan_routes import router as health_plan_router
from api.beneficiary_routes import router as beneficiary_router
from api.clinic_routes import router as clinic_router
from api.professional_routes import router as professional_router
from api.beneficiary_clinic_routes import router as beneficiary_clinic_router
from api.autismia_routes import router as autismia_router
from api.evaluation_routes import router as evaluation_router
from api.family_reunion_routes import router as family_reunion_router
from api.school_feedback_routes import router as school_feedback_router
from api.supervisor_routes import router as supervisor_router
from api.therapeutic_plan_routes import router as therapeutic_plan_router
from api.therapeutic_sessions_routes import router as therapeutic_sessions_router
from core.kernel.container import Container

container = Container()
container.config.database.url.from_env("DATABASE_URL")
container.wire(modules=[diary_routes, auth_routes, school_routes, health_plan_routes, beneficiary_routes, clinic_routes, professional_routes, beneficiary_clinic_routes, autismia_routes, evaluation_routes, family_reunion_routes, school_feedback_routes, supervisor_routes, therapeutic_plan_routes, therapeutic_sessions_routes])

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
app.include_router(beneficiary_clinic_router)
app.include_router(autismia_router)
app.include_router(evaluation_router)
app.include_router(family_reunion_router)
app.include_router(school_feedback_router)
app.include_router(supervisor_router)
app.include_router(therapeutic_plan_router)
app.include_router(therapeutic_sessions_router)


@app.get("/health", tags=["Health"])
def read_root():
    return {"status": "ok", "message": "TEA AI Agent API is running"}