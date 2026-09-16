"""Repository for AI model usage logs — stores token counts, cost, and timing per call."""

import logging
from datetime import datetime, date, timedelta
from typing import Optional
from sqlalchemy import select, func, and_, cast, Date
from infrastructure.database_context.database import Database
from infrastructure.models.ai_usage_log import AiUsageLog

logger = logging.getLogger(__name__)

# ── Pricing table (USD per token) ────────────────────────────────────────────
# Source: ai.google.dev/gemini-api/docs/pricing (checked 2026-09-16)
# "input_audio" é o preço cobrado quando a entrada é áudio (transcrição de
# diário/família) — mais caro que texto/imagem/vídeo na tabela do Gemini.
PRICING: dict[str, dict[str, float]] = {
    "gemini-2.5-flash": {"input": 0.30 / 1_000_000, "input_audio": 1.00 / 1_000_000, "output": 2.50 / 1_000_000},
    "gemini-2.5-flash-preview-05-20": {"input": 0.30 / 1_000_000, "input_audio": 1.00 / 1_000_000, "output": 2.50 / 1_000_000},
    "gemini-2.0-flash": {"input": 0.10 / 1_000_000, "input_audio": 0.70 / 1_000_000, "output": 0.40 / 1_000_000},
    "gemini-1.5-flash": {"input": 0.075 / 1_000_000, "input_audio": 0.25 / 1_000_000, "output": 0.30 / 1_000_000},
    "gemini-embedding-001": {"input": 0.15 / 1_000_000, "output": 0.0},
    "models/gemini-embedding-001": {"input": 0.15 / 1_000_000, "output": 0.0},
}

PRICING_REF_DATE = "2026-09-16"

# Operações cujo input é áudio (não texto) — usam a tarifa "input_audio" em
# vez da tarifa padrão de entrada.
AUDIO_INPUT_OPERATIONS = {"diary_audio_transcription", "family_audio_transcription"}


def _calc_cost(model: str, input_tokens: int, output_tokens: int, is_audio_input: bool = False) -> float:
    """Calculate cost in USD based on the pricing table."""
    p = None
    for key, prices in PRICING.items():
        if model.endswith(key) or key.endswith(model) or model == key:
            p = prices
            break
    if p is None:
        # Fallback to gemini-2.0-flash pricing for unknown models
        p = {"input": 0.10 / 1_000_000, "input_audio": 0.70 / 1_000_000, "output": 0.40 / 1_000_000}
    input_price = p.get("input_audio", p["input"]) if is_audio_input else p["input"]
    return round(input_tokens * input_price + output_tokens * p["output"], 8)


class AiUsageRepository:
    def __init__(self, database: Database):
        self._db = database

    async def log(
        self,
        model: str,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int | None = None,
        duration_ms: int | None = None,
        user_id: str | None = None,
        username: str | None = None,
    ) -> None:
        cost = _calc_cost(model, input_tokens, output_tokens, is_audio_input=operation in AUDIO_INPUT_OPERATIONS)
        if total_tokens is None:
            total_tokens = input_tokens + output_tokens
        try:
            async with self._db.session() as session:
                session.add(AiUsageLog(
                    model=model,
                    operation=operation,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    duration_ms=duration_ms,
                    cost_usd=cost,
                    user_id=user_id,
                    username=username,
                ))
                await session.commit()
        except Exception:
            logger.debug("AiUsageLog insert failed silently", exc_info=True)

    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        model: str | None = None,
        operation: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        offset = (page - 1) * page_size
        filters = []
        if model:
            filters.append(AiUsageLog.model == model)
        if operation:
            filters.append(AiUsageLog.operation == operation)
        if date_from:
            filters.append(AiUsageLog.created_at >= datetime(date_from.year, date_from.month, date_from.day))
        if date_to:
            dt_to = datetime(date_to.year, date_to.month, date_to.day) + timedelta(days=1)
            filters.append(AiUsageLog.created_at < dt_to)

        where = and_(*filters) if filters else True

        async with self._db.session() as session:
            total_result = await session.execute(
                select(func.count()).select_from(AiUsageLog).where(where)
            )
            total = total_result.scalar() or 0

            # Totals for filtered set
            totals_result = await session.execute(
                select(
                    func.coalesce(func.sum(AiUsageLog.input_tokens), 0),
                    func.coalesce(func.sum(AiUsageLog.output_tokens), 0),
                    func.coalesce(func.sum(AiUsageLog.total_tokens), 0),
                    func.coalesce(func.sum(AiUsageLog.cost_usd), 0.0),
                ).where(where)
            )
            row = totals_result.one()
            totals = {
                "input_tokens": int(row[0]),
                "output_tokens": int(row[1]),
                "total_tokens": int(row[2]),
                "cost_usd": round(float(row[3]), 6),
            }

            items_result = await session.execute(
                select(AiUsageLog)
                .where(where)
                .order_by(AiUsageLog.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            items = [self._to_dict(r) for r in items_result.scalars().all()]

        return {
            "items": items,
            "totals": totals,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
        }

    async def summary_by_model(self) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(
                    AiUsageLog.model,
                    func.count(AiUsageLog.id).label("requests"),
                    func.coalesce(func.sum(AiUsageLog.input_tokens), 0).label("input_tokens"),
                    func.coalesce(func.sum(AiUsageLog.output_tokens), 0).label("output_tokens"),
                    func.coalesce(func.sum(AiUsageLog.total_tokens), 0).label("total_tokens"),
                    func.coalesce(func.sum(AiUsageLog.cost_usd), 0.0).label("cost_usd"),
                    func.coalesce(func.avg(AiUsageLog.duration_ms), 0).label("avg_duration_ms"),
                )
                .group_by(AiUsageLog.model)
                .order_by(func.sum(AiUsageLog.cost_usd).desc())
            )
            return [
                {
                    "model": r.model,
                    "requests": r.requests,
                    "input_tokens": int(r.input_tokens),
                    "output_tokens": int(r.output_tokens),
                    "total_tokens": int(r.total_tokens),
                    "cost_usd": round(float(r.cost_usd), 6),
                    "avg_duration_ms": int(r.avg_duration_ms or 0),
                }
                for r in result.all()
            ]

    async def summary_by_operation(self) -> list[dict]:
        async with self._db.session() as session:
            result = await session.execute(
                select(
                    AiUsageLog.operation,
                    func.count(AiUsageLog.id).label("requests"),
                    func.coalesce(func.sum(AiUsageLog.total_tokens), 0).label("total_tokens"),
                    func.coalesce(func.sum(AiUsageLog.cost_usd), 0.0).label("cost_usd"),
                )
                .group_by(AiUsageLog.operation)
                .order_by(func.sum(AiUsageLog.cost_usd).desc())
            )
            return [
                {
                    "operation": r.operation,
                    "requests": r.requests,
                    "total_tokens": int(r.total_tokens),
                    "cost_usd": round(float(r.cost_usd), 6),
                }
                for r in result.all()
            ]

    async def daily_usage(self, days: int = 14) -> list[dict]:
        """Returns daily aggregated usage for the last N days."""
        since = datetime.utcnow() - timedelta(days=days)
        async with self._db.session() as session:
            day_col = cast(AiUsageLog.created_at, Date).label("day")
            result = await session.execute(
                select(
                    day_col,
                    func.coalesce(func.sum(AiUsageLog.input_tokens), 0).label("input_tokens"),
                    func.coalesce(func.sum(AiUsageLog.output_tokens), 0).label("output_tokens"),
                    func.coalesce(func.sum(AiUsageLog.total_tokens), 0).label("total_tokens"),
                    func.coalesce(func.sum(AiUsageLog.cost_usd), 0.0).label("cost_usd"),
                    func.count(AiUsageLog.id).label("requests"),
                )
                .where(AiUsageLog.created_at >= since)
                .group_by(cast(AiUsageLog.created_at, Date))
                .order_by(cast(AiUsageLog.created_at, Date))
            )
            return [
                {
                    "day": r.day.strftime("%Y-%m-%d") if r.day else "",
                    "input_tokens": int(r.input_tokens),
                    "output_tokens": int(r.output_tokens),
                    "total_tokens": int(r.total_tokens),
                    "cost_usd": round(float(r.cost_usd), 6),
                    "requests": r.requests,
                }
                for r in result.all()
            ]

    async def rate_status(self) -> dict:
        """Returns current RPM, TPM, RPD counts (last minute / last day)."""
        now = datetime.utcnow()
        one_min_ago = now - timedelta(minutes=1)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        async with self._db.session() as session:
            rpm_res = await session.execute(
                select(func.count(AiUsageLog.id))
                .where(AiUsageLog.created_at >= one_min_ago)
            )
            rpm = int(rpm_res.scalar() or 0)

            tpm_res = await session.execute(
                select(func.coalesce(func.sum(AiUsageLog.total_tokens), 0))
                .where(AiUsageLog.created_at >= one_min_ago)
            )
            tpm = int(tpm_res.scalar() or 0)

            rpd_res = await session.execute(
                select(func.count(AiUsageLog.id))
                .where(AiUsageLog.created_at >= today_start)
            )
            rpd = int(rpd_res.scalar() or 0)

        return {"rpm": rpm, "tpm": tpm, "rpd": rpd}

    async def distinct_values(self) -> dict:
        async with self._db.session() as session:
            models_r = await session.execute(select(AiUsageLog.model).distinct())
            ops_r = await session.execute(select(AiUsageLog.operation).distinct())
        return {
            "models": sorted([r[0] for r in models_r.all()]),
            "operations": sorted([r[0] for r in ops_r.all()]),
            "pricing_ref_date": PRICING_REF_DATE,
        }

    def _to_dict(self, row: AiUsageLog) -> dict:
        return {
            "id": row.id,
            "model": row.model,
            "operation": row.operation,
            "input_tokens": row.input_tokens,
            "output_tokens": row.output_tokens,
            "total_tokens": row.total_tokens,
            "duration_ms": row.duration_ms,
            "cost_usd": row.cost_usd,
            "user_id": row.user_id,
            "username": row.username,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
