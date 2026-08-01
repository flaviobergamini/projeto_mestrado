"""Ferramentas MCP para registros de diário escolar e terapêutico."""
from mcp.server.fastmcp import FastMCP
from mcp_server.context import get_diary_repo


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def listar_alunos_com_diario() -> list[dict]:
        """
        Lista todos os alunos que possuem pelo menos um registro de diário.
        Retorna student_id, student_name, last_entry (data última entrada) e total_entries.
        Útil para descobrir quais alunos têm histórico de acompanhamento.
        """
        return await get_diary_repo().list_students_with_diary()

    @mcp.tool()
    async def listar_entradas_diario(
        aluno_id: str,
        fonte: str | None = None,
        data_de: str | None = None,
        data_ate: str | None = None,
    ) -> list[dict]:
        """
        Lista os registros de diário de um aluno, do mais recente ao mais antigo.
        fonte pode ser 'school' (diário escolar) ou 'family' (diário familiar) ou 'therapy'.
        data_de e data_ate devem estar no formato YYYY-MM-DD para filtrar por período.
        Retorna comportamento, socialização, alimentação, autonomia, presença e observações.
        """
        from datetime import date as date_type
        date_from = date_type.fromisoformat(data_de) if data_de else None
        date_to = date_type.fromisoformat(data_ate) if data_ate else None
        return await get_diary_repo().list_by_student(
            student_id=aluno_id,
            source=fonte,
            date_from=date_from,
            date_to=date_to,
        )

    @mcp.tool()
    async def obter_entrada_diario(entrada_id: str) -> dict:
        """
        Retorna os dados completos de um registro de diário pelo seu ID.
        Inclui todos os campos de comportamento, presença e observações normalizadas.
        """
        entrada = await get_diary_repo().get_by_id(entrada_id)
        if not entrada:
            return {"erro": "Registro de diário não encontrado", "entrada_id": entrada_id}
        return entrada

    @mcp.tool()
    async def criar_entrada_diario(
        aluno_id: str,
        data_diario: str,
        presenca: str = "Presente",
        atencao_professor: str | None = None,
        seguiu_acordos: str | None = None,
        interesse_atividade: str | None = None,
        almocou: str | None = None,
        participou_brincadeiras: str | None = None,
        completou_atividades: str | None = None,
        uso_banheiro: str | None = None,
        observacao_aberta: str | None = None,
        motivo_ausencia: str | None = None,
        nome_professor: str | None = None,
        fonte: str = "school",
    ) -> dict:
        """
        Cria um novo registro de diário para um aluno.
        data_diario deve estar no formato YYYY-MM-DD.
        presenca: 'Presente' ou 'Ausente'.
        fonte: 'school', 'family' ou 'therapy'.
        Os campos de comportamento aceitam valores como 'Sim', 'Não', 'Parcialmente' ou texto livre.
        """
        data = {
            "student_id": aluno_id,
            "diary_date": data_diario,
            "presence": presenca,
            "teacher_attention": atencao_professor,
            "followed_agreements": seguiu_acordos,
            "activity_interest": interesse_atividade,
            "had_lunch": almocou,
            "participated_in_play": participou_brincadeiras,
            "completed_activities": completou_atividades,
            "bathroom_use": uso_banheiro,
            "open_observation": observacao_aberta,
            "absence_reason": motivo_ausencia,
            "teacher_name": nome_professor,
            "source": fonte,
        }
        return await get_diary_repo().create(data)

    @mcp.tool()
    async def atualizar_entrada_diario(
        entrada_id: str,
        data_diario: str | None = None,
        presenca: str | None = None,
        atencao_professor: str | None = None,
        seguiu_acordos: str | None = None,
        interesse_atividade: str | None = None,
        almocou: str | None = None,
        participou_brincadeiras: str | None = None,
        completou_atividades: str | None = None,
        uso_banheiro: str | None = None,
        observacao_aberta: str | None = None,
        motivo_ausencia: str | None = None,
        nome_professor: str | None = None,
    ) -> dict:
        """
        Atualiza campos de um registro de diário existente.
        Apenas os campos fornecidos (não nulos) são alterados.
        """
        data: dict = {}
        mapping = {
            "diary_date": data_diario,
            "presence": presenca,
            "teacher_attention": atencao_professor,
            "followed_agreements": seguiu_acordos,
            "activity_interest": interesse_atividade,
            "had_lunch": almocou,
            "participated_in_play": participou_brincadeiras,
            "completed_activities": completou_atividades,
            "bathroom_use": uso_banheiro,
            "open_observation": observacao_aberta,
            "absence_reason": motivo_ausencia,
            "teacher_name": nome_professor,
        }
        for key, value in mapping.items():
            if value is not None:
                data[key] = value

        resultado = await get_diary_repo().update(entrada_id, data)
        if not resultado:
            return {"erro": "Registro de diário não encontrado", "entrada_id": entrada_id}
        return resultado

    @mcp.tool()
    async def deletar_entrada_diario(entrada_id: str) -> dict:
        """
        Remove (soft delete) um registro de diário pelo seu ID.
        """
        removido = await get_diary_repo().delete(entrada_id)
        if not removido:
            return {"erro": "Registro não encontrado", "entrada_id": entrada_id}
        return {"status": "removido", "entrada_id": entrada_id}

    @mcp.tool()
    async def obter_professores_vinculados(aluno_id: str) -> list[str]:
        """
        Retorna a lista de nomes dos professores vinculados ao aluno.
        """
        return await get_diary_repo().get_linked_teachers(aluno_id)
