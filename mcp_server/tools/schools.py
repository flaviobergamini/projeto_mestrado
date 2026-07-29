"""Ferramentas MCP para gestão de escolas."""
from mcp.server.fastmcp import FastMCP
from mcp_server.context import get_school_repo


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def listar_escolas() -> list[dict]:
        """
        Lista todas as escolas cadastradas na plataforma.
        Retorna id, name, municipality, address e contagem de alunos vinculados.
        """
        return await get_school_repo().list_all()

    @mcp.tool()
    async def obter_escola(escola_id: str) -> dict:
        """
        Retorna os dados completos de uma escola pelo seu ID.
        """
        escola = await get_school_repo().get_by_id(escola_id)
        if not escola:
            return {"erro": "Escola não encontrada", "escola_id": escola_id}
        return escola

    @mcp.tool()
    async def criar_escola(
        nome: str,
        municipio: str | None = None,
        endereco: str | None = None,
        telefone: str | None = None,
        email: str | None = None,
    ) -> dict:
        """
        Cria uma nova escola na plataforma.
        Retorna a escola criada com seu ID gerado.
        """
        data = {
            "name": nome,
            "municipality": municipio,
            "address": endereco,
            "phone": telefone,
            "email": email,
        }
        return await get_school_repo().create(data)

    @mcp.tool()
    async def atualizar_escola(
        escola_id: str,
        nome: str | None = None,
        municipio: str | None = None,
        endereco: str | None = None,
        telefone: str | None = None,
        email: str | None = None,
    ) -> dict:
        """
        Atualiza os dados de uma escola existente.
        Apenas os campos fornecidos (não nulos) são alterados.
        """
        data: dict = {}
        if nome is not None:
            data["name"] = nome
        if municipio is not None:
            data["municipality"] = municipio
        if endereco is not None:
            data["address"] = endereco
        if telefone is not None:
            data["phone"] = telefone
        if email is not None:
            data["email"] = email

        resultado = await get_school_repo().update(escola_id, data)
        if not resultado:
            return {"erro": "Escola não encontrada", "escola_id": escola_id}
        return resultado

    @mcp.tool()
    async def deletar_escola(escola_id: str) -> dict:
        """
        Remove (soft delete) uma escola pelo seu ID.
        """
        removido = await get_school_repo().delete(escola_id)
        if not removido:
            return {"erro": "Escola não encontrada", "escola_id": escola_id}
        return {"status": "removido", "escola_id": escola_id}
