from abc import ABC, abstractmethod


class IReportPdfGenerator(ABC):

    @abstractmethod
    def skill_report(self, report: dict, student_name: str) -> bytes:
        ...

    @abstractmethod
    def kanban_report(self, report: dict, student_name: str) -> bytes:
        ...
