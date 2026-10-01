"""Recomprime as imagens JÁ existentes no Storage (1920x1080, JPEG 80%), reenvia
e atualiza os links no banco (tabela object_storage_files).

SEGURANÇA
  - Por padrão é SIMULAÇÃO: só calcula quanto espaço economizaria. Nada é gravado
    até você passar --apply.
  - Exige o backup feito por `backup_images.py` (--backup-dir). Uma imagem só é
    alterada se existir no backup com EXATAMENTE o mesmo tamanho do banco.
  - Idempotente: imagem cujo resultado não ficar pelo menos 10% menor é ignorada,
    então rodar de novo não recomprime (e não degrada) o que já foi comprimido.
  - O objeto antigo só é apagado com --delete-old (relevante só p/ PNG/GIF/WebP,
    cuja chave muda de extensão para .jpg; JPEGs são sobrescritos no mesmo lugar).

Uso (na pasta agents-backend):
    python scripts/recompress_images.py --backup-dir "C:\\Users\\voce\\Backups\\smartpei_images"            # simulação
    python scripts/recompress_images.py --backup-dir "..." --apply --limit 5                              # teste com 5
    python scripts/recompress_images.py --backup-dir "..." --apply --delete-old                           # tudo
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from sqlalchemy import select  # noqa: E402

from infrastructure.database_context.database import Database  # noqa: E402
from infrastructure.models.object_storage_file import ObjectStorageFile  # noqa: E402
from infrastructure.services.storage_service import StorageService  # noqa: E402
from infrastructure.utils.image_compression import InvalidImageError, compress_image  # noqa: E402

MIN_SAVING_RATIO = 0.90  # só reenvia se o novo arquivo for <= 90% do original


def jpg_key(key: str) -> str:
    return key.rsplit(".", 1)[0] + ".jpg" if "." in key.rsplit("/", 1)[-1] else key + ".jpg"


def mb(n: int) -> str:
    return f"{n / 1048576:.2f} MB"


async def process(row: ObjectStorageFile, backup_files: Path, storage: StorageService, db: Database,
                  apply: bool, delete_old: bool) -> dict:
    res = {"id": row.id, "key": row.object_key, "old_size": row.size_bytes}
    local = backup_files / row.object_key
    if not local.exists():
        return {**res, "status": "sem_backup"}
    original = local.read_bytes()
    if len(original) != row.size_bytes:
        return {**res, "status": "backup_tamanho_diferente",
                "detail": f"backup={len(original)} banco={row.size_bytes}"}

    try:
        comp = await asyncio.to_thread(compress_image, original)
    except InvalidImageError as e:
        return {**res, "status": "imagem_invalida", "detail": str(e)}

    res["new_size"] = comp.size
    res["dimensions"] = f"{comp.width}x{comp.height}"
    if comp.size > len(original) * MIN_SAVING_RATIO:
        return {**res, "status": "sem_ganho"}

    new_key = jpg_key(row.object_key)
    res["new_key"] = new_key
    if not apply:
        return {**res, "status": "simulado"}

    # 1) sobe a versão comprimida (upsert). Se falhar, nada mudou.
    new_url = None
    for attempt in range(4):
        try:
            new_url = await asyncio.to_thread(storage.upload, new_key, comp.content, comp.mime_type)
            break
        except Exception:  # noqa: BLE001 — erro de rede transitório (ex.: WinError 10035)
            if attempt == 3:
                raise
            await asyncio.sleep(1.5 * (attempt + 1))

    # 2) atualiza o link no banco
    stem = row.original_filename.rsplit(".", 1)[0] if "." in row.original_filename else row.original_filename
    async with db.session() as session:
        db_row = (await session.execute(
            select(ObjectStorageFile).where(ObjectStorageFile.id == row.id)
        )).scalars().first()
        db_row.object_key = new_key
        db_row.mime_type = comp.mime_type
        db_row.size_bytes = comp.size
        db_row.original_filename = f"{stem}.jpg"
        db_row.public_url = new_url
        await session.commit()

    # 3) só agora apaga o objeto antigo (quando a chave mudou) e se pedido
    if new_key != row.object_key and delete_old:
        deleted = await asyncio.to_thread(storage.delete, row.object_key)
        res["old_deleted"] = deleted
    return {**res, "status": "atualizado"}


async def main_async(args):
    backup_files = Path(args.backup_dir) / "files"
    if not backup_files.is_dir() or not (Path(args.backup_dir) / "manifest.json").exists():
        sys.exit(f"Backup não encontrado em {args.backup_dir} — rode scripts/backup_images.py primeiro.")

    db = Database(os.environ["DATABASE_URL"])
    storage = StorageService()

    async with db.session() as session:
        rows = (await session.execute(
            select(ObjectStorageFile)
            .where(ObjectStorageFile.deleted == False)  # noqa: E712
            .order_by(ObjectStorageFile.size_bytes.desc())
        )).scalars().all()
        # desanexa para usar fora da sessão
        for r in rows:
            session.expunge(r)

    if args.limit:
        rows = rows[: args.limit]

    mode = "APLICANDO" if args.apply else "SIMULAÇÃO (nada será gravado)"
    print(f"{mode} — {len(rows)} imagens\n")

    sem = asyncio.Semaphore(args.workers)
    results = []

    async def run(row):
        async with sem:
            try:
                r = await process(row, backup_files, storage, db, args.apply, args.delete_old)
            except Exception as e:  # noqa: BLE001
                r = {"id": row.id, "key": row.object_key, "status": "erro", "detail": str(e)}
            results.append(r)
            if len(results) % 25 == 0 or len(results) == len(rows):
                print(f"  {len(results)}/{len(rows)}")

    await asyncio.gather(*(run(r) for r in rows))

    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    changed = [r for r in results if r["status"] in ("simulado", "atualizado")]
    before = sum(r["old_size"] for r in changed)
    after = sum(r["new_size"] for r in changed)

    print("\nResumo:")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
    if changed:
        print(f"\nEspaço: {mb(before)} → {mb(after)}  (economia {mb(before - after)}, "
              f"{(1 - after / before) * 100:.0f}%)")

    report = Path(args.backup_dir) / f"recompress_report_{datetime.now():%Y%m%d_%H%M%S}.json"
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Relatório: {report}")
    if any(r["status"] in ("erro", "sem_backup", "backup_tamanho_diferente") for r in results):
        print("⚠ Há itens com problema — veja o relatório.")


def main():
    p = argparse.ArgumentParser(description="Recomprime imagens do Storage e atualiza os links no banco")
    p.add_argument("--backup-dir", required=True, help="Pasta do backup feito por backup_images.py")
    p.add_argument("--apply", action="store_true", help="Grava de verdade (sem isso, só simula)")
    p.add_argument("--delete-old", action="store_true", help="Apaga o objeto antigo quando a chave muda (PNG/GIF/WebP)")
    p.add_argument("--limit", type=int, default=0, help="Processa só as N maiores imagens (para testar)")
    p.add_argument("--workers", type=int, default=2)
    args = p.parse_args()
    if args.delete_old and not args.apply:
        p.error("--delete-old só faz sentido com --apply")
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
