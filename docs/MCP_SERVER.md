# Servidor MCP — SmartPEI

## O que é o MCP Server

O **Model Context Protocol (MCP)** é um padrão aberto da Anthropic que define como agentes de IA se conectam a sistemas externos de forma padronizada.

Este servidor MCP expõe as funcionalidades da plataforma SmartPEI como **ferramentas** que agentes de IA (Claude, LangChain, n8n, etc.) podem chamar diretamente — sem passar pela interface web e sem precisar de um usuário humano no loop.

### O que o servidor MCP faz hoje

O servidor expõe **52 ferramentas** organizadas por domínio:

| Domínio | Ferramentas disponíveis |
|---|---|
| **Alunos** | Listar, buscar, criar, atualizar, deletar alunos |
| **Diário** | Listar alunos com diário, listar/criar/editar/deletar entradas, buscar professores vinculados |
| **PDI** | Listar, buscar, criar PDIs e atualizar disciplinas por trimestre |
| **Estudo de Caso** | Listar, buscar, criar, atualizar, deletar estudos de caso |
| **Chat RAG** | Enviar mensagens com contexto anonimizado do aluno, listar/buscar/deletar sessões |
| **PEI com IA** | Gerar PEI completo via Gemini, listar/buscar/deletar PEIs salvos |
| **Escolas** | Listar, buscar, criar, atualizar, deletar escolas |
| **Professores** | Listar, buscar, criar, atualizar, deletar professores |
| **Vínculos** | Listar alunos com vínculos, listar professores disponíveis, definir vínculos |
| **Usuários** | Listar usuários por perfil, atualizar perfil, listar municípios |
| **Uso de IA** | Resumo de consumo, logs paginados, status dos rate limits |

O servidor acessa o banco de dados **diretamente via repositórios** (sem passar pela camada HTTP), usando a mesma lógica já existente na API. Dados enviados à IA passam pelo mesmo sistema de anonimização da plataforma.

---

## Configuração

### 1. Instalar a dependência

```bash
pip install "mcp[cli]>=1.0.0"
```

Ou, após atualizar o `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Variáveis de ambiente

Adicione ao `.env` do backend:

```env
# ── MCP Server ────────────────────────────────────────────────────
# Transporte: stdio (Claude Desktop / local) ou sse (HTTP remoto)
MCP_TRANSPORT=stdio

# Porta usada apenas no modo SSE
MCP_PORT=8001

# Chave de autenticação para o modo SSE.
# Gere uma chave segura com: python -c "import secrets; print(secrets.token_hex(32))"
# Obrigatória em produção com SSE. Deixar vazia desativa a autenticação (não recomendado).
MCP_SERVER_API_KEY=cole-aqui-sua-chave-gerada
```

As demais variáveis do backend (`DATABASE_URL`, `GEMINI_API_KEY`, `COGNITO_*`, etc.) são compartilhadas — o MCP server lê o mesmo `.env`.

---

## Transportes disponíveis

O servidor suporta dois modos de operação, controlados por `MCP_TRANSPORT`:

### stdio — para uso local (Claude Desktop, IDEs)

O agente de IA inicia o servidor como um processo filho e se comunica via stdin/stdout. Não há rede envolvida, portanto não há autenticação por chave — a segurança é garantida pelo sistema operacional (só o processo que iniciou o servidor pode se comunicar com ele).

```bash
python -m mcp_server.server
# ou explicitamente:
MCP_TRANSPORT=stdio python -m mcp_server.server
```

### SSE — para agentes remotos (HTTP)

O servidor expõe um endpoint HTTP/SSE que agentes externos podem consumir. **Toda requisição deve incluir o header `Authorization: Bearer <MCP_SERVER_API_KEY>`**.

```bash
MCP_TRANSPORT=sse python -m mcp_server.server
# Disponível em: http://localhost:8001/sse
```

---

## Autenticação

| Transporte | Mecanismo | Quem controla |
|---|---|---|
| `stdio` | Sem autenticação de rede — processo local confiável | Sistema operacional |
| `sse` | `Authorization: Bearer <MCP_SERVER_API_KEY>` em toda requisição | Variável de ambiente |

Para gerar uma chave segura:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Conectando ao Claude Desktop

O Claude Desktop lê um arquivo JSON para saber quais servidores MCP iniciar automaticamente.

**Localização do arquivo:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Conteúdo do arquivo:**

```json
{
  "mcpServers": {
    "smartpei": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/caminho/absoluto/para/agents-backend",
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@host/db",
        "GEMINI_API_KEY": "sua-chave-gemini",
        "GEMINI_MODEL": "gemini-2.5-flash",
        "GEMINI_EMBEDDING_MODEL": "models/gemini-embedding-001",
        "MCP_TRANSPORT": "stdio",
        "COGNITO_REGION": "us-east-1",
        "COGNITO_USER_POOL_ID": "us-east-1_XXXXX",
        "COGNITO_APP_CLIENT_ID": "XXXXX"
      }
    }
  }
}
```

> Se o projeto usa um ambiente virtual (`venv`), substitua `"python"` pelo caminho completo do interpretador:
> - Windows: `"C:\\caminho\\agents-backend\\venv\\Scripts\\python.exe"`
> - Linux/macOS: `"/caminho/agents-backend/venv/bin/python"`

Após salvar, **reinicie o Claude Desktop**. Um ícone de ferramenta aparecerá no chat, indicando que o servidor está ativo.

**Exemplos de uso com Claude Desktop:**
- *"Liste todos os alunos cadastrados"*
- *"Gere um PEI para o aluno com ID abc-123 usando os últimos 30 dias de diário"*
- *"Quais foram os custos de IA nos últimos 14 dias?"*
- *"Crie um novo aluno chamado João Silva na escola X"*

---

## Executando junto com a API no servidor

Em produção, a API FastAPI e o MCP server são processos separados. A forma recomendada de gerenciá-los juntos é com **Supervisor** ou **systemd**.

### Opção 1 — Supervisor (recomendado)

Instale o Supervisor:

```bash
sudo apt install supervisor
```

Crie o arquivo de configuração em `/etc/supervisor/conf.d/smartpei.conf`:

```ini
[program:smartpei-api]
command=/caminho/agents-backend/venv/bin/gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
directory=/caminho/agents-backend
user=ubuntu
autostart=true
autorestart=true
stdout_logfile=/var/log/smartpei-api.log
stderr_logfile=/var/log/smartpei-api-err.log
environment=DATABASE_URL="%(ENV_DATABASE_URL)s",GEMINI_API_KEY="%(ENV_GEMINI_API_KEY)s"

[program:smartpei-mcp]
command=/caminho/agents-backend/venv/bin/python -m mcp_server.server
directory=/caminho/agents-backend
user=ubuntu
autostart=true
autorestart=true
stdout_logfile=/var/log/smartpei-mcp.log
stderr_logfile=/var/log/smartpei-mcp-err.log
environment=MCP_TRANSPORT="sse",MCP_PORT="8001",MCP_SERVER_API_KEY="sua-chave",DATABASE_URL="..."
```

Ative e inicie:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start smartpei-api
sudo supervisorctl start smartpei-mcp

# Ver status:
sudo supervisorctl status
```

### Opção 2 — systemd

Crie `/etc/systemd/system/smartpei-mcp.service`:

```ini
[Unit]
Description=SmartPEI MCP Server
After=network.target smartpei-api.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/caminho/agents-backend
ExecStart=/caminho/agents-backend/venv/bin/python -m mcp_server.server
Restart=on-failure
RestartSec=5
EnvironmentFile=/caminho/agents-backend/.env
Environment=MCP_TRANSPORT=sse
Environment=MCP_PORT=8001

[Install]
WantedBy=multi-user.target
```

Ative o serviço:

```bash
sudo systemctl daemon-reload
sudo systemctl enable smartpei-mcp
sudo systemctl start smartpei-mcp

# Ver status e logs:
sudo systemctl status smartpei-mcp
sudo journalctl -u smartpei-mcp -f
```

### Opção 3 — Docker Compose

Se o projeto já usa Docker, adicione o MCP server como serviço no `docker-compose.yml`:

```yaml
services:
  api:
    build: .
    command: gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    ports:
      - "8000:8000"
    env_file: .env

  mcp:
    build: .
    command: python -m mcp_server.server
    ports:
      - "8001:8001"
    env_file: .env
    environment:
      - MCP_TRANSPORT=sse
      - MCP_PORT=8001
    depends_on:
      - api
```

---

## Expondo o MCP Server via Nginx (modo SSE)

Se usar o modo SSE em produção, configure o Nginx como proxy reverso. SSE requer configurações específicas para manter a conexão aberta:

```nginx
location /mcp/ {
    proxy_pass http://127.0.0.1:8001/;
    proxy_http_version 1.1;

    # Necessário para SSE: desabilita buffering e mantém conexão aberta
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Connection '';
    chunked_transfer_encoding on;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 3600s;
}
```

O endpoint SSE fica acessível em `https://seu-dominio.com/mcp/sse`.

---

## Portas e serviços

| Serviço | Porta padrão | Protocolo |
|---|---|---|
| API FastAPI | 8000 | HTTP/REST |
| MCP Server (SSE) | 8001 | HTTP/SSE |

As duas portas podem coexistir no mesmo servidor sem conflito. O MCP server **não** é necessário para o funcionamento da API — ele é uma camada adicional de acesso para agentes de IA.

---

## Segurança em produção

- **Nunca exponha a porta 8001 sem autenticação** — defina sempre `MCP_SERVER_API_KEY`.
- A chave MCP é independente dos tokens JWT da API. Não reutilize a mesma chave.
- Se o MCP server for usado apenas internamente (por agentes no mesmo servidor), bloqueie a porta 8001 no firewall e use apenas `stdio` ou comunicação localhost.
- Os dados do aluno enviados à IA passam pelo sistema de anonimização existente — os nomes reais nunca chegam ao Gemini.
