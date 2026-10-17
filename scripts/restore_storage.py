"""Envia um backup do Storage (feito por backup_storage.py) para o bucket de OUTRO projeto Supabase.

Escreve SOMENTE no projeto de destino (TARGET_*). Recusa rodar se TARGET_SUPABASE_URL for igual ao
SUPABASE_URL de origem. É retomável: pula o que já existe no destino com o mesmo tamanho.

Variáveis (no .env ou no ambiente — NUNCA cole chaves no chat):
    TARGET_SUPABASE_URL=https://<ref-novo>.supabase.co
    TARGET_SUPABASE_KEY=<service_role key do projeto NOVO>
    TARGET_SUPABASE_BUCKET=agents-buket          # o mesmo nome do bucket de origem (as chaves dos objetos são as mesmas)

Uso (na pasta agents-backend):
    python scripts/restore_storage.py --backup C:\\Users\\...\\Backups\\smartpei\\<data>\\storage\\smartpei_storage_<data-hora>
    python scripts/restore_storage.py --backup <pasta> --dry-run

O que faz:
    1. Confere SHA-256 e tamanho de cada arquivo do backup contra o manifest.json.
    2. Cria o bucket PRIVADO se não existir (o app usa links assinados).
    3. Envia cada arquivo para o mesmo caminho (object_key) com o content-type correto.
    4. Lista o bucket de destino e confere se todos os arquivos chegaram com o tamanho certo.
"""
import argparse
import hashlib
import json
import mimetypes
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from supabase import create_client  # noqa: E402

PAGE = 100
_local = threading.local()


def thread_client(url: str, key: str):
    """Um cliente Supabase por thread: o cliente HTTP/2 compartilhado derruba conexões sob concorrência."""
    c = getattr(_local, "client", None)
    if c is None:
        c = _local.client = create_client(url, key)
    return c


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def list_remote(client, bucket: str, prefix: str = "") -> dict[str, int | None]:
    out: dict[str, int | None] = {}
    offset = 0
    while True:
        items = client.storage.from_(bucket).list(prefix, {"limit": PAGE, "offset": offset})
        if not items:
            break
        for it in items:
            path = f"{prefix}/{it['name']}" if prefix else it["name"]
            if it.get("id") is None:
                out.update(list_remote(client, bucket, path))
            else:
                out[path] = (it.get("metadata") or {}).get("size")
        if len(items) < PAGE:
            break
        offset += PAGE
    return out


def upload_one(url: str, key: str, bucket: str, rel: str, local: Path, existing: dict) -> dict:
    size = local.stat().st_size
    if existing.get(rel) == size:
        return {"path": rel, "status": "skipped"}
    ctype = mimetypes.guess_type(rel)[0] or "application/octet-stream"
    last = None
    for attempt in range(5):
        try:
            thread_client(url, key).storage.from_(bucket).upload(
                path=rel, file=local.read_bytes(), file_options={"content-type": ctype, "upsert": "true"},
            )
            return {"path": rel, "status": "uploaded"}
        except Exception as e:  # noqa: BLE001
            last = e
            _local.client = None  # conexão pode estar quebrada: recria na próxima tentativa
            time.sleep(2 * (attempt + 1))
    return {"path": rel, "status": "failed", "error": str(last)}


def main() -> None:
    ap = argparse.ArgumentParser(description="Envia o backup do Storage para o bucket NOVO (destino)")
    ap.add_argument("--backup", required=True, help="Pasta smartpei_storage_<data-hora> (com files/ e manifest.json)")
    ap.add_argument("--workers", type=int, default=3, help="Envios em paralelo (padrão 3)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    folder = Path(args.backup)
    files_dir = folder / "files"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    entries = [f for f in manifest["files"] if f.get("status") != "failed"]

    url, key, bucket = os.getenv("TARGET_SUPABASE_URL"), os.getenv("TARGET_SUPABASE_KEY"), os.getenv("TARGET_SUPABASE_BUCKET")
    if not (url and key and bucket):
        sys.exit("Defina TARGET_SUPABASE_URL, TARGET_SUPABASE_KEY e TARGET_SUPABASE_BUCKET (projeto NOVO).")
    if url.rstrip("/") == (os.getenv("SUPABASE_URL") or "").rstrip("/"):
        sys.exit("TARGET_SUPABASE_URL é IGUAL ao SUPABASE_URL de origem. Recusado.")

    print(f"Backup: {folder}  ({len(entries)} arquivos)\nDestino: {url}  bucket={bucket}")
    bad = [e["path"] for e in entries
           if not (files_dir / e["path"]).exists()
           or (files_dir / e["path"]).stat().st_size != e["size"]
           or sha256(files_dir / e["path"]) != e["sha256"]]
    if bad:
        sys.exit(f"{len(bad)} arquivo(s) do backup não conferem com o manifest (primeiro: {bad[0]}). Abortando.")
    print("Todos os arquivos do backup conferem (tamanho + SHA-256).")
    if manifest["files_listed"] != manifest["files_ok"]:
        print(f"⚠ O backup original tinha {manifest['files_listed'] - manifest['files_ok']} falha(s) de download.")
    if args.dry_run:
        return

    client = create_client(url, key)
    try:
        client.storage.get_bucket(bucket)
    except Exception:  # noqa: BLE001
        print(f"Criando bucket privado '{bucket}'...")
        client.storage.create_bucket(bucket, options={"public": False})

    existing = list_remote(client, bucket)
    print(f"{len(existing)} arquivo(s) já no destino. Enviando...")
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(upload_one, url, key, bucket, e["path"], files_dir / e["path"], existing) for e in entries]
        for i, f in enumerate(as_completed(futs), 1):
            results.append(f.result())
            if i % 25 == 0 or i == len(entries):
                print(f"  {i}/{len(entries)}")

    remote = list_remote(client, bucket)
    missing = [e["path"] for e in entries if e["path"] not in remote]
    wrong = [e["path"] for e in entries if e["path"] in remote and remote[e["path"]] not in (None, e["size"])]
    failed = [r for r in results if r["status"] == "failed"]
    by = lambda s: sum(1 for r in results if r["status"] == s)  # noqa: E731
    print(f"\nEnviados: {by('uploaded')} | Já existiam: {by('skipped')} | Falhas: {len(failed)}")
    for r in failed:
        print(f"  ✗ {r['path']}: {r['error']}")
    for p in missing:
        print(f"  ✗ ausente no destino: {p}")
    for p in wrong:
        print(f"  ✗ tamanho diferente no destino: {p}")
    if failed or missing or wrong:
        sys.exit(1)
    print(f"✔ {len(entries)} arquivos no bucket '{bucket}' conferidos (existência e tamanho).")


if __name__ == "__main__":
    main()
