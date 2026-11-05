"""Nível de acesso por perfil e por tela, configurável pelo administrador: sem acesso, somente ver ou ver e editar.

Salvo em `role_permissions.allowed`:
  * dict {chave_da_tela: "read" | "write"}  (tela ausente = sem acesso)
  * lista de chaves (formato antigo, só "ver/ocultar"): cada tela listada vale como "write", ou seja, o que o perfil
    já podia fazer pelas regras de papel continua igual.
Sem linha para o perfil = vale o padrão do código (nenhum bloqueio extra além das regras de papel).

As chaves são as mesmas do menu do frontend (labelKey de `nav-items.ts`). Aqui só se bloqueia ESCRITA: ler continua
dependendo das regras de papel, porque uma tela costuma ler dados de outras (ex.: a lista de alunos).
"""
from typing import Any, Optional

NONE, READ, WRITE = "none", "read", "write"
LEVELS = (NONE, READ, WRITE)
WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")

# prefixo da API -> chave(s) da tela. Vale o prefixo mais longo; com mais de uma chave, basta ter "editar" em uma delas.
PATH_KEYS: list[tuple[str, tuple[str, ...]]] = [
    ("/admin/metrics", ("metrics",)),
    ("/ai-usage", ("aiSpending",)),
    ("/prompts", ("aiPrompts",)),
    ("/admin", ("users",)),
    ("/students", ("students",)),
    ("/schools", ("schools", "schoolProfile")),  # a tela do questionário da escola grava em /schools/{id}
    ("/municipalities", ("schools",)),
    ("/teachers", ("teachers",)),
    ("/links", ("links",)),
    ("/case-studies", ("caseStudy",)),
    ("/diary-summary", ("dailySummary",)),
    ("/diary-questions", ("schoolDiary",)),
    ("/diary", ("schoolDiary",)),
    ("/family/diary/therapy", ("therapyDiary",)),
    ("/family/diary/family", ("familyDiary",)),
    ("/family", ("users",)),  # vínculos de responsáveis e terapeutas
    ("/pei-kanban/from-skill", ("skillsRegistry",)),  # exportar do plano da habilidade para o quadro
    ("/pei-kanban", ("skillsTracking",)),
    ("/bncc", ("skillsRegistry",)),
    ("/saved-skills", ("skillsRegistry",)),
    ("/skill-plan", ("skillsRegistry",)),
    ("/skills", ("skillsRegistry",)),
    ("/pdi", ("skillsRegistry",)),
    ("/functional-profiles", ("functionalProfile",)),
    ("/pei-gen", ("structuredPei",)),
]
# POSTs que só consultam/geram sem alterar dados da tela (conversa com a IA, relatório em PDF, transcrição de áudio)
EXEMPT_PREFIXES = ("/chat", "/rag", "/pei-kanban/report", "/family/transcribe-audio", "/auth", "/permissions")


def normalize_levels(raw: Any) -> Optional[dict[str, str]]:
    """Formato salvo -> {chave: "read"|"write"}; None = perfil sem personalização."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        return {str(k): v for k, v in raw.items() if v in (READ, WRITE)}
    if isinstance(raw, (list, tuple, set)):
        return {str(k): WRITE for k in raw}
    return None


def keys_for_path(path: str) -> tuple[str, ...]:
    p = "/" + path.strip("/")
    if any(p == x or p.startswith(x + "/") for x in EXEMPT_PREFIXES):
        return ()
    for prefix, keys in sorted(PATH_KEYS, key=lambda item: -len(item[0])):
        if p == prefix or p.startswith(prefix + "/"):
            return keys
    return ()


def blocks_write(levels: Optional[dict[str, str]], path: str, method: str) -> bool:
    """A escrita deve ser recusada? Só quando o perfil tem personalização e a tela da rota não está em "editar"."""
    if levels is None or method.upper() not in WRITE_METHODS:
        return False
    keys = keys_for_path(path)
    return bool(keys) and not any(levels.get(k) == WRITE for k in keys)
