"""Ferramentas MCP para gestão de alunos."""
from mcp.server.fastmcp import FastMCP
from mcp_server.context import get_student_repo


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def listar_alunos(escola_id: str | None = None) -> list[dict]:
        """
        Lista todos os alunos cadastrados na plataforma.
        Retorna nome, escola, diagnóstico, série, turma e responsáveis.
        Parâmetro opcional escola_id filtra por escola específica.
        """
        return await get_student_repo().list_all(school_id=escola_id)

    @mcp.tool()
    async def obter_aluno(aluno_id: str) -> dict:
        """
        Retorna os dados completos de um aluno pelo seu ID (UUID).
        Inclui nome, data de nascimento, escola, série, turma, diagnóstico,
        responsáveis e observações.
        """
        aluno = await get_student_repo().get_by_id(aluno_id)
        if not aluno:
            return {"erro": "Aluno não encontrado", "aluno_id": aluno_id}
        return aluno

    @mcp.tool()
    async def criar_aluno(
        nome: str,
        escola_id: str | None = None,
        data_nascimento: str | None = None,
        idade: str | None = None,
        serie: str | None = None,
        turma: str | None = None,
        responsaveis: list[str] | None = None,
        diagnostico: str | None = None,
        observacoes: str | None = None,
    ) -> dict:
        """
        Cria um novo aluno na plataforma.
        data_nascimento deve estar no formato YYYY-MM-DD.
        responsaveis é uma lista de nomes dos responsáveis.
        Retorna o aluno criado com seu ID gerado.
        """
        data = {
            "name": nome,
            "school_id": escola_id,
            "birth_date": data_nascimento,
            "age": idade,
            "grade": serie,
            "class_name": turma,
            "guardians": responsaveis or [],
            "diagnosis": diagnostico,
            "notes": observacoes,
        }
        return await get_student_repo().create(data)

    @mcp.tool()
    async def atualizar_aluno(
        aluno_id: str,
        nome: str | None = None,
        escola_id: str | None = None,
        data_nascimento: str | None = None,
        idade: str | None = None,
        serie: str | None = None,
        turma: str | None = None,
        responsaveis: list[str] | None = None,
        diagnostico: str | None = None,
        observacoes: str | None = None,
    ) -> dict:
        """
        Atualiza os dados de um aluno existente.
        Apenas os campos fornecidos (não nulos) são alterados.
        Retorna o aluno atualizado ou erro se não encontrado.
        """
        data: dict = {}
        if nome is not None:
            data["name"] = nome
        if escola_id is not None:
            data["school_id"] = escola_id
        if data_nascimento is not None:
            data["birth_date"] = data_nascimento
        if idade is not None:
            data["age"] = idade
        if serie is not None:
            data["grade"] = serie
        if turma is not None:
            data["class_name"] = turma
        if responsaveis is not None:
            data["guardians"] = responsaveis
        if diagnostico is not None:
            data["diagnosis"] = diagnostico
        if observacoes is not None:
            data["notes"] = observacoes

        resultado = await get_student_repo().update(aluno_id, data)
        if not resultado:
            return {"erro": "Aluno não encontrado", "aluno_id": aluno_id}
        return resultado

    @mcp.tool()
    async def deletar_aluno(aluno_id: str) -> dict:
        """
        Remove (soft delete) um aluno da plataforma pelo seu ID.
        O registro é marcado como deletado mas não é apagado do banco.
        """
        removido = await get_student_repo().delete(aluno_id)
        if not removido:
            return {"erro": "Aluno não encontrado", "aluno_id": aluno_id}
        return {"status": "removido", "aluno_id": aluno_id}
