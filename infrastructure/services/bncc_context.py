"""Catálogo BNCC como contexto de referência para a IA, com cache explícito do Gemini.

O catálogo (~50 mil tokens) é igual para todos os alunos, então vale ficar em um
cache explícito COMPARTILHADO (não por aluno): o conteúdo não tem dado pessoal e
só muda quando alguém edita o catálogo (a "versão" muda e o cache é recriado).

Custo: o cache é criado sob demanda e tem validade curta (BNCC_CACHE_TTL_SECONDS,
padrão 30 min), renovada enquanto estiver em uso — em horário ocioso ele expira e
não gera cobrança de armazenamento. Se o cache não puder ser criado (ou for
desligado com TTL=0), o catálogo vai inline no início do prompt, onde o cache
IMPLÍCITO do Gemini ainda pode reaproveitá-lo.
"""
import asyncio
import logging
import time
from typing import Optional

from google import genai
from google.genai import types
from sqlalchemy import select, func

from core.config import settings
from infrastructure.models.bncc import BnccSkill

logger = logging.getLogger(__name__)

CATALOG_HEADER = "=== CATÁLOGO DE HABILIDADES BNCC (material de referência; cite somente códigos que existam aqui) ==="

BNCC_USAGE_RULE = (
    "CATÁLOGO BNCC: o catálogo de habilidades BNCC é material de referência. Ao propor objetivos, metas ou "
    "atividades de aprendizagem acadêmica, relacione-os, quando pertinente, a habilidades do catálogo citando o "
    "código exato (ex.: EF01LP02). Nunca invente códigos nem descrições: use somente o que consta no catálogo."
)

_BACKOFF_SECONDS = 300


class BnccContext:
    def __init__(self, database, gemini, usage_repo) -> None:
        self._db = database
        self._gemini = gemini
        self._usage_repo = usage_repo
        self._lock = asyncio.Lock()
        self._version: Optional[str] = None
        self._text: Optional[str] = None
        self._cache: Optional[dict] = None  # {"name", "version", "expires_at"}
        self._backoff_until = 0.0

    # ── texto do catálogo ────────────────────────────────────────────────────

    @staticmethod
    def _render(rows) -> str:
        lines = [CATALOG_HEADER]
        grade = area = None
        for g, a, code, desc in rows:
            if g != grade:
                lines.append("\n## " + g)
                grade, area = g, None
            if a != area:
                lines.append("### " + a)
                area = a
            lines.append(f"{code}: {desc}")
        return "\n".join(lines)

    async def catalog(self) -> tuple[str, str]:
        """(versão, texto). A versão muda quando uma habilidade é criada, editada ou removida."""
        async with self._db.session() as session:
            count, last = (await session.execute(
                select(func.count(BnccSkill.id), func.max(BnccSkill.updated_at)).where(BnccSkill.deleted == False)
            )).one()
            version = f"{count}:{last}"
            if version == self._version and self._text:
                return version, self._text
            rows = (await session.execute(
                select(BnccSkill.grade, BnccSkill.area, BnccSkill.code, BnccSkill.description)
                .where(BnccSkill.deleted == False)
                .order_by(BnccSkill.grade_order, BnccSkill.grade, BnccSkill.position, BnccSkill.code)
            )).all()
        self._version, self._text = version, self._render(rows)
        return self._version, self._text

    # ── cache explícito ──────────────────────────────────────────────────────

    def _client(self):
        return genai.Client(api_key=self._gemini.api_key)

    async def _ensure_cache(self, version: str, text: str) -> Optional[str]:
        ttl = int(getattr(settings, "BNCC_CACHE_TTL_SECONDS", 1800) or 0)
        if ttl <= 0:
            return None
        now = time.time()
        async with self._lock:
            c = self._cache
            if c and c["version"] == version and c["expires_at"] - now > 30:
                if c["expires_at"] - now < ttl / 2:
                    await self._extend(c, ttl)
                return c["name"]
            if now < self._backoff_until:
                return None
            old = c["name"] if c else None
            try:
                def _create():
                    # O cliente precisa ficar numa variável: se for descartado antes do fim da
                    # requisição, o SDK fecha a conexão ("client has been closed").
                    client = self._client()
                    return client.caches.create(
                        model=self._gemini.model_name,
                        config=types.CreateCachedContentConfig(
                            contents=[types.Content(role="user", parts=[types.Part(text=text + "\n\n")])],
                            ttl=f"{ttl}s", display_name="bncc-catalog",
                        ),
                    )

                created = await asyncio.to_thread(_create)
            except Exception:
                logger.warning("Não foi possível criar o cache do catálogo BNCC; usando o catálogo inline.", exc_info=True)
                self._cache = None
                self._backoff_until = now + _BACKOFF_SECONDS
                return None
            self._cache = {"name": created.name, "version": version, "expires_at": now + ttl}
            tokens = getattr(getattr(created, "usage_metadata", None), "total_token_count", None) or 0
            await self._usage_repo.log(
                model=self._gemini.model_name, operation="bncc_cache_create",
                input_tokens=int(tokens), output_tokens=0,
            )
            if old:
                asyncio.create_task(self._delete(old))
            return created.name

    async def _extend(self, cache: dict, ttl: int) -> None:
        try:
            def _update():
                client = self._client()
                client.caches.update(name=cache["name"], config=types.UpdateCachedContentConfig(ttl=f"{ttl}s"))

            await asyncio.to_thread(_update)
            cache["expires_at"] = time.time() + ttl
        except Exception:
            logger.debug("Falha ao renovar o cache do catálogo BNCC", exc_info=True)

    async def _delete(self, name: str) -> None:
        try:
            def _remove():
                client = self._client()
                client.caches.delete(name=name)

            await asyncio.to_thread(_remove)
        except Exception:
            logger.debug("Falha ao apagar o cache antigo do catálogo BNCC", exc_info=True)

    # ── uso nas gerações ─────────────────────────────────────────────────────

    async def attach(self, prompt: str) -> dict:
        """Argumentos para GeminiService.generate_text_tracked com o catálogo anexado.

        Com cache explícito: o catálogo fica no cache (prompt intacto) e `cache_fallback_prefix`
        guarda o texto para repetir a chamada sem cache se ele expirar. Sem cache: catálogo inline
        no INÍCIO do prompt (prefixo igual para todos os alunos = melhor para o cache implícito)."""
        version, text = await self.catalog()
        block = text + "\n\n"
        name = await self._ensure_cache(version, text)
        if name:
            return {"prompt": prompt, "cached_content": name, "cache_fallback_prefix": block}
        return {"prompt": block + prompt, "cached_content": None, "cache_fallback_prefix": None}
