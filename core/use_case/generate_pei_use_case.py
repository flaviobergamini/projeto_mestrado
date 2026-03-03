from datetime import datetime
import json
import re

from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository
from infrastructure.repositories.study_case_embedding_gemini_repository import StudyCaseEmbeddingGeminiRepository
from infrastructure.repositories.institution_embedding_gemini_repository import InstitutionEmbeddingGeminiRepository
from infrastructure.repositories.diary_embedding_gemini_repository import DiaryEmbeddingGeminiRepository
from infrastructure.repositories.school_repository import SchoolRepository
from infrastructure.repositories.pei_repository import PEIRepository
from infrastructure.repositories.pei_embedding_gemini_repository import PEIEmbeddingGeminiRepository
from infrastructure.services.llm_service import LLMService
from infrastructure.services.storage_service import StorageService
from infrastructure.models.pei import PEI
from infrastructure.models.pei_embedding_gemini import PEIEmbeddingGemini
from core.kernel.result import Result


class GeneratePEIUseCase:
    def __init__(
        self,
        beneficiary_repository: BeneficiaryRepository,
        study_case_embedding_gemini_repository: StudyCaseEmbeddingGeminiRepository,
        institution_embedding_gemini_repository: InstitutionEmbeddingGeminiRepository,
        diary_embedding_gemini_repository: DiaryEmbeddingGeminiRepository,
        school_repository: SchoolRepository,
        pei_repository: PEIRepository,
        pei_embedding_gemini_repository: PEIEmbeddingGeminiRepository,
        llm_service: LLMService,
        storage_service: StorageService
    ):
        self.beneficiary_repository = beneficiary_repository
        self.study_case_embedding_gemini_repository = study_case_embedding_gemini_repository
        self.institution_embedding_gemini_repository = institution_embedding_gemini_repository
        self.diary_embedding_gemini_repository = diary_embedding_gemini_repository
        self.school_repository = school_repository
        self.pei_repository = pei_repository
        self.pei_embedding_gemini_repository = pei_embedding_gemini_repository
        self.llm_service = llm_service
        self.storage_service = storage_service

    async def execute(self, beneficiary_id: int, user_id: str, prompt_file_path: str):
        """
        Gera o JSON do PEI e salva no banco de dados com embeddings para RAG.
        Não gera mais o PDF diretamente - isso será feito através de outra rota.
        """
        try:
            beneficiary = await self.beneficiary_repository.get_by_id(beneficiary_id)
            if not beneficiary:
                return Result.not_found("Beneficiário não encontrado")

            # Buscar informações da escola
            school = None
            school_name = "Não informado"
            if beneficiary.school_id:
                school = await self.school_repository.get_by_id(beneficiary.school_id)
                if school and school.name:
                    school_name = school.name

            # Calcular idade a partir da data de nascimento
            age = "Não informado"
            if beneficiary.date_of_birth:
                from datetime import date
                today = date.today()
                age_years = today.year - beneficiary.date_of_birth.year - ((today.month, today.day) < (beneficiary.date_of_birth.month, beneficiary.date_of_birth.day))
                age = f"{age_years} anos"

            try:
                prompt_content = self.storage_service.download_file(prompt_file_path)
                prompt_text = prompt_content.decode('utf-8')
            except Exception as e:
                return Result.error(f"Erro ao buscar arquivo de prompt: {str(e)}")

            self.llm_service.configure("gemini")
            prompt_embedding = await self.llm_service.generate_embeddings(prompt_text)

            study_case_embeddings = await self.study_case_embedding_gemini_repository.search_similar_by_beneficiary(
                query_embedding=prompt_embedding,
                beneficiary_id=beneficiary_id,
                limit=20
            )

            institution_embeddings = await self.institution_embedding_gemini_repository.search_similar_by_beneficiary(
                query_embedding=prompt_embedding,
                beneficiary_id=beneficiary_id,
                limit=20
            )

            # Buscar embeddings dos diários (se existirem)
            diary_embeddings = await self.diary_embedding_gemini_repository.search_similar_by_beneficiary(
                query_embedding=prompt_embedding,
                beneficiary_id=beneficiary_id,
                limit=20
            )

            # Construir informações estruturadas do beneficiário
            beneficiary_info = f"""=== INFORMAÇÕES DO BENEFICIÁRIO ===
Nome Completo: {beneficiary.name or 'Não informado'}
Idade: {age}
Diagnóstico: {beneficiary.diagnosis or 'Não informado'}
Escola: {school_name}
"""

            context_parts = [beneficiary_info]

            if study_case_embeddings:
                context_parts.append("\n=== INFORMAÇÕES DO ESTUDO DE CASO ===\n")
                for emb in study_case_embeddings:
                    context_parts.append(emb.content)
                    context_parts.append("\n")

            if institution_embeddings:
                context_parts.append("\n=== INFORMAÇÕES DA INSTITUIÇÃO ===\n")
                for emb in institution_embeddings:
                    context_parts.append(emb.content)
                    context_parts.append("\n")

            if diary_embeddings:
                context_parts.append("\n=== INFORMAÇÕES DOS DIÁRIOS ===\n")
                for emb in diary_embeddings:
                    context_parts.append(emb.content)
                    context_parts.append("\n")

            context = "\n".join(context_parts)

            if not context.strip():
                return Result.error("Não foram encontradas informações suficientes para gerar o PEI")

            full_prompt = f"""{prompt_text}

CONTEXTO COM INFORMAÇÕES DO ALUNO E INSTITUIÇÃO:
{context}

INSTRUÇÕES IMPORTANTES:
1. RETORNE APENAS UM JSON VÁLIDO sem nenhum texto adicional antes ou depois
2. O JSON deve conter todos os dados estruturados do PEI
3. UTILIZE AS INFORMAÇÕES ESTRUTURADAS DO BENEFICIÁRIO fornecidas acima (Nome Completo, Idade, Diagnóstico, Escola)
4. Procure no ESTUDO DE CASO as seguintes informações adicionais:
   - Ano ou série do aluno
   - CID (pode estar junto com o diagnóstico)
   - Nome do(a) Professor(a) principal
   - Nome do(a) Professor(a) auxiliar
   - Nome da mãe e do pai
   - Justificativa para o nível de suporte
   - Nome de especialistas envolvidos
5. Se alguma informação não estiver disponível, indique como "Não informado"

Por favor, gere um JSON estruturado e completo com todos os dados do Plano Educacional Individualizado (PEI) baseado nas informações acima."""

            pei_json_content = await self.llm_service.chat(full_prompt)
            pei_json_content = pei_json_content.strip()

            pei_json_content = re.sub(r"```json", "", pei_json_content, flags=re.IGNORECASE)
            pei_json_content = re.sub(r"```", "", pei_json_content)

            # 2. Remove quebras de linha e tabs excessivos
            pei_json_content = pei_json_content.replace("\n", "").replace("\t", "").strip()

            # 3. Extrai SOMENTE o JSON (do primeiro { ao último })
            match = re.search(r"\{.*\}", pei_json_content)
            if not match:
                raise ValueError("Nenhum JSON válido encontrado no conteúdo")

            pei_json_content = match.group(0)

            # Tentar fazer parse do JSON para validar
            try:
                pei_data = json.loads(pei_json_content)
            except json.JSONDecodeError as e:
                return Result.error(f"Erro ao parsear JSON do PEI: {str(e)}")

            # Salvar PEI no banco de dados
            pei = PEI(
                beneficiary_id=beneficiary_id,
                user_id=user_id,
                pei_data=pei_data,
                meta_data={
                    "prompt_file": prompt_file_path,
                    "model": "gemini",
                    "generated_at": datetime.now().isoformat()
                }
            )

            saved_pei = await self.pei_repository.add(pei)

            # Criar embeddings do PEI para RAG
            await self._create_pei_embeddings(
                pei_id=saved_pei.id,
                beneficiary_id=beneficiary_id,
                pei_data=pei_data
            )

            return Result.ok({
                "pei_id": saved_pei.id,
                "beneficiary_id": beneficiary_id,
                "generated_at": saved_pei.created_at.isoformat(),
                "message": "PEI gerado e salvo com sucesso. Use a rota /pei/generate-pdf para gerar o PDF."
            })

        except Exception as e:
            return Result.error(f"Erro ao gerar PEI: {str(e)}")

    async def _create_pei_embeddings(self, pei_id: int, beneficiary_id: int, pei_data: dict):
        """
        Cria embeddings do PEI dividindo o conteúdo em chunks.
        Cada seção do JSON será transformada em um chunk com embedding.
        """
        try:
            self.llm_service.configure("gemini")

            # Função recursiva para extrair texto do JSON
            def extract_text_chunks(data, parent_key=''):
                chunks = []

                if isinstance(data, dict):
                    for key, value in data.items():
                        current_key = f"{parent_key}.{key}" if parent_key else key

                        if isinstance(value, (dict, list)):
                            chunks.extend(extract_text_chunks(value, current_key))
                        elif isinstance(value, str) and value and value != "Não informado":
                            chunk_text = f"{current_key}: {value}"
                            chunks.append({
                                "text": chunk_text,
                                "section": current_key
                            })

                elif isinstance(data, list):
                    for idx, item in enumerate(data):
                        current_key = f"{parent_key}[{idx}]"
                        if isinstance(item, (dict, list)):
                            chunks.extend(extract_text_chunks(item, current_key))
                        elif isinstance(item, str) and item and item != "Não informado":
                            chunk_text = f"{current_key}: {item}"
                            chunks.append({
                                "text": chunk_text,
                                "section": current_key
                            })

                return chunks

            # Extrair chunks de texto do JSON
            text_chunks = extract_text_chunks(pei_data)

            # Criar embeddings para cada chunk
            for chunk in text_chunks:
                embedding = await self.llm_service.generate_embeddings(chunk["text"])

                pei_embedding = PEIEmbeddingGemini(
                    pei_id=pei_id,
                    beneficiary_id=beneficiary_id,
                    content=chunk["text"],
                    meta_data={"section": chunk["section"]},
                    embedding=embedding
                )

                await self.pei_embedding_gemini_repository.add(pei_embedding)

        except Exception as e:
            # Log do erro mas não falha a criação do PEI
            print(f"Erro ao criar embeddings do PEI: {str(e)}")
