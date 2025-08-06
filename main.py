from fastapi import FastAPI
from api.routes import router as api_router

app = FastAPI(title="Agente IA TEA")

app.include_router(api_router)