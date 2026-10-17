"""Fontes de contexto do plano por habilidade. Os textos dos prompts ficam em core/constants/prompt_defaults.py."""

STAR_SCALE = (
    "0 = não avaliada; 1 = dependência total (ajuda física total); 2 = ajuda física parcial; "
    "3 = ajuda gestual ou verbal; 4 = pista mínima/supervisão; 5 = independente"
)

ROUND1_SOURCES = ["student", "school", "case_study", "functional_profile", "diary_summary", "skill_report"]
ROUND2_SOURCES = ["student", "functional_profile", "diary_summary"]

from core.constants.prompt_defaults import SKILL_PLAN_ROUND1_PROMPT, SKILL_PLAN_ROUND2_PROMPT

ROUND1_SYSTEM = SKILL_PLAN_ROUND1_PROMPT
ROUND2_SYSTEM = SKILL_PLAN_ROUND2_PROMPT
