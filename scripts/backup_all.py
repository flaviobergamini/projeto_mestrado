"""Backup de PRODUÇÃO completo: banco de dados + storage, na mesma pasta datada, no seu computador.

SOMENTE LEITURA em produção. Roda `backup_database.py` e depois `backup_storage.py`.

Uso (na pasta agents-backend; o .env/ambiente deve ter as variáveis de PRODUÇÃO — DATABASE_URL,
SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET. Nunca cole chaves no chat):

    python scripts/backup_all.py
    python scripts/backup_all.py --out D:\\Backups\\smartpei
    python scripts/backup_all.py --only db          # só o banco
    python scripts/backup_all.py --only storage     # só o storage

Resultado: <out>/<data-hora>/db/... e <out>/<data-hora>/storage/...
Dica: confira o apontamento ANTES (a URL do banco é de produção, não do ambiente local?):
    python scripts/backup_all.py --dry-run
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(HERE.parent / ".env")


def target_summary() -> list[str]:
    """Mostra para onde o backup vai apontar (host/banco/bucket), sem expor senhas nem chaves."""
    lines = []
    db = os.getenv("DATABASE_URL", "")
    if db:
        p = urlparse(db.replace("postgresql+asyncpg://", "postgresql://"))
        lines.append(f"Banco:   {(p.path or '/').lstrip('/')} @ {p.hostname}:{p.port or 5432}")
    else:
        lines.append("Banco:   (DATABASE_URL não definida)")
    sb = os.getenv("SUPABASE_URL", "")
    lines.append(f"Storage: {urlparse(sb).hostname or '(SUPABASE_URL não definida)'}  bucket={os.getenv('SUPABASE_BUCKET', 'agents-buket')}")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup completo de produção (banco + storage)")
    default_out = Path.home() / "Backups" / "smartpei"
    parser.add_argument("--out", default=str(default_out), help=f"Pasta de destino (padrão: {default_out})")
    parser.add_argument("--only", choices=["db", "storage"], help="Rodar só uma das partes")
    parser.add_argument("--dry-run", action="store_true", help="Só mostra o alvo e o destino, sem copiar nada")
    parser.add_argument("--yes", action="store_true", help="Não pedir confirmação")
    args = parser.parse_args()

    root = Path(args.out) / datetime.now().strftime("%Y%m%d_%H%M%S")
    print("Alvo do backup (leitura apenas):")
    for ln in target_summary():
        print("  " + ln)
    print(f"Destino: {root}\n")
    if args.dry_run:
        return
    if not args.yes and input("Esses dados são de PRODUÇÃO? Continuar? [s/N] ").strip().lower() not in ("s", "sim", "y", "yes"):
        sys.exit("Cancelado.")

    steps = []
    if args.only in (None, "db"):
        steps.append(("Banco de dados", [sys.executable, str(HERE / "backup_database.py"), "--out", str(root / "db")]))
    if args.only in (None, "storage"):
        steps.append(("Storage", [sys.executable, str(HERE / "backup_storage.py"), "--out", str(root / "storage")]))

    failures = []
    for name, cmd in steps:
        print(f"\n===== {name} =====")
        if subprocess.run(cmd, cwd=HERE.parent).returncode != 0:
            failures.append(name)
            print(f"✗ {name}: falhou (veja as mensagens acima)")

    print("\n" + "=" * 40)
    if failures:
        sys.exit(f"Backup INCOMPLETO. Falharam: {', '.join(failures)}")
    print(f"✔ Backup completo em: {root}")


if __name__ == "__main__":
    main()
