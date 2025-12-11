from datetime import datetime
import io
import re
from html.parser import HTMLParser
import markdown
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository
from infrastructure.repositories.study_case_embedding_gemini_repository import StudyCaseEmbeddingGeminiRepository
from infrastructure.repositories.institution_embedding_gemini_repository import InstitutionEmbeddingGeminiRepository
from infrastructure.repositories.school_repository import SchoolRepository
from infrastructure.services.llm_service import LLMService
from infrastructure.services.storage_service import StorageService
from core.kernel.result import Result


class GeneratePEIUseCase:
    def __init__(
        self,
        beneficiary_repository: BeneficiaryRepository,
        study_case_embedding_gemini_repository: StudyCaseEmbeddingGeminiRepository,
        institution_embedding_gemini_repository: InstitutionEmbeddingGeminiRepository,
        school_repository: SchoolRepository,
        llm_service: LLMService,
        storage_service: StorageService
    ):
        self.beneficiary_repository = beneficiary_repository
        self.study_case_embedding_gemini_repository = study_case_embedding_gemini_repository
        self.institution_embedding_gemini_repository = institution_embedding_gemini_repository
        self.school_repository = school_repository
        self.llm_service = llm_service
        self.storage_service = storage_service

    async def execute(self, beneficiary_id: int, user_id: str, prompt_file_path: str, return_pdf_buffer: bool = False):
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

            context = "\n".join(context_parts)

            if not context.strip():
                return Result.error("Não foram encontradas informações suficientes para gerar o PEI")

            full_prompt = f"""{prompt_text}

CONTEXTO COM INFORMAÇÕES DO ALUNO E INSTITUIÇÃO:
{context}

INSTRUÇÕES IMPORTANTES:
1. UTILIZE AS INFORMAÇÕES ESTRUTURADAS DO BENEFICIÁRIO fornecidas acima (Nome Completo, Idade, Diagnóstico, Escola)
2. Procure no ESTUDO DE CASO as seguintes informações adicionais:
   - Ano ou série do aluno
   - CID (pode estar junto com o diagnóstico)
   - Nome do(a) Professor(a) principal
   - Nome do(a) Professor(a) auxiliar
   - Nome da mãe e do pai
   - Justificativa para o nível de suporte
   - Nome de especialistas envolvidos
3. Inclua TODAS essas informações na seção "Identificação do Estudante" do PEI
4. Se alguma informação não estiver disponível, indique como "Não informado"

Por favor, gere um Plano Educacional Individualizado (PEI) completo e detalhado baseado nas informações acima."""

            pei_content = await self.llm_service.chat(full_prompt)

            pdf_buffer = self._generate_pdf(
                pei_content=pei_content,
                beneficiary_name=beneficiary.name or "Não informado",
                beneficiary_id=beneficiary_id,
                age=age,
                diagnosis=beneficiary.diagnosis or "Não informado",
                school_name=school_name
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"PEI_{beneficiary.name.replace(' ', '_')}_{timestamp}.pdf"
            pdf_content_bytes = pdf_buffer.getvalue()

            pdf_path, pdf_url = self.storage_service.upload_file(
                file_content=pdf_content_bytes,
                filename=filename,
                user_id=user_id,
                content_type="application/pdf"
            )

            result_data = {
                "pdf_path": pdf_path,
                "pdf_url": pdf_url,
                "beneficiary_id": beneficiary_id,
                "generated_at": datetime.now().isoformat(),
            }

            if return_pdf_buffer:
                result_data['pdf_content'] = pdf_content_bytes
                result_data['filename'] = filename

            return Result.ok(result_data)

        except Exception as e:
            return Result.error(f"Erro ao gerar PEI: {str(e)}")

    def _clean_html_for_reportlab(self, html_text: str) -> str:
        """
        Limpa e converte HTML para um formato aceito pelo ReportLab.
        Remove tags complexas e mantém apenas formatação básica suportada.
        """
        # Remover tags de tabela complexas que podem causar problemas
        html_text = re.sub(r'<table[^>]*>.*?</table>', '', html_text, flags=re.DOTALL)

        # Garantir que tags estejam corretamente fechadas
        # Substituir tags não suportadas por suportadas
        html_text = html_text.replace('<strong>', '<b>').replace('</strong>', '</b>')
        html_text = html_text.replace('<em>', '<i>').replace('</em>', '</i>')

        # Remover tags HTML não suportadas pelo ReportLab, mantendo o conteúdo
        html_text = re.sub(r'<h[1-6][^>]*>', '<b>', html_text)
        html_text = re.sub(r'</h[1-6]>', '</b>', html_text)

        # Remover outras tags não suportadas mantendo o conteúdo
        html_text = re.sub(r'</?div[^>]*>', '', html_text)
        html_text = re.sub(r'</?span[^>]*>', '', html_text)
        html_text = re.sub(r'</?section[^>]*>', '', html_text)
        html_text = re.sub(r'</?article[^>]*>', '', html_text)

        # Converter quebras de linha
        html_text = html_text.replace('<br>', '<br/>')
        html_text = html_text.replace('<br/><br/>', '<br/>')

        return html_text

    def _markdown_to_story_elements(self, md_content: str, styles: dict):
        """
        Converte conteúdo Markdown em elementos do ReportLab (Paragraph, Spacer, etc)
        """
        story = []

        # Processar linha por linha para melhor controle
        lines = md_content.split('\n')
        i = 0
        in_list = False

        while i < len(lines):
            line = lines[i].rstrip()

            # Linha vazia
            if not line:
                if in_list:
                    story.append(Spacer(1, 0.05 * inch))
                    in_list = False
                else:
                    story.append(Spacer(1, 0.1 * inch))
                i += 1
                continue

            # Headers (##)
            if line.startswith('##'):
                level = len(line) - len(line.lstrip('#'))
                text = line.lstrip('#').strip()

                if level == 2:
                    story.append(Spacer(1, 0.2 * inch))
                    story.append(Paragraph(text, styles['heading2']))
                    story.append(Spacer(1, 0.1 * inch))
                elif level == 3:
                    story.append(Spacer(1, 0.15 * inch))
                    story.append(Paragraph(text, styles['heading3']))
                elif level == 4:
                    story.append(Paragraph(f"<b>{text}</b>", styles['normal']))
                else:
                    story.append(Paragraph(text, styles['heading2']))

                in_list = False
                i += 1
                continue

            # Lista com * ou -
            if line.lstrip().startswith(('* ', '- ', '• ')):
                # Determinar nível de indentação
                indent_level = (len(line) - len(line.lstrip())) // 4
                text = line.lstrip('*- •').strip()

                # Processar formatação inline (negrito e itálico)
                text = self._process_inline_formatting(text)

                # Adicionar bullet point
                bullet = '•' if indent_level == 0 else '◦'
                indent = '    ' * indent_level

                story.append(Paragraph(f"{indent}{bullet} {text}", styles['list']))
                in_list = True
                i += 1
                continue

            # Texto normal (pode conter formatação inline)
            if line.strip():
                # Processar formatação inline
                text = self._process_inline_formatting(line)
                story.append(Paragraph(text, styles['normal']))
                in_list = False

            i += 1

        return story

    def _process_inline_formatting(self, text: str) -> str:
        """
        Processa formatação inline do Markdown (negrito e itálico) de forma segura
        """
        # Escapar caracteres especiais do XML/HTML
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Processar negrito (**texto**)
        # Usar regex para encontrar pares de **
        text = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', text)

        # Processar itálico (*texto* ou _texto_)
        # Importante: fazer isso DEPOIS do negrito para evitar conflitos
        text = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
        text = re.sub(r'_([^_]+?)_', r'<i>\1</i>', text)

        return text

    def _generate_pdf(self, pei_content: str, beneficiary_name: str, beneficiary_id: int, age: str, diagnosis: str, school_name: str) -> io.BytesIO:
        """Gera um PDF formatado com o conteúdo do PEI"""
        buffer = io.BytesIO()

        # Criar documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=36,
        )

        # Estilos
        base_styles = getSampleStyleSheet()

        styles = {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=base_styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ),
            'heading2': ParagraphStyle(
                'CustomHeading2',
                parent=base_styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=10,
                spaceBefore=15,
                fontName='Helvetica-Bold',
                leftIndent=0
            ),
            'heading3': ParagraphStyle(
                'CustomHeading3',
                parent=base_styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=8,
                spaceBefore=10,
                fontName='Helvetica-Bold',
                leftIndent=0
            ),
            'normal': ParagraphStyle(
                'CustomNormal',
                parent=base_styles['Normal'],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=6,
                leading=14,
                fontName='Helvetica',
                leftIndent=0
            ),
            'list': ParagraphStyle(
                'CustomList',
                parent=base_styles['Normal'],
                fontSize=10,
                alignment=TA_LEFT,
                spaceAfter=4,
                leading=13,
                fontName='Helvetica',
                leftIndent=20,
                firstLineIndent=0
            )
        }

        # Conteúdo do PDF
        story = []

        # Título
        story.append(Paragraph("PLANO EDUCACIONAL INDIVIDUALIZADO (PEI)", styles['title']))
        story.append(Spacer(1, 0.2 * inch))

        # Informações do aluno no cabeçalho
        story.append(Paragraph(f"<b>Nome Completo:</b> {beneficiary_name}", styles['normal']))
        story.append(Paragraph(f"<b>Idade:</b> {age}", styles['normal']))
        story.append(Paragraph(f"<b>Diagnóstico:</b> {diagnosis}", styles['normal']))
        story.append(Paragraph(f"<b>Escola:</b> {school_name}", styles['normal']))
        story.append(Paragraph(f"<b>Data de Geração:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['normal']))
        story.append(Spacer(1, 0.3 * inch))

        # Processar conteúdo Markdown do PEI
        pei_elements = self._markdown_to_story_elements(pei_content, styles)
        story.extend(pei_elements)

        # Gerar PDF
        doc.build(story)
        buffer.seek(0)

        return buffer
