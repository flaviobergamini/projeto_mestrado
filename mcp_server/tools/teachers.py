"""Ferramentas MCP para gestão de professores."""
from mcp.server.fastmcp import FastMCP
from mcp_server.context import get_teacher_repo


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def listar_professores(escola_id: str | None = None) -> list[dict]:
        """
        Lista todos os professores cadastrados.
        Parâmetro opcional escola_id filtra por escola específica.
        Retorna id, name, email, school_id e school_name.
        """
        professores = await get_teacher_repo().list_all()
        if escola_id:
            professores = [p for p in professores if p.get("school_id") == escola_id]
        return professores

    @mcp.tool()
    async def obter_professor(professor_id: str) -> dict:
        """
        Retorna os dados completos de um professor pelo seu ID.
        """
        professor = await get_teacher_repo().get_by_id(professor_id)
        if not professor:
            return {"erro": "Professor não encontrado", "professor_id": professor_id}
        return professor

    @mcp.tool()
    async def criar_professor(
        nome: str,
        email: str | None = None,
        escola_id: str | None = None,
        telefone: str | None = None,
    ) -> dict:
        """
        Cria um novo professor na plataforma.
        Retorna o professor criado com seu ID gerado.
        """
        data = {
            "name": nome,
            "email": email,
            "school_id": escola_id,
            "phone": telefone,
        }
        return await get_teacher_repo().create(data)

    @mcp.tool()
    async def atualizar_professor(
        professor_id: str,
        nome: str | None = None,
        email: str | None = None,
        escola_id: str | None = None,
        telefone: str | None = None,
    ) -> dict:
        """
        Atualiza os dados de um professor existente.
        Apenas os campos fornecidos (não nulos) são alterados.
        """
        data: dict = {}
        if nome is not None:
            data["name"] = nome
        if email is not None:
            data["email"] = email
        if escola_id is not None:
            data["school_id"] = escola_id
        if telefone is not None:
            data["phone"] = telefone

        resultado = await get_teacher_repo().update(professor_id, data)
        if not resultado:
            return {"erro": "Professor não encontrado", "professor_id": professor_id}
        return resultado

    @mcp.tool()
    async def deletar_professor(professor_id: str) -> dict:
        """
        Remove (soft delete) um professor pelo seu ID.
        """
        removido = await get_teacher_repo().delete(professor_id)
        if not removido:
            return {"erro": "Professor não encontrado", "professor_id": professor_id}
        return {"status": "removido", "professor_id": professor_id}
