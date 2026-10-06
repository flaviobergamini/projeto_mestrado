from core.interfaces.i_report_pdf_generator import IReportPdfGenerator
from infrastructure.services.skill_report_pdf import generate_skill_report_pdf


class ReportPdfGenerator(IReportPdfGenerator):
    def skill_report(self, report: dict, student_name: str) -> bytes:
        return generate_skill_report_pdf(report, student_name)
