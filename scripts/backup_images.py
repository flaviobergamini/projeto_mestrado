"""Backup de TODAS as imagens do bucket do Supabase Storage para o seu computador.

Somente leitura: não altera nada no Storage nem no banco. Rode ANTES de
`recompress_images.py` — aquele script se recusa a mexer em qualquer imagem que
não esteja neste backup (com o mesmo tamanho).

Uso (na pasta agents-backend, com o .env preenchido — SUPABASE_URL/KEY/BUCKET e
DATABASE_URL):

    python scripts/backup_images.py
    python scripts/backup_images.py --out D:\\Backups\\smartpei_images

O que grava em <out>:
    files/<object_key>          as imagens, com a mesma estrutura de pastas do bucket
    object_storage_files.json   cópia da tabela do banco (para poder restaurar os links)
    manifest.json               lista de arquivos, tamanhos e SHA-256

É retomável: rodar de novo pula o que já foi baixado com o mesmo tamanho.
"""
import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from supabase import create_client  # noqa: E402

BUCKET = os.getenv("SUPABASE_BUCKET", "agents-buket")
PAGE = 100


def list_bucket(client, prefix: str = "") -> list[dict]:
    """Lista recursivamente todos os arquivos do bucket (pastas aparecem com id None)."""
    files: list[dict] = []
    offset = 0
    while True:
        items = client.storage.from_(BUCKET).list(
            prefix, {"limit": PAGE, "offset": offset, "sortBy": {"column": "name", "order": "asc"}}
        )
        if not items:
            break
        for it in items:
            name = it.get("name")
            path = f"{prefix}/{name}" if prefix else name
            if it.get("id") is None:  # pasta
                files.extend(list_bucket(client, path))
            else:
                size = (it.get("metadata") or {}).get("size")
                files.append({"path": path, "size": size})
        if len(items) < PAGE:
            break
        offset += PAGE
    return files


def download_one(client, path: str, dest: Path, expected_size) -> dict:
    if dest.exists() and (expected_size is None or dest.stat().st_size == expected_size):
        return {"path": path, "status": "skipped", "size": dest.stat().st_size}
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err = None
    for attempt in range(3):
        try:
            data = client.storage.from_(BUCKET).download(path)
            if expected_size is not None and len(data) != expected_size:
                raise IOError(f"tamanho difere: baixou {len(data)}, esperado {expected_size}")
            tmp = dest.with_suffix(dest.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(dest)
            return {"path": path, "status": "downloaded", "size": len(data)}
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    return {"path": path, "status": "failed", "error": str(last_err)}


async def dump_db_table(out: Path) -> int:
    from sqlalchemy import text
    from infrastructure.database_context.database import Database

    db = Database(os.environ["DATABASE_URL"])
    async with db.session() as s:
        res = await s.execute(text("SELECT * FROM object_storage_files"))
        rows = [dict(r._mapping) for r in res.fetchall()]
    (out / "object_storage_files.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return len(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Backup das imagens do Supabase Storage")
    default_out = Path.home() / "Backups" / "smartpei_images"
    parser.add_argument("--out", default=str(default_out), help=f"Pasta de destino (padrão: {default_out})")
    parser.add_argument("--workers", type=int, default=6, help="Downloads em paralelo (padrão 6)")
    args = parser.parse_args()

    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        sys.exit("SUPABASE_URL / SUPABASE_KEY não definidos no .env")

    out = Path(args.out)
    files_dir = out / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    client = create_client(url, key)
    print(f"Bucket: {BUCKET}\nDestino: {out}\n\nListando arquivos do bucket...")
    remote = list_bucket(client)
    total = sum(f["size"] or 0 for f in remote)
    print(f"  {len(remote)} arquivos, {total / 1048576:.1f} MB\n")

    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(download_one, client, f["path"], files_dir / f["path"], f["size"]) for f in remote
        ]
        for fut in as_completed(futures):
            results.append(fut.result())
            done += 1
            if done % 25 == 0 or done == len(remote):
                print(f"  {done}/{len(remote)}")

    failed = [r for r in results if r["status"] == "failed"]
    manifest = {
        "created_at": datetime.now().isoformat(),
        "bucket": BUCKET,
        "files": [],
    }
    for r in sorted(results, key=lambda x: x["path"]):
        if r["status"] == "failed":
            manifest["files"].append({"path": r["path"], "status": "failed", "error": r["error"]})
            continue
        manifest["files"].append({
            "path": r["path"],
            "size": r["size"],
            "sha256": sha256(files_dir / r["path"]),
        })
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        n = asyncio.run(dump_db_table(out))
        print(f"\nTabela object_storage_files exportada ({n} linhas)")
    except Exception as e:  # noqa: BLE001
        print(f"\n⚠ Não consegui exportar a tabela do banco: {e}")

    downloaded = sum(1 for r in results if r["status"] == "downloaded")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    print(f"\nBaixadas: {downloaded} | Já existiam: {skipped} | Falhas: {len(failed)}")
    for r in failed:
        print(f"  ✗ {r['path']}: {r['error']}")
    print(f"Backup em: {out}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
