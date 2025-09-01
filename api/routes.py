from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from core.kernel.container import Container
from core.use_case.diary_embedding_use_case import DiaryEmbeddingUseCase
from core.use_case.query_diary_use_case import QueryDiaryUseCase
from domain.schema import RAGRequest
from dependency_injector.wiring import inject, Provide

router = APIRouter()

@router.post("/rag")
@inject
async def rag(
    payload: RAGRequest, 
    use_case: DiaryEmbeddingUseCase = Depends(
        Provide[Container.diary_embedding_use_case]
    ),
):
    try:
        await use_case.execute(payload.pergunta, payload.model)
        return JSONResponse(status_code=200)
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)
    
@router.post("/chat")
@inject
async def chat(
    payload: RAGRequest, 
    use_case: QueryDiaryUseCase = Depends(
        Provide[Container.query_diary_use_case]
    ),
):
    try:
        response = await use_case.execute(payload.pergunta, payload.model)
        return JSONResponse(content={"value": response}, status_code=200)
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)