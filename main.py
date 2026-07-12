from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import (
    auth_routes, student_routes, diary_routes, pdi_routes,
    school_routes, teacher_routes, case_study_routes,
    chat_routes, prompt_routes, pei_gen_routes,
    municipality_routes, admin_routes, vinculos_routes,
)
from api.auth_routes import router as auth_router
from api.student_routes import router as student_router
from api.diary_routes import router as diary_router
from api.pdi_routes import router as pdi_router
from api.school_routes import router as school_router
from api.teacher_routes import router as teacher_router
from api.case_study_routes import router as case_study_router
from api.chat_routes import router as chat_router
from api.prompt_routes import router as prompt_router
from api.pei_gen_routes import router as pei_gen_router
from api.municipality_routes import router as municipality_router
from api.admin_routes import router as admin_router
from api import ai_usage_routes
from api.ai_usage_routes import router as ai_usage_router
from api import vinculos_routes
from api.vinculos_routes import router as vinculos_router
from api.middleware.audit_middleware import AuditMiddleware
from core.kernel.container import Container

container = Container()
container.config.database.url.from_env("DATABASE_URL")
container.wire(modules=[
    auth_routes, student_routes, diary_routes, pdi_routes,
    school_routes, teacher_routes, case_study_routes,
    chat_routes, prompt_routes, pei_gen_routes,
    municipality_routes, admin_routes, ai_usage_routes, vinculos_routes,
])

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

# Audit middleware runs after CORS
app.add_middleware(AuditMiddleware, database=container.database())

app.container = container
app.include_router(auth_router)
app.include_router(student_router)
app.include_router(diary_router)
app.include_router(pdi_router)
app.include_router(school_router)
app.include_router(teacher_router)
app.include_router(case_study_router)
app.include_router(chat_router)
app.include_router(prompt_router)
app.include_router(pei_gen_router)
app.include_router(municipality_router)
app.include_router(admin_router)
app.include_router(ai_usage_router)
app.include_router(vinculos_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "TEA AI Agent API is running"}
