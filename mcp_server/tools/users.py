"""Ferramentas MCP para gestão de usuários (operações administrativas)."""
from mcp.server.fastmcp import FastMCP
from mcp_server.context import get_user_repo

# Perfis válidos no sistema
_PERFIS_VALIDOS = {"admin", "secretaria", "coordenacao", "professor", "viewer", "parent", "therapist"}


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def listar_usuarios(perfil: str | None = None) -> list[dict]:
        """
        Lista os usuários cadastrados na plataforma.
        perfil filtra por tipo de usuário. Valores válidos:
          admin, secretaria, coordenacao, professor, viewer, parent, therapist.
        Se omitido, retorna todos os usuários.
        Retorna id, full_name, email, role, is_active e created_at.
        """
        if perfil:
            return await get_user_repo().list_by_role(perfil)
        return await get_user_repo().get_all()

    @mcp.tool()
    async def obter_usuario(usuario_id: str) -> dict:
        """
        Retorna os dados de um usuário pelo seu ID.
        """
        usuario = await get_user_repo().get_by_id(usuario_id)
        if not usuario:
            return {"erro": "Usuário não encontrado", "usuario_id": usuario_id}
        return usuario

    @mcp.tool()
    async def atualizar_perfil_usuario(usuario_id: str, perfil: str) -> dict:
        """
        Atualiza o perfil (role) de um usuário.
        perfil deve ser um dos valores válidos:
          admin, secretaria, coordenacao, professor, viewer, parent, therapist.
        ATENÇÃO: Operação administrativa — alterar perfis afeta as permissões do usuário.
        """
        if perfil not in _PERFIS_VALIDOS:
            return {
                "erro": "Perfil inválido",
                "perfis_validos": sorted(_PERFIS_VALIDOS),
                "perfil_fornecido": perfil,
            }

        resultado = await get_user_repo().update_role(usuario_id, perfil)
        if not resultado:
            return {"erro": "Usuário não encontrado", "usuario_id": usuario_id}
        return {"status": "atualizado", "usuario_id": usuario_id, "novo_perfil": perfil}

    @mcp.tool()
    async def listar_municipios() -> list[dict]:
        """
        Lista os municípios cadastrados na plataforma.
        Retorna id e name de cada município.
        """
        from mcp_server.context import get_municipality_repo
        return await get_municipality_repo().list_all()
