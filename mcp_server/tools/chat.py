"""Ferramentas MCP para Chat RAG com contexto de alunos."""
from mcp.server.fastmcp import FastMCP
from mcp_server.context import (
    get_chat_repo,
    get_gemini,
    get_rag_service,
    get_prompt_repo,
    get_ai_usage_repo,
    get_anonymization_service,
)
from infrastructure.services.anonymization_service import deanonymize

# ID de serviço usado para operações feitas pelo agente MCP
_MCP_SERVICE_USER_ID = "mcp-agent"
_MCP_SERVICE_USERNAME = "Agente MCP"
_MCP_SERVICE_ROLE = "admin"


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def enviar_mensagem_rag(
        aluno_id: str,
        mensagem: str,
        sessao_id: str | None = None,
        fontes: list[str] | None = None,
        data_de: str | None = None,
        data_ate: str | None = None,
    ) -> dict:
        """
        Envia uma mensagem ao chat RAG e recebe uma resposta contextualizada sobre o aluno.
        O sistema busca no histórico de diários, estudos de caso e PDIs do aluno para
        construir um contexto anonimizado antes de consultar a IA.

        aluno_id: ID do aluno sobre o qual se quer consultar.
        mensagem: pergunta ou instrução para o agente de IA.
        sessao_id: ID de sessão existente para continuar uma conversa (opcional).
        fontes: lista de fontes a usar. Opções: 'diary', 'case_study', 'pei'.
                Se omitido, usa todas as fontes disponíveis.
        data_de / data_ate: filtra diários por período (formato YYYY-MM-DD).

        Retorna session_id, resposta da IA e índice da mensagem na sessão.
        """
        chat_repo = get_chat_repo()
        gemini = get_gemini()
        rag = get_rag_service()
        prompt_repo = get_prompt_repo()
        usage_repo = get_ai_usage_repo()
        anon_svc = get_anonymization_service()

        # Obter ou criar sessão
        if sessao_id:
            sessao = await chat_repo.get_session(sessao_id)
            if not sessao:
                return {"erro": "Sessão não encontrada", "sessao_id": sessao_id}
        else:
            nova_sessao = await chat_repo.create_session(
                user_id=_MCP_SERVICE_USER_ID,
                username=_MCP_SERVICE_USERNAME,
                role=_MCP_SERVICE_ROLE,
                student_id=aluno_id,
            )
            sessao_id = nova_sessao["id"]

        # Construir contexto anonimizado
        anon_context, deanon_map = await anon_svc.build_context(
            aluno_id,
            sources=fontes,
            diary_date_from=data_de,
            diary_date_to=data_ate,
        )

        if not anon_context.strip():
            return {
                "erro": "Sem dados suficientes",
                "detail": "O aluno não possui registros de diário ou estudo de caso disponíveis para consulta.",
                "sessao_id": sessao_id,
            }

        # Contexto RAG semântico
        rag_context = await rag.build_rag_context(
            query=mensagem,
            student_id=aluno_id,
            limit=8,
            sources=fontes,
        )

        # Histórico de mensagens anteriores da sessão
        historico = await chat_repo.list_messages(sessao_id)
        historico_formatado = "\n".join(
            f"{'Usuário' if m['role'] == 'user' else 'Assistente'}: {m['content']}"
            for m in historico[-10:]  # últimas 10 mensagens
        )

        prompt_data = await prompt_repo.get_active("chat")
        system_instruction = prompt_data["content"] if prompt_data else ""

        prompt = f"""Você está analisando dados anonimizados de um aluno com TEA.
Os identificadores no contexto são UUIDs — não representam nomes reais.

=== CONTEXTO DO ALUNO (ANONIMIZADO) ===
{anon_context}

=== REGISTROS SIMILARES (RAG) ===
{rag_context}

=== HISTÓRICO DA CONVERSA ===
{historico_formatado}

=== PERGUNTA DO USUÁRIO ===
{mensagem}

Responda com base nos dados fornecidos."""

        try:
            raw_resposta, usage = gemini.generate_text_tracked(
                prompt=prompt,
                system_instruction=system_instruction,
            )
            await usage_repo.log(
                model=usage.model,
                operation="chat_rag",
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens,
                duration_ms=usage.duration_ms,
                user_id=_MCP_SERVICE_USER_ID,
            )
        except Exception as exc:
            return {"erro": "Falha ao gerar resposta", "detail": str(exc), "sessao_id": sessao_id}

        resposta = deanonymize(raw_resposta, deanon_map)

        # Salvar mensagens na sessão
        await chat_repo.add_message(
            sessao_id, role="user", content=mensagem,
            user_id=_MCP_SERVICE_USER_ID, username=_MCP_SERVICE_USERNAME,
        )
        await chat_repo.add_message(
            sessao_id, role="assistant", content=resposta,
            user_id=_MCP_SERVICE_USER_ID, username="Gemini",
        )

        return {
            "sessao_id": sessao_id,
            "resposta": resposta,
            "total_mensagens": len(historico) + 2,
        }

    @mcp.tool()
    async def listar_sessoes_chat(aluno_id: str | None = None) -> list[dict]:
        """
        Lista as sessões de chat do agente MCP.
        Se aluno_id for fornecido, filtra as sessões daquele aluno.
        Retorna id, student_id, title, created_at e contagem de mensagens.
        """
        sessoes = await get_chat_repo().list_sessions(
            user_id=_MCP_SERVICE_USER_ID,
            student_id=aluno_id,
        )
        return sessoes

    @mcp.tool()
    async def obter_mensagens_chat(sessao_id: str) -> list[dict]:
        """
        Retorna todas as mensagens de uma sessão de chat pelo seu ID.
        Cada mensagem contém role ('user' ou 'assistant'), content e index.
        """
        mensagens = await get_chat_repo().list_messages(sessao_id)
        if not mensagens and not await get_chat_repo().get_session(sessao_id):
            return [{"erro": "Sessão não encontrada", "sessao_id": sessao_id}]
        return mensagens

    @mcp.tool()
    async def deletar_sessao_chat(sessao_id: str) -> dict:
        """
        Remove uma sessão de chat e todas as suas mensagens pelo seu ID.
        """
        removido = await get_chat_repo().delete_session(sessao_id)
        if not removido:
            return {"erro": "Sessão não encontrada", "sessao_id": sessao_id}
        return {"status": "removido", "sessao_id": sessao_id}
