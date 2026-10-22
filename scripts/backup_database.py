"""Backup do banco de dados (PostgreSQL) para o seu computador.

SOMENTE LEITURA: só executa `pg_dump` e `SELECT`; não altera nada no banco.

Uso (na pasta agents-backend). A DATABASE_URL de PRODUÇÃO deve estar no ambiente ou no .env
— nunca cole a senha no chat nem na linha de comando:

    python scripts/backup_database.py
    python scripts/backup_database.py --out D:\\Backups\\smartpei_db
    python scripts/backup_database.py --all-schemas          # inclui schemas do Supabase (auth, storage...)

Como o dump é feito (nesta ordem):
    1. `pg_dump` instalado no PC;
    2. senão, Docker (imagem postgres:17-alpine, só roda o cliente; o banco continua remoto).
Se o servidor for de versão MAIOR que o cliente, use --pg-image postgres:<versão>-alpine.

O que grava em <out>/smartpei_db_<data-hora>/:
    database.dump      dump em formato custom (restaura com pg_restore)
    row_counts.json    contagem de linhas por tabela + revisão do Alembic (para conferir depois)
    manifest.json      tamanho, SHA-256, versão do pg_dump e do banco
    RESTORE.md         comandos de restauração

SÓ UM PERÍODO (--since): em vez do dump completo, exporta apenas as LINHAS criadas no período
    (de --since até --until, inclusive; padrão: hoje), uma tabela por arquivo .jsonl:

        python scripts/backup_database.py --since 2026-09-21
        python scripts/backup_database.py --since 21/09/2026 --until 19/10/2026

    A data usada em cada tabela é `created_at` (ou `submitted_at` / `generated_at` / `updated_at` nas poucas
    tabelas que não têm created_at). Linhas só EDITADAS no período, mas criadas antes, não entram (exceto em
    student_skill_scores, que usa updated_at). Não é um dump restaurável com pg_restore: é para trazer o que é
    novo para outro banco (INSERT ... ON CONFLICT DO NOTHING). Os campos continuam criptografados.

ATENÇÃO:
    * O backup contém dados sensíveis (alunos, saúde). Guarde em disco criptografado e fora de pastas sincronizadas.
    * Campos sensíveis são criptografados com ENCRYPTION_KEY. SEM essa chave o backup NÃO é legível.
      Guarde a chave num gerenciador de senhas — este script NÃO a grava no backup.
"""
import argparse
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DEFAULT_IMAGE = "postgres:17-alpine"


def parse_database_url(raw: str) -> dict:
    """Aceita postgresql://, postgres:// e postgresql+asyncpg:// e devolve as partes (sem logar a senha)."""
    url = raw.replace("postgresql+asyncpg://", "postgresql://").replace("postgres://", "postgresql://", 1)
    p = urlparse(url)
    if p.scheme != "postgresql" or not p.hostname:
        sys.exit("DATABASE_URL inválida (esperado postgresql://usuario:senha@host:porta/banco)")
    return {
        "host": p.hostname, "port": str(p.port or 5432), "user": unquote(p.username or ""),
        "password": unquote(p.password or ""), "dbname": (p.path or "/postgres").lstrip("/"),
        "sslmode": ("require" if "ssl" in (p.query or "") or p.hostname not in ("localhost", "127.0.0.1") else "prefer"),
    }


def pick_runner(image: str) -> tuple[str, list[str]]:
    """Escolhe como executar o cliente do Postgres: local ou via Docker."""
    if shutil.which("pg_dump"):
        return "local", []
    if shutil.which("docker"):
        probe = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if probe.returncode == 0:
            return "docker", ["docker", "run", "--rm", "-i", "-e", "PGPASSWORD", "-e", "PGSSLMODE", image]
    sys.exit(
        "Não encontrei `pg_dump` nem o Docker em execução.\n"
        "Instale um deles: PostgreSQL client tools (https://www.postgresql.org/download/) ou Docker Desktop."
    )


def run_client(runner_prefix: list[str], tool: str, args: list[str], env: dict, stdout=None):
    cmd = (runner_prefix + [tool] + args) if runner_prefix else [tool] + args
    return subprocess.run(cmd, env=env, stdout=stdout, stderr=subprocess.PIPE)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


async def collect_counts(database_url: str) -> dict:
    from sqlalchemy import text
    from infrastructure.database_context.database import Database

    db = Database(database_url)
    out: dict = {"tables": {}, "alembic_version": None, "server_version": None}
    async with db.session() as s:
        out["server_version"] = (await s.execute(text("SHOW server_version"))).scalar()
        try:
            out["alembic_version"] = (await s.execute(text("SELECT version_num FROM alembic_version"))).scalar()
        except Exception:  # noqa: BLE001
            out["alembic_version"] = None
        names = (await s.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY 1"
        ))).scalars().all()
        for name in names:
            out["tables"][name] = (await s.execute(text(f'SELECT count(*) FROM "{name}"'))).scalar()
    return out


# Coluna de data usada para decidir se a linha é do período (a primeira que a tabela tiver).
DATE_COLUMNS = ("created_at", "submitted_at", "generated_at", "updated_at")


def parse_day(value: str, flag: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            pass
    sys.exit(f"{flag}: data inválida '{value}' (use AAAA-MM-DD ou DD/MM/AAAA)")


async def export_period(database_url: str, dest: Path, since: datetime, until: datetime) -> dict:
    """Exporta, em JSON Lines, as linhas de cada tabela de `public` cuja data cai em [since, until] (dias inteiros).

    Só SELECT. O JSON é gerado pelo próprio Postgres (row_to_json), então tipos como vetor, UUID e datas
    voltam fielmente com json_populate_recordset na hora de importar."""
    from datetime import timedelta
    from sqlalchemy import text
    from infrastructure.database_context.database import Database

    end = until + timedelta(days=1)  # limite exclusivo
    tables_dir = dest / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    db = Database(database_url)
    summary: dict = {"tables": {}, "skipped_without_date": []}
    async with db.session() as s:
        cols = (await s.execute(text(
            "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='public' "
            "AND column_name = ANY(:cols)"
        ), {"cols": list(DATE_COLUMNS)})).all()
        by_table: dict[str, set] = {}
        for table, col in cols:
            by_table.setdefault(table, set()).add(col)
        names = (await s.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' "
            "AND table_type='BASE TABLE' AND table_name <> 'alembic_version' ORDER BY 1"
        ))).scalars().all()
        for name in names:
            col = next((c for c in DATE_COLUMNS if c in by_table.get(name, set())), None)
            if not col:
                summary["skipped_without_date"].append(name)
                continue
            query = text(
                f'SELECT row_to_json(t)::text FROM "{name}" t '
                f'WHERE t."{col}"::timestamp >= :since AND t."{col}"::timestamp < :until ORDER BY t."{col}"'
            )
            count = 0
            with (tables_dir / f"{name}.jsonl").open("w", encoding="utf-8") as f:
                result = await s.stream(query, {"since": since, "until": end})
                async for (line,) in result:
                    f.write(line + "\n")
                    count += 1
            if count == 0:
                (tables_dir / f"{name}.jsonl").unlink()
            else:
                summary["tables"][name] = {"rows": count, "date_column": col}
    return summary


def delta_main(args, raw: str) -> None:
    since = parse_day(args.since, "--since")
    until = parse_day(args.until, "--until") if args.until else datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if until < since:
        sys.exit("--until não pode ser antes de --since.")
    conn = parse_database_url(raw)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = Path(args.out) / f"smartpei_db_de_{since:%Y%m%d}_ate_{until:%Y%m%d}_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    print(f"Banco: {conn['dbname']} @ {conn['host']}:{conn['port']}")
    print(f"Período: {since:%d/%m/%Y} a {until:%d/%m/%Y} (dias inteiros, inclusive)")
    print(f"Destino: {dest}\n")
    summary = asyncio.run(export_period(raw, dest, since, until))
    total = sum(t["rows"] for t in summary["tables"].values())
    manifest = {
        "created_at": datetime.now().isoformat(), "database": conn["dbname"], "host": conn["host"],
        "mode": "period", "since": f"{since:%Y-%m-%d}", "until": f"{until:%Y-%m-%d}",
        "rows_total": total, "tables": summary["tables"], "skipped_without_date": summary["skipped_without_date"],
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    for name, info in sorted(summary["tables"].items(), key=lambda kv: -kv[1]["rows"]):
        print(f"  {name:<40} {info['rows']:>6}")
    print(f"\n✔ {total} linhas em {len(summary['tables'])} tabelas.  Pasta: {dest}")
    if summary["skipped_without_date"]:
        print(f"  (sem coluna de data, ignoradas: {', '.join(summary['skipped_without_date'])})")
    print("Lembrete: guarde a ENCRYPTION_KEY de produção — sem ela os campos criptografados não abrem.")


RESTORE_MD = """# Restaurar este backup

Pré-requisitos: um PostgreSQL VAZIO (mesma versão ou superior) com a extensão pgvector disponível, e a
`ENCRYPTION_KEY` de produção (sem ela os campos criptografados ficam ilegíveis).

```bash
# 1) criar o banco e a extensão (como superusuário)
createdb smartpei_restore
psql -d smartpei_restore -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 2) restaurar
pg_restore --no-owner --no-privileges -d smartpei_restore database.dump

# 3) conferir com row_counts.json (contagem de linhas por tabela)
```

Com Docker (sem instalar nada):

```bash
docker run -d --name pg_restore_test -e POSTGRES_PASSWORD=teste -p 55432:5432 pgvector/pgvector:pg17
docker cp database.dump pg_restore_test:/tmp/database.dump
docker exec pg_restore_test psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec pg_restore_test pg_restore -U postgres --no-owner --no-privileges -d postgres /tmp/database.dump
```

NUNCA restaure por cima do banco de produção sem antes fazer um novo backup dele.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup do banco PostgreSQL (somente leitura)")
    default_out = Path.home() / "Backups" / "smartpei_db"
    parser.add_argument("--out", default=str(default_out), help=f"Pasta de destino (padrão: {default_out})")
    parser.add_argument("--all-schemas", action="store_true", help="Inclui todos os schemas (padrão: só 'public')")
    parser.add_argument("--pg-image", default=DEFAULT_IMAGE, help=f"Imagem Docker do cliente (padrão: {DEFAULT_IMAGE})")
    parser.add_argument("--since", default=None, help="Só linhas criadas a partir desta data (AAAA-MM-DD ou DD/MM/AAAA); não faz pg_dump")
    parser.add_argument("--until", default=None, help="Só linhas criadas até esta data, inclusive (padrão: hoje)")
    args = parser.parse_args()

    raw = os.getenv("DATABASE_URL")
    if not raw:
        sys.exit("DATABASE_URL não definida (coloque a de PRODUÇÃO no .env ou no ambiente).")
    if args.since or args.until:
        if not args.since:
            sys.exit("--until só funciona junto com --since.")
        return delta_main(args, raw)
    conn = parse_database_url(raw)

    mode, prefix = pick_runner(args.pg_image)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = Path(args.out) / f"smartpei_db_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    dump_path = dest / "database.dump"

    env = {**os.environ, "PGPASSWORD": conn["password"], "PGSSLMODE": conn["sslmode"]}
    print(f"Banco: {conn['dbname']} @ {conn['host']}:{conn['port']}  (cliente: {mode})")
    print(f"Destino: {dest}\n")

    dump_args = ["-h", conn["host"], "-p", conn["port"], "-U", conn["user"], "-d", conn["dbname"],
                 "-Fc", "--no-owner", "--no-privileges"]
    if not args.all_schemas:
        dump_args += ["-n", "public"]
    print("Gerando dump (pode levar alguns minutos)...")
    with dump_path.open("wb") as f:
        res = run_client(prefix, "pg_dump", dump_args, env, stdout=f)
    if res.returncode != 0:
        dump_path.unlink(missing_ok=True)
        err = res.stderr.decode("utf-8", "replace").strip()
        hint = "\nDica: versão do servidor maior que a do cliente? Use --pg-image postgres:<versão>-alpine." if "version" in err.lower() else ""
        sys.exit(f"pg_dump falhou:\n{err}{hint}")

    # confere que o arquivo é um dump válido e legível
    with dump_path.open("rb") as f:
        check = subprocess.run(
            (prefix + ["pg_restore", "--list"]) if prefix else ["pg_restore", "--list"],
            stdin=f, capture_output=True, env=env,
        )
    entries = len([ln for ln in check.stdout.decode("utf-8", "replace").splitlines() if ln and not ln.startswith(";")])
    if check.returncode != 0 or entries == 0:
        sys.exit("O dump foi gerado, mas não passou na verificação do pg_restore --list. Não confie neste arquivo.")

    counts: dict = {}
    try:
        counts = asyncio.run(collect_counts(raw))
        (dest / "row_counts.json").write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"⚠ Não consegui contar as linhas (o dump está ok): {e}")

    ver = run_client(prefix, "pg_dump", ["--version"], env, stdout=subprocess.PIPE)
    manifest = {
        "created_at": datetime.now().isoformat(),
        "database": conn["dbname"], "host": conn["host"],
        "schemas": "all" if args.all_schemas else "public",
        "size_bytes": dump_path.stat().st_size, "sha256": sha256(dump_path),
        "toc_entries": entries, "pg_dump": ver.stdout.decode().strip() if ver.returncode == 0 else None,
        "server_version": counts.get("server_version"), "alembic_version": counts.get("alembic_version"),
        "tables": len(counts.get("tables", {})),
        "rows_total": sum(counts.get("tables", {}).values()) if counts else None,
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (dest / "RESTORE.md").write_text(RESTORE_MD, encoding="utf-8")

    print(f"\n✔ Backup concluído: {dump_path.stat().st_size / 1048576:.1f} MB, {entries} objetos, "
          f"{manifest['tables']} tabelas, {manifest['rows_total']} linhas")
    print(f"  SHA-256: {manifest['sha256']}")
    print(f"  Pasta:   {dest}")
    print("\nLembrete: guarde a ENCRYPTION_KEY de produção — sem ela os campos criptografados não abrem.")


if __name__ == "__main__":
    main()
