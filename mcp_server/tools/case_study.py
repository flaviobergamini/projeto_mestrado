"""Ferramentas MCP para Estudos de Caso."""
from mcp.server.fastmcp import FastMCP
from mcp_server.context import get_case_study_repo


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def listar_estudos_caso() -> list[dict]:
        """
        Lista todos os estudos de caso cadastrados, ordenados do mais recente.
        Retorna id, student_id, student_name, submitted_by, submitted_at e um resumo das respostas.
        """
        return await get_case_study_repo().list_all()

    @mcp.tool()
    async def listar_estudos_caso_por_aluno(aluno_id: str) -> list[dict]:
        """
        Lista todos os estudos de caso de um aluno específico.
        """
        todos = await get_case_study_repo().list_all()
        return [c for c in todos if c.get("student_id") == aluno_id]

    @mcp.tool()
    async def obter_estudo_caso(estudo_id: str) -> dict:
        """
        Retorna os dados completos de um estudo de caso pelo seu ID.
        Inclui todas as respostas do formulário (campo 'answers').
        """
        estudo = await get_case_study_repo().get_by_id(estudo_id)
        if not estudo:
            return {"erro": "Estudo de caso não encontrado", "estudo_id": estudo_id}
        return estudo

    @mcp.tool()
    async def criar_estudo_caso(
        aluno_id: str | None = None,
        enviado_por: str | None = None,
        respostas: dict | None = None,
    ) -> dict:
        """
        Cria um novo estudo de caso.
        aluno_id vincula o estudo a um aluno cadastrado.
        enviado_por identifica o responsável pelo preenchimento.
        respostas é um dicionário livre com as respostas do formulário de estudo de caso.
        """
        data = {
            "student_id": aluno_id,
            "submitted_by": enviado_por,
            "answers": respostas or {},
        }
        return await get_case_study_repo().create(data)

    @mcp.tool()
    async def atualizar_estudo_caso(
        estudo_id: str,
        respostas: dict | None = None,
        enviado_por: str | None = None,
    ) -> dict:
        """
        Atualiza os dados de um estudo de caso existente.
        """
        data: dict = {}
        if respostas is not None:
            data["answers"] = respostas
        if enviado_por is not None:
            data["submitted_by"] = enviado_por

        resultado = await get_case_study_repo().update(estudo_id, data)
        if not resultado:
            return {"erro": "Estudo de caso não encontrado", "estudo_id": estudo_id}
        return resultado

    @mcp.tool()
    async def deletar_estudo_caso(estudo_id: str) -> dict:
        """
        Remove (soft delete) um estudo de caso pelo seu ID.
        """
        removido = await get_case_study_repo().delete(estudo_id)
        if not removido:
            return {"erro": "Estudo de caso não encontrado", "estudo_id": estudo_id}
        return {"status": "removido", "estudo_id": estudo_id}
