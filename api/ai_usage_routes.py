"""AI usage tracking endpoints."""

import os
from datetime import date
from fastapi import APIRouter, Depends, Query
from typing import Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from infrastructure.repositories.ai_usage_repository import AiUsageRepository, PRICING, PRICING_REF_DATE

router = APIRouter(prefix="/ai-usage", tags=["AI Usage"])


@router.get("/logs")
@inject
async def list_usage_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    model: Optional[str] = Query(None),
    operation: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: dict = Depends(require_roles("admin")),
    repo: AiUsageRepository = Depends(Provide[Container.ai_usage_repository]),
):
    return await repo.list_paginated(
        page=page, page_size=page_size,
        model=model, operation=operation,
        date_from=date_from, date_to=date_to,
    )


@router.get("/summary")
@inject
async def usage_summary(
    current_user: dict = Depends(require_roles("admin")),
    repo: AiUsageRepository = Depends(Provide[Container.ai_usage_repository]),
):
    by_model = await repo.summary_by_model()
    by_operation = await repo.summary_by_operation()
    daily = await repo.daily_usage(days=14)
    distinct = await repo.distinct_values()
    return {
        "by_model": by_model,
        "by_operation": by_operation,
        "daily": daily,
        "distinct": distinct,
    }


@router.get("/rate-status")
@inject
async def rate_status(
    current_user: dict = Depends(require_roles("admin")),
    repo: AiUsageRepository = Depends(Provide[Container.ai_usage_repository]),
):
    """Returns current RPM/TPM/RPD and configured limits from env vars."""
    current = await repo.rate_status()
    models_summary = await repo.summary_by_model()

    model_limits = []
    for m in models_summary:
        name = m["model"]
        env_key = name.upper().replace("-", "_").replace("/", "_").replace("MODELS_", "")
        rpm_limit = os.getenv(f"GOOGLE_RATE_LIMIT_{env_key}_RPM")
        tpm_limit = os.getenv(f"GOOGLE_RATE_LIMIT_{env_key}_TPM")
        rpd_limit = os.getenv(f"GOOGLE_RATE_LIMIT_{env_key}_RPD")
        model_limits.append({
            "model": name,
            "requests": m["requests"],
            "cost_usd": m["cost_usd"],
            "rpm_limit": int(rpm_limit) if rpm_limit else None,
            "tpm_limit": int(tpm_limit) if tpm_limit else None,
            "rpd_limit": int(rpd_limit) if rpd_limit else None,
        })

    return {
        "current": current,
        "models": model_limits,
        "pricing": {k: v for k, v in PRICING.items()},
        "pricing_ref_date": PRICING_REF_DATE,
    }
