import asyncio
from core.interfaces.i_ai_gateway import IAiGateway
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.services.anonymization_service import AnonymizationService, deanonymize, reanonymize
from infrastructure.services.bncc_context import BnccContext, BNCC_USAGE_RULE
from infrastructure.services.gemini_service import GeminiService
from core.services.functional_profile_content import parse_model_json


class AiGateway(IAiGateway):
    def __init__(
        self, gemini: GeminiService, usage_repo: AiUsageRepository, anonymization: AnonymizationService,
        bncc_context: BnccContext,
    ) -> None:
        self._bncc_context = bncc_context
        self._gemini = gemini
        self._usage_repo = usage_repo
        self._anonymization = anonymization

    async def build_context(self, student_id: str, sources: list[str]) -> tuple[str, dict[str, str]]:
        return await self._anonymization.build_context(student_id, sources=sources)

    async def generate_json(
        self, operation: str, system_instruction: str, prompt: str, user_id: str | None,
        with_bncc_catalog: bool = False,
    ) -> dict:
        call: dict = {"prompt": prompt, "cached_content": None, "cache_fallback_prefix": None}
        if with_bncc_catalog:
            call = await self._bncc_context.attach(BNCC_USAGE_RULE + "\n\n" + prompt)
        text, usage = await asyncio.to_thread(
            self._gemini.generate_text_tracked, prompt=call["prompt"], system_instruction=system_instruction,
            cached_content=call["cached_content"], cache_fallback_prefix=call["cache_fallback_prefix"],
        )
        await self._usage_repo.log(
            model=usage.model, operation=operation, input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens, total_tokens=usage.total_tokens,
            duration_ms=usage.duration_ms, cached_tokens=usage.cached_tokens, user_id=user_id,
        )
        return parse_model_json(text)

    def deanonymize(self, text: str, name_map: dict[str, str]) -> str:
        return deanonymize(text, name_map)

    def reanonymize(self, text: str, name_map: dict[str, str]) -> str:
        return reanonymize(text, name_map)
