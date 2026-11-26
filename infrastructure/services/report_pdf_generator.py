from core.interfaces.i_report_pdf_generator import IReportPdfGenerator
from infrastructure.services.skill_report_pdf import generate_skill_report_pdf
from infrastructure.services.kanban_report_pdf import generate_kanban_report_pdf
from infrastructure.services.functional_profile_pdf import generate_functional_profile_pdf


class ReportPdfGenerator(IReportPdfGenerator):
    def skill_report(self, report: dict, student_name: str) -> bytes:
        return generate_skill_report_pdf(report, student_name)

    def kanban_report(self, report: dict, student_name: str) -> bytes:
        return generate_kanban_report_pdf(report, student_name)

    def functional_profile(self, profile: dict, student_name: str) -> bytes:
        return generate_functional_profile_pdf(profile, student_name)
