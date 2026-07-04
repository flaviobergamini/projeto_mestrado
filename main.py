from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import auth_routes, student_routes, diary_routes, pdi_routes, school_routes, teacher_routes, case_study_routes, chat_routes
from api.auth_routes import router as auth_router
from api.student_routes import router as student_router
from api.diary_routes import router as diary_router
from api.pdi_routes import router as pdi_router
from api.school_routes import router as school_router
from api.teacher_routes import router as teacher_router
from api.case_study_routes import router as case_study_router
from api.chat_routes import router as chat_router
from core.kernel.container import Container

container = Container()
container.config.database.url.from_env("DATABASE_URL")
container.wire(modules=[auth_routes, student_routes, diary_routes, pdi_routes, school_routes, teacher_routes, case_study_routes, chat_routes])

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
app.include_router(student_router)
app.include_router(diary_router)
app.include_router(pdi_router)
app.include_router(school_router)
app.include_router(teacher_router)
app.include_router(case_study_router)
app.include_router(chat_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "TEA AI Agent API is running"}
