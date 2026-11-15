"""Anonimização do texto de anexos (PDFs) antes de ele ser vetorizado ou enviado à IA.

Tudo aqui é determinístico (substituição por regras), sem IA. Camadas, da mais certa para a mais ampla:
  1. nomes conhecidos pelo sistema (aluno, escola, professores vinculados) -> o identificador anonimizado (UUID),
     o mesmo que o restante do pipeline usa, então a resposta da IA volta com os nomes reais pelo `deanonymize`;
  2. responsáveis cadastrados -> [RESPONSÁVEL];
  3. campos rotulados ("Nome:", "Mãe:", "Endereço:"...) -> o valor vira marcador, pegando nomes que o sistema não conhece;
  4. documentos e contatos (CPF, CNPJ, RG, e-mail, telefone, CEP, SUS, registros profissionais);
  5. data de nascimento do aluno e datas ao lado de "nascimento";
  6. tratamento + nome ("Dra. Maria Souza") -> [PROFISSIONAL].
É um filtro de melhor esforço: um nome que o sistema não conhece e que aparece solto no texto não é detectável sem IA.
"""
import re
import unicodedata
from datetime import date
from typing import Iterable, Optional

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
MAX_CHUNKS = 300

# partículas de nome e palavras comuns: nunca substituídas isoladamente
_NAME_STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "as", "os", "em", "no", "na", "para", "com", "sem", "por",
    "filho", "filha", "neto", "neta", "junior", "júnior", "jr", "santos", "silva",
}
_MIN_TOKEN = 4

_MONTHS = "janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro"

_RE_CPF = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")
_RE_CNPJ = re.compile(r"(?<!\d)\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?!\d)")
_RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_RE_PHONE = re.compile(r"(?<!\d)(?:\+?55[\s.-]?)?(?:\(?\d{2}\)?[\s.-]?)?9?\d{4}[\s.-]\d{4}(?!\d)")
_RE_CEP = re.compile(r"(?<!\d)\d{5}-\d{3}(?!\d)")
_RE_RG = re.compile(r"(?i)\b(R\.?G\.?|identidade|CNH|certid[ãa]o)\s*(?:n[ºo°.]*)?\s*[:\-]?\s*[\d.\-xX/]{5,}")
_RE_SUS = re.compile(r"(?i)\b(?:cart[ãa]o\s+)?(?:SUS|CNS)\b\s*[:\-]?\s*[\d ]{15,}")
_RE_REGISTRO = re.compile(r"(?i)\b(CRM|CRP|CREFITO|CRFa|CREFONO|COREN|CRESS|CREF|OAB)\s*[/\- ]?\s*[A-Z]{0,2}\s*[:\-]?\s*\d[\d.\-/]{2,}")
_RE_TITULO_NOME = re.compile(
    r"\b(Dr|Dra|Prof|Profa|Psic|Fono|Sr|Sra)\.?\s+"
    r"[A-ZÀ-Ý][\wÀ-ÿ'’-]+(?:\s+(?:d[aeo]s?|e)?\s*[A-ZÀ-Ý][\wÀ-ÿ'’-]+){0,3}"
)
_RE_ENDERECO = re.compile(
    r"(?i)\b(?:endere[çc]o|resid[eê]ncia|resid(?:e|ente)\s+(?:na|no|em))\b\s*[:\-]?\s*[^\n]{0,120}"
    r"|\b(?:rua|avenida|av\.|travessa|alameda|rodovia|estrada)\s+[^\n]{3,80}"
)
# "Nome: Fulano de Tal" -> mantém o rótulo, troca o valor (até o fim da linha)
_RE_CAMPO_NOME = re.compile(
    r"(?im)^([ \t]*(?:nome(?:\s+(?:completo|da\s+m[ãa]e|do\s+pai|do\s+respons[áa]vel|do\s+paciente|do\s+aluno|da\s+aluna|do\s+benefici[áa]rio))?"
    r"|m[ãa]e|pai|respons[áa]vel|paciente|aluno\(?a?\)?|benefici[áa]rio|filiação)[ \t]*:[ \t]*)(?!\[)[^\n]+$"
)


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _word_pattern(value: str) -> re.Pattern:
    """Padrão do texto como palavra inteira, sem diferenciar maiúsculas e tolerando espaços/quebras entre as palavras."""
    parts = [re.escape(p) for p in value.split() if p]
    return re.compile(r"(?<!\w)" + r"\s+".join(parts) + r"(?!\w)", re.IGNORECASE)


def _replace_name(text: str, name: str, replacement: str) -> str:
    """Troca o nome (como escrito e também sem acentos) pelo marcador."""
    name = (name or "").strip()
    if len(name) < 2:
        return text
    for variant in dict.fromkeys([name, _strip_accents(name)]):
        text = _word_pattern(variant).sub(replacement, text)
    return text


def _tokens(name: str) -> list[str]:
    out = []
    for tok in re.split(r"[\s,;]+", name or ""):
        tok = tok.strip(".-'’")
        if len(tok) >= _MIN_TOKEN and tok.lower() not in _NAME_STOPWORDS:
            out.append(tok)
    return out


def _birth_patterns(d: date) -> list[re.Pattern]:
    months = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    forms = [
        rf"0?{d.day}\s*[/.\-]\s*0?{d.month}\s*[/.\-]\s*(?:{d.year}|{d.year % 100:02d})",
        rf"{d.year}-0?{d.month}-0?{d.day}",
        rf"0?{d.day}\s+de\s+(?:{months[d.month - 1]}|{_strip_accents(months[d.month - 1])})\s+de\s+{d.year}",
    ]
    return [re.compile(f, re.IGNORECASE) for f in forms]


def anonymize_text(
    text: str,
    *,
    id_names: Optional[dict[str, str]] = None,
    person_names: Optional[dict[str, str]] = None,
    guardian_names: Iterable[str] = (),
    birth_date: Optional[date] = None,
) -> str:
    """Devolve o texto sem dados pessoais.

    id_names: nome real -> identificador anonimizado, trocado só pelo nome completo (aluno, escola, professores).
    person_names: nome real de PESSOA -> identificador; além do nome completo, cada nome/sobrenome isolado também é trocado.
    guardian_names: nomes de responsáveis (completos e por partes) -> [RESPONSÁVEL].
    birth_date: data de nascimento do aluno, em qualquer formato usual.
    """
    if not text:
        return ""
    id_names = id_names or {}
    person_names = person_names or {}

    # 0. documentos e contatos (antes dos nomes: um e-mail pode conter o nome de alguém)
    text = _RE_EMAIL.sub("[E-MAIL]", text)
    text = _RE_CNPJ.sub("[CNPJ]", text)
    text = _RE_CPF.sub("[CPF]", text)
    text = _RE_SUS.sub("[SUS]", text)
    text = _RE_RG.sub(lambda m: f"{m.group(1)} [DOCUMENTO]", text)
    text = _RE_REGISTRO.sub(lambda m: f"{m.group(1)} [REGISTRO]", text)
    text = _RE_CEP.sub("[CEP]", text)
    text = _RE_PHONE.sub("[TELEFONE]", text)
    text = _RE_ENDERECO.sub("[ENDEREÇO]", text)

    # 1. nomes completos, do mais longo para o mais curto (o nome inteiro antes de qualquer parte dele)
    full = {**id_names, **person_names}
    for name in sorted(full, key=len, reverse=True):
        text = _replace_name(text, name, full[name])
    # 1b. partes do nome de pessoas (primeiro nome, sobrenomes)
    for name, ident in person_names.items():
        for tok in _tokens(name):
            text = _replace_name(text, tok, ident)

    # 2. responsáveis cadastrados
    for guardian in sorted({g for g in guardian_names if g}, key=len, reverse=True):
        text = _replace_name(text, guardian, "[RESPONSÁVEL]")
        for tok in _tokens(guardian):
            text = _replace_name(text, tok, "[RESPONSÁVEL]")

    # 3. campos rotulados que citam nomes que o sistema não conhece
    text = _RE_CAMPO_NOME.sub(lambda m: m.group(1) + "[NOME]", text)

    # 5. data de nascimento
    if birth_date:
        for pat in _birth_patterns(birth_date):
            text = pat.sub("[DATA DE NASCIMENTO]", text)
    text = re.sub(
        rf"(?i)(nascid[oa]\s+em|nascimento|nasc\.?)\s*[:\-]?\s*(?:\d{{1,2}}\s*[/.\-]\s*\d{{1,2}}\s*[/.\-]\s*\d{{2,4}}|\d{{1,2}}\s+de\s+(?:{_MONTHS})\s+de\s+\d{{4}})",
        lambda m: f"{m.group(1)} [DATA DE NASCIMENTO]", text)

    # 6. tratamento + nome
    text = _RE_TITULO_NOME.sub(lambda m: f"{m.group(1)}. [PROFISSIONAL]", text)

    # nome e sobrenome trocados em partes geram o mesmo marcador em sequência: junta num só
    markers = [re.escape(v) for v in set(full.values())] + [r"\[RESPONSÁVEL\]"]
    for marker in markers:
        text = re.sub(rf"({marker})(?:\s+{marker})+", r"\1", text)
    return text


def chunk_text(text: str) -> list[str]:
    """Divide o texto em trechos (quebrando de preferência em parágrafos e frases) para vetorização."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    text = re.sub(r"[ \t]+", " ", text or "")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return [c.strip() for c in splitter.split_text(text) if c.strip()][:MAX_CHUNKS]
