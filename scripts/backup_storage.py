"""Backup completo do Supabase Storage (TODOS os arquivos do bucket) para o seu computador.

SOMENTE LEITURA: só lista e baixa; não altera nada no Storage nem no banco.
Reaproveita as funções de `backup_images.py`, mas aqui o backup é versionado por data, confere cada
arquivo (tamanho + SHA-256) e termina com um relatório.

Uso (na pasta agents-backend, com SUPABASE_URL / SUPABASE_KEY / SUPABASE_BUCKET e DATABASE_URL no .env
ou no ambiente — as de PRODUÇÃO; nunca cole chaves no chat):

    python scripts/backup_storage.py
    python scripts/backup_storage.py --out D:\\Backups\\smartpei_storage
    python scripts/backup_storage.py --bucket outro-bucket --workers 8

Grava em <out>/smartpei_storage_<data-hora>/:
    files/<caminho no bucket>      os arquivos, com a mesma estrutura de pastas
    object_storage_files.json      cópia da tabela do banco que mapeia arquivos ↔ registros
    manifest.json                  lista de arquivos, tamanhos e SHA-256 (+ falhas, se houver)

Para economizar tempo/espaço em backups seguidos, use --reuse <pasta de um backup anterior>: arquivos
idênticos (mesmo tamanho) são copiados dali em vez de baixados de novo.

ATENÇÃO: contém fotos/vídeos de crianças. Guarde em disco criptografado e fora de pastas sincronizadas.
"""
import argparse
import asyncio
import json
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import backup_images as bi  # noqa: E402  (carrega o .env e fornece list_bucket/download_one/sha256)
from supabase import create_client  # noqa: E402


def fetch(client, rel: str, dest: Path, size, reuse_root: Path | None) -> dict:
    """Copia de um backup anterior se idêntico; senão baixa."""
    if reuse_root:
        old = reuse_root / "files" / rel
        if old.exists() and size is not None and old.stat().st_size == size and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old, dest)
            return {"path": rel, "status": "reused", "size": size}
    return bi.download_one(client, rel, dest, size)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup completo do Supabase Storage (somente leitura)")
    default_out = Path.home() / "Backups" / "smartpei_storage"
    parser.add_argument("--out", default=str(default_out), help=f"Pasta de destino (padrão: {default_out})")
    parser.add_argument("--bucket", default=bi.BUCKET, help=f"Bucket (padrão: {bi.BUCKET})")
    parser.add_argument("--workers", type=int, default=6, help="Downloads em paralelo (padrão 6)")
    parser.add_argument("--reuse", default=None, help="Pasta de um backup anterior para reaproveitar arquivos idênticos")
    args = parser.parse_args()

    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        sys.exit("SUPABASE_URL / SUPABASE_KEY não definidos (use os de PRODUÇÃO no .env ou no ambiente).")
    bi.BUCKET = args.bucket  # as funções reaproveitadas leem o bucket deste módulo

    dest = Path(args.out) / f"smartpei_storage_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    files_dir = dest / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    reuse_root = Path(args.reuse) if args.reuse else None

    client = create_client(url, key)
    print(f"Bucket: {args.bucket}\nDestino: {dest}\n\nListando arquivos do bucket...")
    remote = bi.list_bucket(client)
    total = sum(f["size"] or 0 for f in remote)
    print(f"  {len(remote)} arquivos, {total / 1048576:.1f} MB\n")

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(fetch, client, f["path"], files_dir / f["path"], f["size"], reuse_root) for f in remote
        ]
        for i, fut in enumerate(as_completed(futures), 1):
            results.append(fut.result())
            if i % 25 == 0 or i == len(remote):
                print(f"  {i}/{len(remote)}")

    # verificação: tudo que foi listado precisa estar no disco com o tamanho certo
    sizes = {f["path"]: f["size"] for f in remote}
    manifest_files, failed, mismatched = [], [], []
    for r in sorted(results, key=lambda x: x["path"]):
        if r["status"] == "failed":
            failed.append(r)
            manifest_files.append({"path": r["path"], "status": "failed", "error": r["error"]})
            continue
        local = files_dir / r["path"]
        if sizes.get(r["path"]) is not None and local.stat().st_size != sizes[r["path"]]:
            mismatched.append(r["path"])
        manifest_files.append({"path": r["path"], "size": local.stat().st_size, "sha256": bi.sha256(local)})

    manifest = {
        "created_at": datetime.now().isoformat(), "bucket": args.bucket,
        "files_listed": len(remote), "files_ok": len(manifest_files) - len(failed),
        "total_bytes": sum(f.get("size", 0) for f in manifest_files), "files": manifest_files,
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if os.getenv("DATABASE_URL"):
        try:
            n = asyncio.run(bi.dump_db_table(dest))
            print(f"\nTabela object_storage_files exportada ({n} linhas)")
        except Exception as e:  # noqa: BLE001
            print(f"\n⚠ Não consegui exportar a tabela do banco: {e}")

    by = lambda s: sum(1 for r in results if r["status"] == s)  # noqa: E731
    print(f"\nBaixados: {by('downloaded')} | Reaproveitados: {by('reused')} | Já existiam: {by('skipped')} | Falhas: {len(failed)}")
    for r in failed:
        print(f"  ✗ {r['path']}: {r['error']}")
    for p in mismatched:
        print(f"  ✗ tamanho diferente do bucket: {p}")
    print(f"Backup em: {dest}")
    if failed or mismatched:
        sys.exit(1)
    print("✔ Todos os arquivos listados foram salvos e conferidos.")


if __name__ == "__main__":
    main()
