"""Proteções contra um modo de falha do Gemini observado na geração de PEI: ao
montar uma tabela markdown com células longas (seção "Adaptações Curriculares
por Componente Curricular"), o modelo entra num loop preenchendo a célula com
espaços em branco até bater no teto de tokens. O resultado é um PEI de centenas
de milhares de caracteres que termina em espaços, sem as seções seguintes."""
import re

# Nenhum texto legítimo repete o mesmo caractere 100+ vezes seguidas (espaço,
# traço da linha separadora de tabela, etc.) — sinal do loop de repetição.
_REPEATED_CHAR_RE = re.compile(r"([^\n])\1{99,}")
# Um PEI real tem ~15-30 mil caracteres; acima disso é quase certamente loop.
MAX_PLAUSIBLE_CHARS = 100_000
# Indentação de lista aninhada tem no máximo poucos espaços; 20+ é preenchimento.
_PADDING_RE = re.compile(r"[ \t]{20,}")

# Vai no prompt (código, não no prompt editável do admin) — prevenção do loop.
TABLE_FORMAT_RULE = (
    "REGRAS DE FORMATAÇÃO DE TABELAS: escreva cada linha de tabela markdown de forma "
    "compacta, com uma barra '|' e um único espaço entre as células. NUNCA alinhe colunas "
    "nem preencha células com espaços em branco. Mantenha cada célula curta (uma ou duas "
    "frases) e sempre termine todas as seções do PEI."
)

RETRY_NOTE = (
    "\n\nATENÇÃO: uma tentativa anterior falhou por preencher células de tabela com espaços "
    "em branco. Nesta tentativa, seja conciso em cada célula, sem espaços de alinhamento, e "
    "complete todas as seções até o final."
)


def has_degenerate_output(text: str) -> bool:
    """True se a resposta parece um loop de repetição (e portanto está cortada)."""
    if not text:
        return False
    return len(text) > MAX_PLAUSIBLE_CHARS or _REPEATED_CHAR_RE.search(text) is not None


def collapse_padding(text: str) -> str:
    """Reduz preenchimento excessivo de espaços sem mexer na indentação normal."""
    return _PADDING_RE.sub(" ", text)
