from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from api.dependencies import get_current_user
from core.kernel.container import Container
from core.use_case.generate_pei_use_case import GeneratePEIUseCase
from domain.schema import GeneratePEIRequest
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR
from dependency_injector.wiring import inject, Provide

router = APIRouter(prefix="/pei", tags=["PEI"])


@router.post("/generate", response_class=Response)
@inject
async def generate_pei(
    request: GeneratePEIRequest,
    use_case: GeneratePEIUseCase = Depends(
        Provide[Container.generate_pei_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Gera um Plano Educacional Individualizado (PEI) em PDF para um beneficiário.

    Args:
        request: Contém o beneficiary_id
        prompt_file_path: Caminho do arquivo TXT no storage contendo o prompt para a IA

    Returns:
        JSON com pdf_path, pdf_url, beneficiary_id e generated_at
    """
    try:
        prompt_file_path = "prompts/PEI_prompt.txt"

        response = await use_case.execute(
            beneficiary_id=request.beneficiary_id,
            user_id=user_id,
            prompt_file_path=prompt_file_path,
            return_pdf_buffer=True
        )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )
    
        pdf_content = response.value['pdf_content']
        filename = response.value['filename'] 

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\"" 
            },
            status_code=HTTP_201_CREATED
        )
    
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)
