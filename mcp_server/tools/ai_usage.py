"""Ferramentas MCP para monitoramento de uso e custos da API de IA."""
import asyncio
from mcp.server.fastmcp import FastMCP
from mcp_server.context import get_ai_usage_repo


async def _gather(*coros):
    return await asyncio.gather(*coros)


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def obter_resumo_uso_ia(dias: int = 14) -> dict:
        """
        Retorna um resumo do uso e custo da API Gemini nos últimos N dias.
        Inclui:
          - by_model: custo e tokens agrupados por modelo
          - by_operation: custo e tokens agrupados por operação (chat_rag, pei_generation, etc.)
          - daily: uso diário com tokens de entrada, saída e custo
          - distinct: modelos e operações únicas usadas
        dias: número de dias para o resumo (padrão: 14).
        """
        repo = get_ai_usage_repo()
        by_model, by_operation, daily, distinct = await _gather(
            repo.summary_by_model(),
            repo.summary_by_operation(),
            repo.daily_usage(days=dias),
            repo.distinct_values(),
        )
        return {
            "by_model": by_model,
            "by_operation": by_operation,
            "daily": daily,
            "distinct": distinct,
        }

    @mcp.tool()
    async def listar_logs_uso_ia(
        modelo: str | None = None,
        operacao: str | None = None,
        data_de: str | None = None,
        data_ate: str | None = None,
        pagina: int = 1,
        tamanho_pagina: int = 20,
    ) -> dict:
        """
        Lista os registros individuais de uso da API Gemini com filtros e paginação.
        Cada registro contém model, operation, input_tokens, output_tokens, cost_usd,
        duration_ms, username e created_at.

        modelo: filtra por nome do modelo (ex: 'gemini-2.5-flash').
        operacao: filtra por operação (ex: 'pei_generation', 'chat_rag', 'embedding_diary').
        data_de / data_ate: filtra por data no formato YYYY-MM-DD.
        pagina: número da página (padrão: 1).
        tamanho_pagina: registros por página (padrão: 20, máximo recomendado: 100).
        """
        from datetime import date as date_type
        return await get_ai_usage_repo().list_paginated(
            model=modelo,
            operation=operacao,
            date_from=date_type.fromisoformat(data_de) if data_de else None,
            date_to=date_type.fromisoformat(data_ate) if data_ate else None,
            page=pagina,
            page_size=tamanho_pagina,
        )

    @mcp.tool()
    async def obter_status_rate_limits() -> dict:
        """
        Retorna o status atual dos rate limits da API Gemini:
          - RPM (requests per minute): requisições por minuto atuais vs limite configurado
          - TPM (tokens per minute): tokens de entrada por minuto atuais vs limite
          - RPD (requests per day): requisições por dia atuais vs limite
        Útil para verificar se o sistema está próximo dos limites.
        """
        return await get_ai_usage_repo().rate_status()
