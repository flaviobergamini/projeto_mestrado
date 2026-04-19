from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from core.use_case.generate_pei_use_case import GeneratePEIUseCase
from core.use_case.generate_pei_pdf_use_case import GeneratePEIPDFUseCase
from domain.schema import GeneratePEIRequest, GeneratePEIPDFRequest
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK
from dependency_injector.wiring import inject, Provide

router = APIRouter(prefix="/pei", tags=["PEI"], dependencies=[Depends(require_roles("admin", "secretary", "school_admin", "teacher"))])


@router.post("/generate", response_class=JSONResponse)
@inject
async def generate_pei(
    request: GeneratePEIRequest,
    use_case: GeneratePEIUseCase = Depends(
        Provide[Container.generate_pei_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Gera um PEI em formato JSON e salva no banco de dados com embeddings para RAG.
    O JSON será usado posteriormente para gerar o PDF através da rota /pei/generate-pdf.

    Args:
        request: Contém o beneficiary_id

    Returns:
        JSON com pei_id, beneficiary_id, generated_at e mensagem de sucesso
    """
    try:
        prompt_file_path = "prompts/PEI_prompt_json.txt"

        response = await use_case.execute(
            beneficiary_id=request.beneficiary_id,
            user_id=user_id,
            prompt_file_path=prompt_file_path
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

        return JSONResponse(
            status_code=HTTP_201_CREATED,
            content=response.value
        )

    except Exception as e:
        print(e)
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


@router.post("/generate-pdf", response_class=Response)
@inject
async def generate_pei_pdf(
    request: GeneratePEIPDFRequest,
    use_case: GeneratePEIPDFUseCase = Depends(
        Provide[Container.generate_pei_pdf_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Gera um PDF do PEI a partir do JSON salvo no banco de dados.
    Usa RAG para buscar informações relevantes e gera um documento formatado em Markdown/PDF.

    Args:
        request: Contém o pei_id

    Returns:
        Arquivo PDF para download
    """
    try:
        prompt_file_path = "prompts/PEI_prompt_pdf.txt"

        response = await use_case.execute(
            pei_id=request.pei_id,
            user_id=user_id,
            prompt_file_path=prompt_file_path,
            return_pdf_buffer=True,
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
            status_code=HTTP_200_OK
        )

    except Exception as e:
        print(e)
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)
