"""Ferramentas MCP para Plano de Desenvolvimento Individual (PDI)."""
from mcp.server.fastmcp import FastMCP
from mcp_server.context import get_pdi_repo


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def listar_pdis() -> list[dict]:
        """
        Lista todos os PDIs cadastrados na plataforma, ordenados pelo mais recente.
        Retorna id, student_id, student_name, grade, class_name, diagnosis, created_at.
        """
        return await get_pdi_repo().list_all()

    @mcp.tool()
    async def listar_pdis_por_aluno(aluno_id: str) -> list[dict]:
        """
        Lista todos os PDIs de um aluno específico.
        Inclui as disciplinas por trimestre (trimester_subjects) com habilidades e adaptações.
        """
        todos = await get_pdi_repo().list_all()
        return [p for p in todos if p.get("student_id") == aluno_id]

    @mcp.tool()
    async def obter_pdi(pdi_id: str) -> dict:
        """
        Retorna os dados completos de um PDI pelo seu ID, incluindo todas as
        disciplinas e trimestres com habilidades, adaptações e aprendizados.
        """
        pdi = await get_pdi_repo().get_by_id(pdi_id)
        if not pdi:
            return {"erro": "PDI não encontrado", "pdi_id": pdi_id}
        return pdi

    @mcp.tool()
    async def criar_pdi(
        aluno_id: str,
        turma: str | None = None,
        diagnostico: str | None = None,
        nome_professor: str | None = None,
    ) -> dict:
        """
        Cria um novo PDI para um aluno.
        turma, diagnostico e nome_professor são opcionais — se não fornecidos,
        serão herdados do cadastro do aluno.
        Para adicionar disciplinas por trimestre, use atualizar_disciplinas_pdi após criar.
        """
        data = {
            "student_id": aluno_id,
            "class_name": turma,
            "diagnosis": diagnostico,
            "teacher_name": nome_professor,
        }
        return await get_pdi_repo().create(data)

    @mcp.tool()
    async def atualizar_disciplinas_pdi(
        pdi_id: str,
        disciplinas: list[dict],
    ) -> dict:
        """
        Atualiza as disciplinas por trimestre de um PDI.
        disciplinas é uma lista de objetos com os campos:
          - trimester: int (1, 2 ou 3)
          - subject: str (nome da disciplina)
          - skills: str (habilidades a desenvolver)
          - adaptations: str (adaptações necessárias)
          - learnings: str (aprendizados registrados)
        Substitui todas as disciplinas existentes do PDI.
        """
        resultado = await get_pdi_repo().upsert_subjects(pdi_id, disciplinas)
        if not resultado:
            return {"erro": "PDI não encontrado", "pdi_id": pdi_id}
        return resultado

    @mcp.tool()
    async def deletar_pdi(pdi_id: str) -> dict:
        """
        Remove (soft delete) um PDI pelo seu ID.
        """
        removido = await get_pdi_repo().delete(pdi_id)
        if not removido:
            return {"erro": "PDI não encontrado", "pdi_id": pdi_id}
        return {"status": "removido", "pdi_id": pdi_id}
