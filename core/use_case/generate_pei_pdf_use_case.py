from datetime import datetime
import io
import re
import json
import markdown
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors

from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository
from infrastructure.repositories.pei_repository import PEIRepository
from infrastructure.repositories.pei_embedding_gemini_repository import PEIEmbeddingGeminiRepository
from infrastructure.repositories.school_repository import SchoolRepository
from infrastructure.services.llm_service import LLMService
from infrastructure.services.storage_service import StorageService
from core.kernel.result import Result


class GeneratePEIPDFUseCase:
    def __init__(
        self,
        beneficiary_repository: BeneficiaryRepository,
        pei_repository: PEIRepository,
        pei_embedding_gemini_repository: PEIEmbeddingGeminiRepository,
        school_repository: SchoolRepository,
        llm_service: LLMService,
        storage_service: StorageService
    ):
        self.beneficiary_repository = beneficiary_repository
        self.pei_repository = pei_repository
        self.pei_embedding_gemini_repository = pei_embedding_gemini_repository
        self.school_repository = school_repository
        self.llm_service = llm_service
        self.storage_service = storage_service

    async def execute(self, pei_id: int, user_id: str, return_pdf_buffer: bool = False):
        """
        Gera um PDF do PEI a partir do JSON salvo no banco de dados.
        Usa RAG para buscar informações relevantes dos embeddings do PEI.
        """
        try:
            # Buscar o PEI salvo
            pei = await self.pei_repository.get_by_id(pei_id)
            if not pei:
                return Result.not_found("PEI não encontrado")

            # Buscar informações do beneficiário
            beneficiary = await self.beneficiary_repository.get_by_id(pei.beneficiary_id)
            if not beneficiary:
                return Result.not_found("Beneficiário não encontrado")

            # Buscar informações da escola
            school_name = "Não informado"
            if beneficiary.school_id:
                school = await self.school_repository.get_by_id(beneficiary.school_id)
                if school and school.name:
                    school_name = school.name

            # Calcular idade
            age = "Não informado"
            if beneficiary.date_of_birth:
                from datetime import date
                today = date.today()
                age_years = today.year - beneficiary.date_of_birth.year - ((today.month, today.day) < (beneficiary.date_of_birth.month, beneficiary.date_of_birth.day))
                age = f"{age_years} anos"

            # Usar RAG para buscar informações relevantes do PEI
            self.llm_service.configure("gemini")

            # Criar uma query para buscar informações do PEI
            search_query = f"Informações do Plano Educacional Individualizado do aluno {beneficiary.name}"
            query_embedding = await self.llm_service.generate_embeddings(search_query)

            # Buscar embeddings similares
            pei_embeddings = await self.pei_embedding_gemini_repository.get_by_pei_id(pei_id)

            # Construir contexto do PEI a partir dos embeddings
            pei_context_parts = []
            if pei_embeddings:
                pei_context_parts.append("=== INFORMAÇÕES DO PEI ===\n")
                for emb in pei_embeddings:
                    pei_context_parts.append(emb.content)
                    pei_context_parts.append("\n")

            pei_context = "\n".join(pei_context_parts)

            # Converter o JSON do PEI para uma representação legível
            pei_json_str = json.dumps(pei.pei_data, indent=2, ensure_ascii=False)

            # Gerar texto bonito em Markdown através da LLM
            markdown_prompt = f"""Você é um especialista em educação especial e deve gerar um documento em Markdown formatado e bonito para um Plano Educacional Individualizado (PEI).

DADOS DO PEI EM JSON:
{pei_json_str}

CONTEXTO ADICIONAL (use para enriquecer o documento):
{pei_context}

INFORMAÇÕES DO ALUNO:
Nome: {beneficiary.name or 'Não informado'}
Idade: {age}
Diagnóstico: {beneficiary.diagnosis or 'Não informado'}
Escola: {school_name}

INSTRUÇÕES:
1. Crie um documento em Markdown bem estruturado e formatado
2. Organize as informações de forma lógica e profissional
3. Use títulos (##), subtítulos (###), listas e formatação adequada
4. Inclua todas as informações relevantes do JSON
5. Torne o texto claro, objetivo e profissional
6. NÃO inclua a seção "Identificação do Estudante" pois ela será adicionada automaticamente no cabeçalho do PDF
7. Retorne APENAS o conteúdo em Markdown, sem explicações adicionais

Por favor, gere o documento em Markdown:"""

            markdown_content = await self.llm_service.chat(markdown_prompt)

            # Gerar o PDF
            pdf_buffer = self._generate_pdf(
                pei_content=markdown_content,
                beneficiary_name=beneficiary.name or "Não informado",
                beneficiary_id=pei.beneficiary_id,
                age=age,
                diagnosis=beneficiary.diagnosis or "Não informado",
                school_name=school_name
            )

            # Salvar PDF no storage
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
                "pei_id": pei_id,
                "beneficiary_id": pei.beneficiary_id,
                "generated_at": datetime.now().isoformat(),
            }

            if return_pdf_buffer:
                result_data['pdf_content'] = pdf_content_bytes
                result_data['filename'] = filename

            return Result.ok(result_data)

        except Exception as e:
            return Result.error(f"Erro ao gerar PDF do PEI: {str(e)}")

    def _markdown_to_story_elements(self, md_content: str, styles: dict):
        """Converte conteúdo Markdown em elementos do ReportLab"""
        story = []
        lines = md_content.split('\n')
        i = 0
        in_list = False

        while i < len(lines):
            line = lines[i].rstrip()

            if not line:
                if in_list:
                    story.append(Spacer(1, 0.05 * inch))
                    in_list = False
                else:
                    story.append(Spacer(1, 0.1 * inch))
                i += 1
                continue

            # Headers
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

            # Lista
            if line.lstrip().startswith(('* ', '- ', '• ')):
                indent_level = (len(line) - len(line.lstrip())) // 4
                text = line.lstrip('*- •').strip()
                text = self._process_inline_formatting(text)
                bullet = '•' if indent_level == 0 else '◦'
                indent = '    ' * indent_level

                story.append(Paragraph(f"{indent}{bullet} {text}", styles['list']))
                in_list = True
                i += 1
                continue

            # Texto normal
            if line.strip():
                text = self._process_inline_formatting(line)
                story.append(Paragraph(text, styles['normal']))
                in_list = False

            i += 1

        return story

    def _process_inline_formatting(self, text: str) -> str:
        """Processa formatação inline do Markdown"""
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        text = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
        text = re.sub(r'_([^_]+?)_', r'<i>\1</i>', text)
        return text

    def _generate_pdf(self, pei_content: str, beneficiary_name: str, beneficiary_id: int, age: str, diagnosis: str, school_name: str) -> io.BytesIO:
        """Gera um PDF formatado com o conteúdo do PEI"""
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=36,
        )

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

        story = []

        # Título
        story.append(Paragraph("PLANO EDUCACIONAL INDIVIDUALIZADO (PEI)", styles['title']))
        story.append(Spacer(1, 0.2 * inch))

        # Cabeçalho com informações do aluno
        story.append(Paragraph(f"<b>Nome Completo:</b> {beneficiary_name}", styles['normal']))
        story.append(Paragraph(f"<b>Idade:</b> {age}", styles['normal']))
        story.append(Paragraph(f"<b>Diagnóstico:</b> {diagnosis}", styles['normal']))
        story.append(Paragraph(f"<b>Escola:</b> {school_name}", styles['normal']))
        story.append(Paragraph(f"<b>Data de Geração:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['normal']))
        story.append(Spacer(1, 0.3 * inch))

        # Processar conteúdo Markdown
        pei_elements = self._markdown_to_story_elements(pei_content, styles)
        story.extend(pei_elements)

        doc.build(story)
        buffer.seek(0)

        return buffer
