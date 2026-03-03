from core.kernel.result import Result
from infrastructure.repositories.diary_embedding_gemini_repository import DiaryEmbeddingGeminiRepository
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository
from infrastructure.services.llm_service import LLMService


class QueryDiaryRAGUseCase:
    """
    Caso de uso para consultar registros diários usando RAG (Retrieval Augmented Generation).
    Permite fazer perguntas sobre os registros de um beneficiário específico.
    """

    def __init__(
        self,
        diary_embedding_gemini_repository: DiaryEmbeddingGeminiRepository,
        beneficiary_repository: BeneficiaryRepository,
        llm_service: LLMService,
    ):
        self.diary_embedding_gemini_repository = diary_embedding_gemini_repository
        self.beneficiary_repository = beneficiary_repository
        self.llm_service = llm_service

    async def execute(self, beneficiary_id: int, query: str, limit: int = 10):
        """
        Executa consulta RAG sobre os diários de um beneficiário.

        Args:
            beneficiary_id: ID do beneficiário
            query: Pergunta ou consulta a ser respondida
            limit: Número de registros similares a considerar
        """
        try:
            # Verificar se o beneficiário existe
            beneficiary = await self.beneficiary_repository.get_by_id(beneficiary_id)
            if not beneficiary:
                return Result.not_found("Beneficiário não encontrado")

            # Configurar LLM com Gemini
            self.llm_service.configure("gemini")

            # Gerar embedding da query
            query_embedding = await self.llm_service.generate_embeddings(query)

            # Buscar registros similares do beneficiário
            similar_entries = await self.diary_embedding_gemini_repository.search_similar_by_beneficiary(
                query_embedding, beneficiary_id, limit
            )

            if not similar_entries:
                return Result.ok({
                    "answer": "Não há registros diários suficientes para responder essa pergunta.",
                    "beneficiary_name": beneficiary.name,
                    "sources_count": 0
                })

            # Criar contexto com os registros encontrados
            context_parts = []
            for i, entry in enumerate(similar_entries, 1):
                meta = entry.meta_data or {}
                context_parts.append(
                    f"Registro {i} (Data: {meta.get('diary_date', 'N/A')}):\n{entry.content}"
                )

            context = "\n\n---\n\n".join(context_parts)

            # Criar prompt para o LLM
            final_prompt = f"""
            Você é um assistente especializado em análise de acompanhamento educacional de alunos com TEA.

            Baseado nos seguintes registros diários do aluno {beneficiary.name}, responda à pergunta de forma clara,
            objetiva e fundamentada nos dados apresentados.

            REGISTROS DIÁRIOS:
            {context}

            PERGUNTA: {query}

            INSTRUÇÕES:
            - Base sua resposta APENAS nos registros apresentados
            - Se os registros não contiverem informação suficiente, seja honesto sobre isso
            - Cite as datas relevantes quando aplicável
            - Seja específico e objetivo
            - Use linguagem profissional mas acessível

            RESPOSTA:
            """

            # Gerar resposta
            answer = await self.llm_service.chat(final_prompt)

            return Result.ok({
                "answer": answer,
                "beneficiary_name": beneficiary.name,
                "sources_count": len(similar_entries),
                "query": query
            })

        except Exception as e:
            return Result.error(f"Erro ao executar consulta RAG: {str(e)}")
