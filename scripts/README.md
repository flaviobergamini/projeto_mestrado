# Manual dos scripts de backup e restauração — SmartPEI

Scripts em `agents-backend/scripts/` para **fazer backup** do banco (PostgreSQL) e do storage (Supabase) para o seu computador e **restaurá-los** em outro projeto Supabase.

| Script | Para que serve | Escreve em |
|---|---|---|
| `backup_all.py` | Roda o backup do banco e do storage, na mesma pasta datada | só no seu disco |
| `backup_database.py` | Dump do PostgreSQL (`pg_dump`, formato custom) | só no seu disco |
| `backup_storage.py` | Baixa todos os arquivos do bucket | só no seu disco |
| `restore_database.py` | Restaura o dump em um banco **novo** | banco de destino |
| `restore_storage.py` | Envia os arquivos para o bucket **novo** | bucket de destino |
| `backup_images.py`, `recompress_images.py` | Scripts antigos (backup só de imagens e recompressão). Não são necessários no fluxo abaixo | — |

Os scripts de **backup só leem** a origem (`pg_dump`, `SELECT`, `list`, `download`). Os de **restore escrevem só no destino** (`TARGET_*`) e **recusam rodar** se o destino for igual à origem.

---

## 1. Pré-requisitos

1. **Python do projeto** com as dependências (`requirements.txt`). Rode sempre na pasta `agents-backend`.
2. **Para o banco**, um destes dois:
   - **Docker Desktop em execução** (o script usa a imagem `postgres:17-alpine`; na primeira vez baixa ~100 MB); ou
   - **PostgreSQL client tools** instalados (`pg_dump`, `pg_restore`, `psql` no PATH).
3. **Espaço em disco** para o backup (banco pequeno; o storage tem ~140 MB hoje).
4. **Segurança:** o backup contém dados sensíveis de crianças. Guarde em disco criptografado, fora de pastas sincronizadas (OneDrive, Drive).

> **`ENCRYPTION_KEY`:** campos sensíveis do banco são criptografados com essa chave. **Sem ela, o backup do banco é ilegível.** Guarde-a num gerenciador de senhas. Os scripts **não** a gravam no backup. Ao migrar para outro projeto, ela **não muda**.

---

## 2. Variáveis de ambiente (`.env` em `agents-backend/`)

Você preenche os valores no arquivo `.env`. **Nunca cole senhas ou chaves no chat, em e-mails ou na linha de comando.**

### Origem (backup)
| Variável | O que é |
|---|---|
| `DATABASE_URL` | Connection string do banco **de origem** |
| `SUPABASE_URL` | URL do projeto Supabase de origem (`https://<ref>.supabase.co`) |
| `SUPABASE_KEY` | Chave com permissão de administrador (`service_role` ou `sb_secret_…`) |
| `SUPABASE_BUCKET` | Nome do bucket (ex.: `agents-buket`) |

### Destino (restore)
| Variável | O que é |
|---|---|
| `TARGET_DATABASE_URL` | Connection string do banco **novo** (Session pooler, porta 5432) |
| `TARGET_SUPABASE_URL` | URL do projeto Supabase **novo** |
| `TARGET_SUPABASE_KEY` | **Secret key / service_role** do projeto novo (**não** a publishable/anon) |
| `TARGET_SUPABASE_BUCKET` | Nome do bucket no projeto novo (ex.: `mestrado`) |
| `OLD_SUPABASE_URL` | URL do projeto **antigo**, usada para corrigir as `public_url` gravadas no banco |

### Como escrever a connection string
```
postgresql://postgres.<ref>:<senha>@<host-do-pooler>:5432/postgres
```
- Copie a string **do painel** (botão **Connect → Session pooler**), sem montar à mão. O host muda por região e geração do projeto (`aws-0-…` ou `aws-1-…`).
- **Caracteres especiais na senha devem ser codificados:** `@`→`%40`, `:`→`%3A`, `/`→`%2F`, `?`→`%3F`, `#`→`%23`, `%`→`%25`, espaço→`%20`. Exemplo: `Husky@987` vira `Husky%40987`.
- Use o **Session pooler** (5432). Não use a conexão direta (`db.<ref>.supabase.co`): ela usa IPv6 e costuma falhar no Docker do Windows.
- **Não deixe a mesma variável duas vezes** no `.env`: vale a **última** linha. Isso já fez o script recusar rodar por achar que origem e destino eram iguais.

---

## 3. Fazer backup

### Backup completo (banco + storage)
```bash
python scripts/backup_all.py --dry-run
python scripts/backup_all.py
```
- `--dry-run` mostra o alvo (host do banco, host do storage, bucket) e o destino, **sem copiar nada**. Confira se é o projeto certo.
- Opções: `--out <pasta>` (padrão `C:\Users\<você>\Backups\smartpei`), `--only db` ou `--only storage`, `--yes` (não pergunta "são dados de produção?").

Resultado: `<out>/<data-hora>/db/smartpei_db_<data-hora>/` e `<out>/<data-hora>/storage/smartpei_storage_<data-hora>/`.

### Só o banco
```bash
python scripts/backup_database.py
```
Opções: `--out <pasta>`, `--all-schemas` (inclui schemas do Supabase; padrão: só `public`), `--pg-image postgres:<versão>-alpine` (se o servidor for de versão maior que o cliente).

Gera na pasta:
- `database.dump` — dump em formato custom (restaura com `pg_restore`)
- `row_counts.json` — linhas por tabela e revisão do Alembic (para conferir depois)
- `manifest.json` — tamanho, SHA-256, versões
- `RESTORE.md` — comandos de restauração manual

O script confere o dump com `pg_restore --list` antes de terminar.

### Só o storage
```bash
python scripts/backup_storage.py
```
Opções: `--out <pasta>`, `--bucket <nome>`, `--workers <n>` (padrão 6), `--reuse <pasta de backup anterior>` (copia arquivos idênticos em vez de baixar de novo).

Gera `files/<caminho no bucket>`, `object_storage_files.json` (cópia da tabela do banco) e `manifest.json` (tamanho e SHA-256 de cada arquivo). Termina com erro se algum arquivo falhar ou vier com tamanho diferente.

### Só um período (por exemplo, de 21/09 até hoje)
```bash
python scripts/backup_all.py --since 2026-09-21
python scripts/backup_database.py --since 21/09/2026
python scripts/backup_storage.py --since 2026-09-21 --until 2026-10-19
```
- `--since` aceita `AAAA-MM-DD` ou `DD/MM/AAAA`; `--until` é opcional (padrão: hoje) e inclui o dia inteiro. Funciona nos três scripts.
- **Storage:** baixa só os arquivos criados no período (data de criação no bucket). A pasta leva o período no nome.
- **Banco:** em vez do `pg_dump`, exporta só as **linhas criadas** no período, uma tabela por arquivo em `tables/<tabela>.jsonl`, mais `manifest.json` (linhas por tabela). A data usada é `created_at` (ou `submitted_at`/`generated_at`/`updated_at` nas poucas tabelas sem `created_at`; em `student_skill_scores` vale o `updated_at`). Só `SELECT`, não altera nada.
- Limites: linhas **criadas antes** do período e apenas editadas nele não entram (exceto `student_skill_scores`). Esse formato **não** restaura com `pg_restore`: serve para trazer o que é novo para outro banco com `INSERT ... ON CONFLICT DO NOTHING` (o script de importação ainda não existe). Os campos sensíveis continuam criptografados: guarde a `ENCRYPTION_KEY`.
- Os horários no banco estão em UTC; 21/09 às 00:00 UTC equivale a 20/09 às 21:00 em Brasília, então algumas linhas das últimas horas de 20/09 podem vir junto.

---

## 4. Restaurar em um projeto Supabase novo

### Ordem
1. Faça o backup da origem (seção 3).
2. Crie o projeto novo no Supabase (região **São Paulo**, perto do Azure). **Não crie tabelas nem bucket**: os scripts cuidam disso.
3. Preencha as variáveis `TARGET_*` e `OLD_SUPABASE_URL` no `.env`.
4. Restaure o banco → restaure o storage → corrija o nome do bucket (opcional) → teste → troque as variáveis no Azure.

### 4.1 Restaurar o banco
```bash
python scripts/restore_database.py --backup <pasta>\db\smartpei_db_<data-hora> --dry-run
python scripts/restore_database.py --backup <pasta>\db\smartpei_db_<data-hora>
```
- O `--backup` é a pasta **`smartpei_db_…`** (a do banco, não a do storage).
- O `--dry-run` só confere o SHA-256 do dump e mostra o destino.
- Ao rodar de verdade, ele pede para você **digitar o host do destino** (a parte entre `@` e `:5432` da `TARGET_DATABASE_URL`). É uma trava para evitar restaurar no lugar errado. `--yes` pula a pergunta.

O que ele faz, em ordem:
1. Confere o SHA-256 do `database.dump`.
2. Habilita a extensão **pgvector** no destino (`CREATE EXTENSION vector`).
3. `pg_restore --no-owner --no-privileges` (esquema, dados e vetores).
4. Confere a revisão do Alembic e a contagem de linhas de **cada tabela** contra o `row_counts.json`.
5. Se `OLD_SUPABASE_URL` e `TARGET_SUPABASE_URL` existirem, troca o endereço antigo nas colunas `public_url`.

**Resultado esperado:** "Alembic no destino: 0034… (backup: 0034…)" e "todas as tabelas conferem". Avisos como `schema public already exists` são **benignos**.

**Não rode as migrations do Alembic no banco novo.** O dump já traz esquema, dados e a tabela `alembic_version`; rodar `alembic upgrade head` por cima duplicaria dados como o catálogo BNCC.

Para corrigir só as URLs, depois (por exemplo, se o `OLD_SUPABASE_URL` estava errado):
```bash
python scripts/restore_database.py --backup <pasta>\db\smartpei_db_<data-hora> --only-urls
```

### 4.2 Restaurar o storage
```bash
python scripts/restore_storage.py --backup <pasta>\storage\smartpei_storage_<data-hora> --dry-run
python scripts/restore_storage.py --backup <pasta>\storage\smartpei_storage_<data-hora>
```
- O `--backup` é a pasta **`smartpei_storage_…`**.
- Opções: `--workers <n>` (padrão 3), `--dry-run`.

O que faz: confere tamanho e SHA-256 de cada arquivo contra o manifesto, **cria o bucket privado** se não existir, envia cada arquivo para o **mesmo caminho**, e no fim lista o bucket de destino para conferir existência e tamanho.

**Resultado esperado:** "✔ N arquivos no bucket '<nome>' conferidos (existência e tamanho)".

### 4.3 Nome do bucket diferente do original
Se o bucket novo tem nome diferente (ex.: `agents-buket` → `mestrado`):
- Defina `SUPABASE_BUCKET=<nome novo>` no Azure e no `.env` de teste.
- A coluna `bucket` da tabela `object_storage_files` ainda guarda o nome antigo. Atualize no banco novo:
```sql
UPDATE object_storage_files SET bucket = 'mestrado' WHERE bucket = 'agents-buket';
```
O app gera os links de imagem pela `object_key` e pelo `SUPABASE_BUCKET`. A `public_url` gravada é só reserva (a maioria são links assinados antigos, já vencidos).

### 4.4 Teste e troca em produção
1. **Teste local:** no `.env`, deixe **um só valor ativo** de cada variável e aponte `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_KEY` (secret/service_role) e `SUPABASE_BUCKET` para o projeto novo. Rode o backend e teste: login, lista de alunos, um diário com fotos, o catálogo de habilidades e um PEI em PDF.
2. **Azure:** em *Environment variables*, atualize as 4 variáveis. **Não altere a `ENCRYPTION_KEY`.** Salve e reinicie o app. Repita o teste pelo front de produção.
3. **Plano de volta:** mantenha o projeto antigo intacto por cerca de 15 dias. Para voltar, restaure as 4 variáveis no Azure.
4. Escritas feitas entre o backup e a troca se perdem. Se houve uso nesse intervalo, repita backup e restauração antes de trocar.

---

## 5. Pode rodar mais de uma vez?

| Script | Repetir? |
|---|---|
| `backup_*` | **Sim.** Cada execução cria uma pasta nova e datada. |
| `restore_storage.py` | **Sim, sem duplicar.** Usa `upsert` (mesmo caminho = substitui) e pula o que já existe com o mesmo tamanho. É o jeito certo de completar uma execução que teve falhas de rede. |
| `restore_database.py --only-urls` | **Sim.** A segunda vez não acha mais nada para trocar. |
| `restore_database.py` (restore completo) | **Não, no mesmo banco.** O `pg_restore` tentaria recriar tabelas e reinserir dados; tabelas sem chave primária podem **duplicar linhas**. Restaure **uma vez** em um banco **vazio**. Para refazer, use um projeto novo (ou esvazie o schema `public` antes). |
| `--dry-run` | **Sim.** Só lê. |

---

## 6. Problemas comuns

| Mensagem / sintoma | Causa e solução |
|---|---|
| `Não encontrei pg_dump nem o Docker em execução` | Abra o **Docker Desktop** e espere "Engine running" (`docker info` deve listar "Server Version"), ou instale o PostgreSQL client tools. Se só o banco falhou, repita com `--only db`. |
| `FATAL: (ENOTFOUND) tenant/user postgres.<ref> not found` | Host do pooler não combina com o projeto (região ou `aws-0` × `aws-1`). Copie a string do painel (**Connect → Session pooler**), sem montar à mão. |
| Senha com `@` e erro de conexão | Codifique o `@` como `%40` na URL. |
| `KeyError: 'size_bytes'` | Você passou a pasta do **storage** ao `restore_database.py`. Use `smartpei_db_…` para o banco e `smartpei_storage_…` para o storage. |
| `TARGET_SUPABASE_URL é IGUAL ao SUPABASE_URL de origem. Recusado.` | O `.env` tem a variável `SUPABASE_URL` repetida (vale a última). Remova a duplicata ou comente a linha do projeto novo. |
| `new row violates row-level security policy` ao criar o bucket | A `TARGET_SUPABASE_KEY` é a chave **publicável/anon**. Use a **Secret key** (`sb_secret_…`) ou a `service_role`. |
| Falhas `WinError 10035` ou `ConnectionTerminated` no envio | Queda de conexão. O script já usa uma conexão por envio e 5 tentativas. **Repita o comando**: ele só envia o que falta. |
| `COM PROBLEMAS` com "errors ignored on restore: 1" | A linha-resumo do `pg_restore` repete o aviso benigno. Se as contagens e o Alembic conferem, o restore está bom. |
| `0 linha(s) de object_storage_files atualizadas` | `OLD_SUPABASE_URL` não é o endereço que está nas linhas (ou é igual ao novo). Corrija e rode com `--only-urls`. |
| `SHA-256 do database.dump NÃO bate` | Backup corrompido ou incompleto. Refaça o backup. |
| `pg_dump falhou … version` | Servidor com versão maior que o cliente. Use `--pg-image postgres:<versão>-alpine`. |

---

## 7. Limites e cuidados

- O Supabase Free cobra por **egress** (tráfego de saída) por ciclo. O backup do storage baixa todos os arquivos, o que conta. Hoje são ~140 MB.
- Os links de imagem do app são **assinados** (válidos por 24 h) e gerados a partir da `object_key`. Por isso as chaves e o nome do bucket precisam estar corretos no destino.
- O restore **não copia usuários** de autenticação: o sistema usa Cognito, não o Auth do Supabase.
- Guarde `database.dump`, o `manifest.json` e os arquivos como material sensível. Apague cópias temporárias ao terminar.
