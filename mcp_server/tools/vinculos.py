"""Ferramentas MCP para vínculos professor-aluno."""
from mcp.server.fastmcp import FastMCP
from mcp_server.context import get_vinculos_repo, get_teacher_repo


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def listar_alunos_com_vinculos() -> list[dict]:
        """
        Lista todos os alunos com seus professores vinculados.
        Retorna uma lista com student_id, student_name, school_name e teachers (lista de professores).
        Útil para entender quais professores acompanham cada aluno.
        """
        return await get_vinculos_repo().list_students_with_links()

    @mcp.tool()
    async def listar_professores_vinculaveis() -> list[dict]:
        """
        Lista todos os professores disponíveis para vinculação com alunos.
        Retorna id, name, email e school_name de cada professor.
        """
        return await get_teacher_repo().list_all()

    @mcp.tool()
    async def definir_vinculos_aluno(
        aluno_id: str,
        professor_ids: list[str],
    ) -> dict:
        """
        Define os professores vinculados a um aluno.
        Esta operação substitui todos os vínculos anteriores do aluno.
        professor_ids: lista de IDs dos professores a vincular.
        Para desvincular todos os professores, passe uma lista vazia [].
        """
        ok = await get_vinculos_repo().set_student_teachers(aluno_id, professor_ids)
        if not ok:
            return {"erro": "Aluno não encontrado ou falha ao atualizar vínculos", "aluno_id": aluno_id}
        return {"status": "atualizado", "aluno_id": aluno_id, "professores_vinculados": len(professor_ids)}
