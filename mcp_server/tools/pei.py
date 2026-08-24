"""Ferramentas MCP para geração e gestão de PEIs (Plano Educacional Individualizado)."""
import asyncio
from mcp.server.fastmcp import FastMCP
from mcp_server.context import (
    get_student_repo,
    get_generated_pei_repo,
    get_gemini,
    get_rag_service,
    get_prompt_repo,
    get_ai_usage_repo,
    get_anonymization_service,
)
from infrastructure.services.anonymization_service import deanonymize

_MCP_SERVICE_USER_ID = "mcp-agent"


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def gerar_pei(
        aluno_id: str,
        fontes: list[str] | None = None,
        data_de: str | None = None,
        data_ate: str | None = None,
    ) -> dict:
        """
        Gera um Plano Educacional Individualizado (PEI) completo para um aluno usando IA (Gemini).
        O PEI é baseado no histórico de diários, estudos de caso e PDIs do aluno,
        que são anonimizados antes de serem enviados à IA.

        aluno_id: ID do aluno para o qual o PEI será gerado.
        fontes: lista de fontes de dados a incluir no contexto. Opções: 'diary', 'case_study', 'pei'.
                Se omitido, usa todas as fontes disponíveis.
        data_de / data_ate: filtra diários por período (formato YYYY-MM-DD).

        Retorna o PEI gerado em texto, o ID do PEI salvo e a data de geração.
        ATENÇÃO: Esta operação consome tokens da API Gemini.
        """
        student_repo = get_student_repo()
        gemini = get_gemini()
        rag = get_rag_service()
        prompt_repo = get_prompt_repo()
        pei_repo = get_generated_pei_repo()
        usage_repo = get_ai_usage_repo()
        anon_svc = get_anonymization_service()

        aluno = await student_repo.get_by_id(aluno_id)
        if not aluno:
            return {"erro": "Aluno não encontrado", "aluno_id": aluno_id}

        student_name = aluno.get("name", "")

        anon_context, deanon_map = await anon_svc.build_context(
            aluno_id,
            diary_limit=15,
            sources=fontes,
            diary_date_from=data_de,
            diary_date_to=data_ate,
        )

        if not anon_context.strip():
            return {
                "erro": "Dados insuficientes",
                "detail": "O aluno não possui registros de diário ou estudo de caso para gerar o PEI.",
            }

        rag_context = await rag.build_rag_context(
            query="perfil completo do aluno: comportamento, socialização, habilidades, dificuldades, histórico escolar, família",
            student_id=aluno_id,
            limit=10,
            sources=fontes,
        )

        prompt_data = await prompt_repo.get_active("pei")
        system_instruction = prompt_data["content"] if prompt_data else ""

        prompt = f"""Com base nos dados anonimizados abaixo, gere o PEI completo.
Os identificadores no contexto são chaves primárias (UUIDs) — não representam nomes reais.

=== CONTEXTO DO ALUNO (ANONIMIZADO) ===
{anon_context}

=== REGISTROS SIMILARES (RAG) ===
{rag_context}

Gere o Plano Educacional Individualizado (PEI) completo para este aluno."""

        try:
            raw_pei, usage = await asyncio.to_thread(
                gemini.generate_text_tracked,
                prompt=prompt,
                system_instruction=system_instruction,
            )
            await usage_repo.log(
                model=usage.model,
                operation="pei_generation",
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens,
                duration_ms=usage.duration_ms,
                user_id=_MCP_SERVICE_USER_ID,
            )
        except Exception as exc:
            return {"erro": "Falha ao gerar PEI", "detail": str(exc)}

        pei_text = deanonymize(raw_pei, deanon_map)

        salvo = await pei_repo.save(
            student_id=aluno_id,
            student_name=student_name,
            pei_text=pei_text,
            sources_used=fontes,
            generated_by=_MCP_SERVICE_USER_ID,
        )

        return {
            "id": salvo["id"],
            "aluno_id": aluno_id,
            "nome_aluno": student_name,
            "pei_texto": pei_text,
            "gerado_em": salvo.get("generated_at"),
        }

    @mcp.tool()
    async def listar_peis_salvos(aluno_id: str) -> list[dict]:
        """
        Lista todos os PEIs gerados por IA para um aluno específico.
        Retorna id, student_name, generated_at e o texto do PEI.
        """
        return await get_generated_pei_repo().list_by_student(aluno_id)

    @mcp.tool()
    async def obter_pei_salvo(pei_id: str) -> dict:
        """
        Retorna o texto completo de um PEI salvo pelo seu ID.
        """
        pei = await get_generated_pei_repo().get_by_id(pei_id)
        if not pei:
            return {"erro": "PEI não encontrado", "pei_id": pei_id}
        return pei

    @mcp.tool()
    async def deletar_pei_salvo(pei_id: str) -> dict:
        """
        Remove um PEI salvo pelo seu ID.
        """
        removido = await get_generated_pei_repo().delete(pei_id)
        if not removido:
            return {"erro": "PEI não encontrado", "pei_id": pei_id}
        return {"status": "removido", "pei_id": pei_id}
