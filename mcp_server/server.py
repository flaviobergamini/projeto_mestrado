"""
Servidor MCP da plataforma SmartPEI.

Expõe as funcionalidades da plataforma como ferramentas MCP para que agentes de IA
possam interagir com dados de alunos com TEA de forma padronizada e segura.

Transportes suportados:
  - stdio  (padrão): para integração local com Claude Desktop e IDEs.
  - sse:             para agentes remotos via HTTP/SSE com autenticação por API key.

Configuração via variáveis de ambiente (.env):
  MCP_TRANSPORT        = stdio | sse         (padrão: stdio)
  MCP_PORT             = <porta>             (padrão: 8001, apenas para SSE)
  MCP_SERVER_API_KEY   = <chave-secreta>     (obrigatória para SSE em produção)

  As demais variáveis do backend (DATABASE_URL, GEMINI_API_KEY, etc.) também são necessárias.

Execução:
  python -m mcp_server.server          # stdio
  MCP_TRANSPORT=sse python -m mcp_server.server   # SSE na porta 8001
"""

import os
import logging

from mcp.server.fastmcp import FastMCP

from mcp_server.auth import ApiKeyMiddleware, get_api_key
from mcp_server.tools import (
    students,
    diary,
    pdi,
    case_study,
    chat,
    pei,
    schools,
    teachers,
    vinculos,
    users,
    ai_usage,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MCP] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Instância principal do servidor MCP ───────────────────────────────────────

mcp = FastMCP(
    "SmartPEI",
    instructions="""
Você é um assistente especializado no suporte à educação inclusiva de alunos com
Transtorno do Espectro Autista (TEA) via plataforma SmartPEI.

Capacidades disponíveis via ferramentas MCP:
- Consultar e gerenciar alunos, escolas e professores
- Ler e registrar entradas de diário escolar, familiar e terapêutico
- Acessar e criar PDIs (Planos de Desenvolvimento Individual)
- Consultar e criar estudos de caso
- Conversar via chat RAG com contexto anonimizado do aluno
- Gerar PEIs (Planos Educacionais Individualizados) com IA Gemini
- Monitorar uso e custos da API de IA

Todos os dados retornados são em JSON.
Ao gerar PEIs ou usar o chat RAG, os dados do aluno são anonimizados antes de
serem enviados à IA (os nomes reais são restaurados na resposta final).
""",
)

# ── Registro das ferramentas por domínio ──────────────────────────────────────

students.register(mcp)
diary.register(mcp)
pdi.register(mcp)
case_study.register(mcp)
chat.register(mcp)
pei.register(mcp)
schools.register(mcp)
teachers.register(mcp)
vinculos.register(mcp)
users.register(mcp)
ai_usage.register(mcp)


# ── Ponto de entrada ──────────────────────────────────────────────────────────

def run() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport == "sse":
        import uvicorn

        port = int(os.getenv("MCP_PORT", "8001"))
        api_key = get_api_key()

        # Obtém o app Starlette/ASGI do FastMCP para SSE
        app = mcp.sse_app()

        if api_key:
            app.add_middleware(ApiKeyMiddleware, api_key=api_key)
            logger.info("Autenticação por API key habilitada para SSE.")
        else:
            logger.warning(
                "MCP_SERVER_API_KEY não definida — servidor SSE sem autenticação. "
                "Não recomendado para produção."
            )

        logger.info("Iniciando servidor MCP (SSE) na porta %d", port)
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

    else:
        logger.info("Iniciando servidor MCP (stdio)")
        mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
