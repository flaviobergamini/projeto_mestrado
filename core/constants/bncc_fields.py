"""Campos de experiência da BNCC (Educação Infantil), usados no plano de cada habilidade.

O valor gravado no banco é a CHAVE estável (idioma-neutra). O nome exibido vem dos arquivos de tradução do frontend
(messages/pt.json e messages/en.json, em bncc.experienceFields). O nome em português abaixo é usado só no texto do
prompt da IA, para ela entender cada chave.
"""

EXPERIENCE_FIELD_NAMES_PT: dict[str, str] = {
    "selfOtherUs": "O eu, o outro e o nós",
    "bodyGestures": "Corpo, gestos e movimentos",
    "linesSounds": "Traços, sons, cores e formas",
    "listeningSpeaking": "Escuta, fala, pensamento e imaginação",
    "spacesTimes": "Espaços, tempos, quantidades, relações e transformações",
}

EXPERIENCE_FIELDS: tuple[str, ...] = tuple(EXPERIENCE_FIELD_NAMES_PT)
