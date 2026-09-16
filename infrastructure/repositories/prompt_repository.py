"""Repository for AI system prompts (chat and pei scopes)."""

import uuid
from sqlalchemy import select, update, delete
from sqlalchemy.exc import OperationalError

from infrastructure.database_context.database import Database
from infrastructure.models.ai_prompt import AiPrompt

DEFAULT_CHAT_PROMPT = """Você é um especialista em educação inclusiva, autismo, análise comportamental e pedagógica. Sua principal tarefa é responder perguntas sobre alunos com Transtorno do Espectro Autista (TEA).

Estamos trabalhando com dados sensíveis seguindo a LGPD, portanto se o usuário entrar com algum nome próprio (aluno ou professor), ou nome de escola, município, etc, você deve recusar o chat e não usar esses dados, e retornar apenas e nada mais além disso: "Chat não considerado, pois devo seguir as diretrizes da LGPD para dados sensíveis" e deve parar de responder qualquer coisa pra frente.
Entretanto, você deve retornar os códigos relacionados que foram enviados para você sempre que necessário, relacionados aos nomes, escolas, etc.

Você só deve seguir a frente se o usuário não cometer problemas de dados sensíveis.

Baseie suas respostas nos documentos fornecidos como contexto. Se o contexto trouxer trecho explícito de uma fonte, trate esse trecho como evidência factual utilizável. Não diga que não tem acesso se o trecho estiver presente no contexto. Se não houver informação suficiente no contexto, informe claramente.

Regra crítica de fontes:
- Diferencie rigorosamente as fontes "Diário", "PDI", "PEI" e "Cadastro".
- Só afirme que existe Diário cadastrado quando houver entradas explícitas na seção de Diário do contexto.
- Nunca trate relatório descritivo do PDI como se fosse entrada de Diário.
- Nunca use inferência para afirmar existência de registros: quando não houver dados explícitos, responda que não há registro encontrado.

Responda sempre em português do Brasil, de forma clara e profissional."""

DEFAULT_PEI_PROMPT = """Você é um especialista em educação inclusiva, autismo, análise comportamental e pedagógica. Sua principal tarefa é gerar um Plano Educacional Individualizado (PEI) para estudantes autistas.

O PEI deve ser completo, abrangendo rigorosamente todos os tópicos e subtópicos listados na estrutura, sem variabilidade. Caso uma informação para um tópico ou subtópico não esteja explicitamente disponível nos documentos fornecidos, o PEI deverá indicar claramente "Não informado no documento", "Dados não disponíveis no estudo de caso", ou uma frase similar que denote a ausência da informação, mantendo a estrutura íntegra.

Tenha em mente as definições de nível de suporte atual da criança com base nos critérios do DSM-5 e justifique a escolha, correlacionando os dados do perfil funcional da criança com as exigências de suporte para comunicação social e comportamentos restritos e repetitivos.

O PEI deve conter as seguintes seções obrigatórias:

1. IDENTIFICAÇÃO DO ALUNO
   - Nome, idade, escola, turma, professores, diagnóstico, nível de suporte TEA (DSM-5)

2. PERFIL FUNCIONAL
   - Habilidades, potencialidades, dificuldades e necessidades de apoio
   - Aspectos cognitivos, socioemocionais, motores e de comunicação

3. OBJETIVOS EDUCACIONAIS (formato SMART)
   - Objetivos de curto prazo (bimestre)
   - Objetivos de longo prazo (ano letivo)

4. ESTRATÉGIAS PEDAGÓGICAS
   - Metodologias e abordagens recomendadas
   - Recursos visuais, estruturação do ambiente, rotina

5. APOIOS E SERVIÇOS
   - Apoio pedagógico especializado (AEE)
   - Apoios terapêuticos complementares
   - Profissional de apoio escolar

6. ADAPTAÇÕES CURRICULARES
   - Adaptações de conteúdo, método, avaliação e temporalidade
   - Alinhamento com a BNCC

7. COMUNICAÇÃO COM A FAMÍLIA
   - Estratégias de parceria escola-família
   - Orientações para continuidade em casa

8. AVALIAÇÃO DO PROGRESSO
   - Indicadores de acompanhamento
   - Periodicidade de revisão do PEI

9. CULTURA ESCOLAR E INCLUSÃO
   - Ações para sensibilização dos colegas e comunidade escolar

10. FUNDAMENTAÇÃO LEGAL
    - LBI (Lei 13.146/2015), LDB, Resolução CNE/CEB 4/2009

Responda em português do Brasil, de forma técnica, objetiva e empática."""

DEFAULT_DIARY_SUMMARY_PROMPT = """Você é um especialista em educação inclusiva, autismo, análise comportamental e pedagógica. Sua tarefa é gerar, em conversa com um administrador, um Resumo Diário sobre o acompanhamento de um aluno com Transtorno do Espectro Autista (TEA), com base nos registros de diário (escolar e/ou familiar) selecionados para o período informado.

Baseie-se exclusivamente nos registros de diário fornecidos como contexto. Não invente informações que não estejam presentes nesses registros.

O resumo deve:
- Descrever a evolução do aluno no período observado (comportamento, socialização, comunicação, autonomia, participação em atividades).
- Destacar padrões, mudanças relevantes ou situações que mereçam atenção.
- Diferenciar observações do diário escolar das observações do diário familiar, quando ambas estiverem presentes.
- Ser objetivo, claro e útil para profissionais que irão consultar esse resumo posteriormente (coordenação, professores, família).

Responda sempre em português do Brasil, de forma clara e profissional."""


def _default_prompt(scope: str) -> dict:
    if scope == "chat":
        content = DEFAULT_CHAT_PROMPT
        name = "Prompt base do Chat - Anonimização"
    elif scope == "diary_summary":
        content = DEFAULT_DIARY_SUMMARY_PROMPT
        name = "Prompt base do Resumo Diário"
    else:
        content = DEFAULT_PEI_PROMPT
        name = "Prompt base do PEI"
    return {
        "id": f"__default_{scope}__",
        "scope": scope,
        "name": f"{name} [base]",
        "description": "Prompt base",
        "content": content,
        "is_active": True,
        "created_at": None,
        "updated_at": None,
        "is_base": True,
    }


class PromptRepository:
    def __init__(self, database: Database):
        self._db = database

    async def get_active(self, scope: str) -> dict:
        """Return the active prompt, or the most recently updated, or the hardcoded default."""
        try:
            async with self._db.session() as session:
                # 1st priority: explicitly activated prompt
                result = await session.execute(
                    select(AiPrompt)
                    .where(AiPrompt.scope == scope, AiPrompt.is_active == True, AiPrompt.deleted == False)
                    .order_by(AiPrompt.updated_at.desc())
                    .limit(1)
                )
                row = result.scalar_one_or_none()
                if row:
                    return self._to_dict(row)

                # 2nd priority: most recently created/updated prompt
                result = await session.execute(
                    select(AiPrompt)
                    .where(AiPrompt.scope == scope, AiPrompt.deleted == False)
                    .order_by(AiPrompt.updated_at.desc())
                    .limit(1)
                )
                row = result.scalar_one_or_none()
                if row:
                    return self._to_dict(row)
        except OperationalError:
            pass
        # 3rd priority: hardcoded default
        return _default_prompt(scope)

    async def list_all(self, scope: str) -> list[dict]:
        """Return prompts: active first, then others by recency, base prompt last."""
        custom: list[dict] = []
        try:
            async with self._db.session() as session:
                result = await session.execute(
                    select(AiPrompt)
                    .where(AiPrompt.scope == scope, AiPrompt.deleted == False)
                    # active first, then by most recently updated
                    .order_by(AiPrompt.is_active.desc(), AiPrompt.updated_at.desc())
                )
                rows = result.scalars().all()
                custom = [self._to_dict(r) for r in rows]
        except OperationalError:
            pass
        # Base prompt always at the end
        return custom + [_default_prompt(scope)]

    async def create(self, scope: str, name: str, description: str, content: str) -> dict:
        async with self._db.session() as session:
            prompt = AiPrompt(
                id=str(uuid.uuid4()),
                scope=scope,
                name=name,
                description=description,
                content=content,
                is_active=False,
            )
            session.add(prompt)
            await session.commit()
            await session.refresh(prompt)
            return self._to_dict(prompt)

    async def update(self, prompt_id: str, name: str, description: str, content: str) -> dict | None:
        async with self._db.session() as session:
            result = await session.execute(select(AiPrompt).where(AiPrompt.id == prompt_id))
            prompt = result.scalar_one_or_none()
            if not prompt:
                return None
            prompt.name = name
            prompt.description = description
            prompt.content = content
            await session.commit()
            await session.refresh(prompt)
            return self._to_dict(prompt)

    async def activate(self, scope: str, prompt_id: str) -> dict | None:
        """Deactivate all, then activate the chosen one."""
        async with self._db.session() as session:
            await session.execute(
                update(AiPrompt).where(AiPrompt.scope == scope).values(is_active=False)
            )
            result = await session.execute(select(AiPrompt).where(AiPrompt.id == prompt_id))
            prompt = result.scalar_one_or_none()
            if not prompt:
                return None
            prompt.is_active = True
            await session.commit()
            await session.refresh(prompt)
            return self._to_dict(prompt)

    async def deactivate(self, scope: str) -> dict:
        """Deactivate all prompts for the scope — Gemini falls back to most recent."""
        async with self._db.session() as session:
            await session.execute(
                update(AiPrompt).where(AiPrompt.scope == scope).values(is_active=False)
            )
            await session.commit()
        return await self.get_active(scope)

    async def delete(self, prompt_id: str) -> bool:
        async with self._db.session() as session:
            result = await session.execute(select(AiPrompt).where(AiPrompt.id == prompt_id))
            prompt = result.scalar_one_or_none()
            if not prompt:
                return False
            # If active, deactivation makes the default take over automatically
            prompt.deleted = True
            await session.commit()
            return True

    async def reset_to_default(self, scope: str) -> dict:
        """Deactivate all custom prompts — default takes over."""
        try:
            async with self._db.session() as session:
                await session.execute(
                    update(AiPrompt).where(AiPrompt.scope == scope).values(is_active=False)
                )
                await session.commit()
        except OperationalError:
            pass
        return _default_prompt(scope)

    def _to_dict(self, row: AiPrompt) -> dict:
        return {
            "id": row.id,
            "scope": row.scope,
            "name": row.name,
            "description": row.description or "",
            "content": row.content,
            "is_active": row.is_active,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "is_base": False,
        }
