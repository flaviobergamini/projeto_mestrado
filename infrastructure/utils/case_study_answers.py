"""Valores canônicos das respostas fechadas do estudo de caso (sempre em português).

O formulário antigo persistia o RÓTULO traduzido como valor da resposta — quem
preenchia com a interface em inglês salvava "Yes"/"No", que o backend nunca
reconhecia (só "Sim"/"Não"), e essas respostas sumiam do contexto da IA. Agora o
valor salvo é sempre o canônico em português e só o rótulo é traduzido na tela;
este módulo também normaliza os valores legados já gravados no banco.
"""
from typing import Any, Optional

SIM = "Sim"
NAO = "Não"
PARCIALMENTE = "Parcialmente"
NAO_SE_ALIMENTA = "Não se alimenta na escola"
NAO_SE_APLICA = "Não se aplica"

CANONICAL_VALUES = {SIM, NAO, PARCIALMENTE, NAO_SE_ALIMENTA, NAO_SE_APLICA}

_LOOKUP = {
    "sim": SIM, "yes": SIM,
    "não": NAO, "nao": NAO, "no": NAO,
    "parcialmente": PARCIALMENTE, "partially": PARCIALMENTE,
    "não se alimenta na escola": NAO_SE_ALIMENTA, "does not eat at school": NAO_SE_ALIMENTA,
    "não se aplica": NAO_SE_APLICA, "not applicable": NAO_SE_APLICA,
}


def normalize_closed_answer(value: Any) -> Optional[str]:
    """Valor canônico se `value` for uma resposta fechada conhecida (inclusive
    legada em inglês); None se for texto livre ou vazio."""
    if not isinstance(value, str):
        return None
    return _LOOKUP.get(value.strip().lower())


def normalize_answers(answers: dict) -> dict:
    """Cópia de `answers` com respostas fechadas legadas trocadas pelo valor
    canônico; qualquer outro valor (texto livre, listas) fica intacto."""
    return {k: (normalize_closed_answer(v) or v) for k, v in answers.items()}
