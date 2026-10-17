"""Restaura um backup do banco (feito por backup_database.py) em OUTRO PostgreSQL/Supabase.

Escreve SOMENTE no banco de destino (TARGET_DATABASE_URL). Nunca toca o banco de origem e RECUSA rodar se
o destino for o mesmo servidor/banco da DATABASE_URL (origem).

Antes de rodar:
    1. Crie o projeto novo no Supabase (mesma região do Azure, ex.: São Paulo).
    2. Pegue a connection string do "Session pooler" (porta 5432) em Project Settings > Database.
    3. Coloque no .env ou no ambiente — NUNCA cole a senha no chat nem na linha de comando:
         TARGET_DATABASE_URL=postgresql://postgres.<ref>:<senha>@aws-0-<regiao>.pooler.supabase.com:5432/postgres
         (opcional, só para corrigir as URLs públicas guardadas no banco)
         OLD_SUPABASE_URL=https://<ref-antigo>.supabase.co
         TARGET_SUPABASE_URL=https://<ref-novo>.supabase.co

Uso (na pasta agents-backend):
    python scripts/restore_database.py --backup C:\\Users\\...\\Backups\\smartpei\\<data>\\db\\smartpei_db_<data-hora>
    python scripts/restore_database.py --backup <pasta> --dry-run

O que faz:
    1. Confere o SHA-256 do database.dump contra o manifest.json.
    2. Habilita a extensão pgvector (CREATE EXTENSION vector) no destino.
    3. pg_restore (cliente local ou Docker postgres:17-alpine).
    4. Compara a contagem de linhas de cada tabela com row_counts.json e a revisão do Alembic.
    5. Se OLD_SUPABASE_URL/TARGET_SUPABASE_URL existirem, troca a URL antiga nas colunas public_url.

A ENCRYPTION_KEY do app NÃO muda: sem a mesma chave os campos criptografados do backup ficam ilegíveis.
"""
import argparse
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from backup_database import parse_database_url  # noqa: E402

IMAGE = "postgres:17-alpine"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def runner(dump: Path) -> tuple[str, list[str]]:
    """Cliente local (pg_restore/psql) ou Docker (monta o dump em /backup, somente leitura)."""
    if shutil.which("pg_restore") and shutil.which("psql"):
        return "local", []
    if shutil.which("docker") and subprocess.run(["docker", "info"], capture_output=True).returncode == 0:
        return "docker", ["docker", "run", "--rm", "-i", "-e", "PGPASSWORD", "-e", "PGSSLMODE",
                          "-v", f"{dump.parent}:/backup:ro", IMAGE]
    sys.exit("Preciso de pg_restore/psql instalados ou do Docker em execução.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Restaura o backup do banco em um banco NOVO (destino)")
    ap.add_argument("--backup", required=True, help="Pasta smartpei_db_<data-hora> (com database.dump e manifest.json)")
    ap.add_argument("--dry-run", action="store_true", help="Só confere o backup e mostra o destino")
    ap.add_argument("--yes", action="store_true", help="Não pedir confirmação")
    ap.add_argument("--only-urls", action="store_true", help="Só corrige as public_url (pula o restore; usar depois de um restore já conferido)")
    args = ap.parse_args()

    folder = Path(args.backup)
    dump = folder / "database.dump"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    counts = json.loads((folder / "row_counts.json").read_text(encoding="utf-8")) if (folder / "row_counts.json").exists() else {}

    target_raw = os.getenv("TARGET_DATABASE_URL")
    if not target_raw:
        sys.exit("TARGET_DATABASE_URL não definida (connection string do banco NOVO).")
    t = parse_database_url(target_raw)
    src_raw = os.getenv("DATABASE_URL", "")
    if src_raw:
        s = parse_database_url(src_raw)
        if (s["host"], s["port"], s["dbname"], s["user"]) == (t["host"], t["port"], t["dbname"], t["user"]):
            sys.exit("O destino é IGUAL à DATABASE_URL de origem. Recusado: este script só restaura em um banco novo.")

    print(f"Backup:  {folder}  ({manifest['size_bytes'] / 1048576:.1f} MB, {manifest.get('tables')} tabelas, "
          f"Alembic {manifest.get('alembic_version')})")
    print(f"Destino: {t['dbname']} @ {t['host']}:{t['port']}  (usuário {t['user']})")
    if sha256(dump) != manifest["sha256"]:
        sys.exit("SHA-256 do database.dump NÃO bate com o manifest.json: backup corrompido. Abortando.")
    print("SHA-256 do dump confere.")
    if args.only_urls:
        old_url, new_url = os.getenv("OLD_SUPABASE_URL"), os.getenv("TARGET_SUPABASE_URL")
        if not (old_url and new_url):
            sys.exit("Defina OLD_SUPABASE_URL e TARGET_SUPABASE_URL.")
        print(f"Trocando '{old_url.rstrip('/')}' por '{new_url.rstrip('/')}' em object_storage_files.public_url ...")
        asyncio.run(fix_urls(target_raw, old_url.rstrip("/"), new_url.rstrip("/")))
        return
    if args.dry_run:
        return
    if not args.yes and input(f"Restaurar em {t['host']}? Digite o host para confirmar: ").strip() != t["host"]:
        sys.exit("Cancelado.")

    mode, prefix = runner(dump)
    env = {**os.environ, "PGPASSWORD": t["password"], "PGSSLMODE": t["sslmode"]}
    conn = ["-h", t["host"], "-p", t["port"], "-U", t["user"], "-d", t["dbname"]]
    dump_arg = "/backup/database.dump" if mode == "docker" else str(dump)

    print(f"\n[1/4] Habilitando pgvector no destino ({mode})...")
    r = subprocess.run(prefix + ["psql", *conn, "-v", "ON_ERROR_STOP=1", "-c",
                                 "CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public"],
                       env=env, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("Não consegui criar a extensão vector:\n" + r.stderr.strip())

    print("[2/4] pg_restore (alguns avisos como 'schema public already exists' são normais)...")
    r = subprocess.run(prefix + ["pg_restore", *conn, "--no-owner", "--no-privileges", "--verbose", dump_arg],
                       env=env, capture_output=True, text=True)
    # a linha-resumo "errors ignored on restore: N" só repete erros já listados (aqui, os benignos)
    errors = [ln for ln in r.stderr.splitlines()
              if "error" in ln.lower() and "errors ignored on restore" not in ln.lower()]
    benign = [ln for ln in errors if "already exists" in ln]
    real = [ln for ln in errors if ln not in benign]
    print(f"      pg_restore: código {r.returncode}, {len(benign)} avisos benignos, {len(real)} erros reais")
    for ln in real[:15]:
        print("      ✗", ln[:200])

    print("[3/4] Conferindo contagens de linhas...")
    ok = asyncio.run(verify(target_raw, counts))

    old, new = os.getenv("OLD_SUPABASE_URL"), os.getenv("TARGET_SUPABASE_URL")
    if old and new and ok:
        print("[4/4] Corrigindo public_url (URL antiga do Storage -> nova)...")
        asyncio.run(fix_urls(target_raw, old.rstrip("/"), new.rstrip("/")))
    else:
        print("[4/4] public_url: pulado (defina OLD_SUPABASE_URL e TARGET_SUPABASE_URL, e confira as contagens).")

    if real or not ok:
        sys.exit("\nRestauração COM PROBLEMAS. Veja as mensagens acima antes de apontar o app para o banco novo.")
    print("\n✔ Banco restaurado e conferido. Próximo: restore_storage.py e trocar as variáveis do Azure.")


async def _db(raw: str):
    from infrastructure.database_context.database import Database
    return Database(raw)


async def verify(raw: str, counts: dict) -> bool:
    from sqlalchemy import text
    db = await _db(raw)
    bad = 0
    async with db.session() as s:
        ver = (await s.execute(text("SELECT version_num FROM alembic_version"))).scalar()
        print(f"      Alembic no destino: {ver} (backup: {counts.get('alembic_version')})")
        for name, expected in counts.get("tables", {}).items():
            try:
                got = (await s.execute(text(f'SELECT count(*) FROM "{name}"'))).scalar()
            except Exception as e:  # noqa: BLE001
                print(f"      ✗ {name}: não existe no destino ({type(e).__name__})")
                bad += 1
                continue
            if got != expected:
                print(f"      ✗ {name}: backup {expected} linhas, destino {got}")
                bad += 1
    print("      todas as tabelas conferem." if not bad else f"      {bad} tabela(s) com diferença.")
    return bad == 0


async def fix_urls(raw: str, old: str, new: str) -> None:
    from sqlalchemy import text
    db = await _db(raw)
    async with db.session() as s:
        res = await s.execute(
            text("UPDATE object_storage_files SET public_url = replace(public_url, :old, :new) WHERE public_url LIKE :like"),
            {"old": old, "new": new, "like": old + "%"},
        )
        await s.commit()
        print(f"      {res.rowcount} linha(s) de object_storage_files atualizadas.")


if __name__ == "__main__":
    main()
