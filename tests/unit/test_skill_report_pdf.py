from infrastructure.services.skill_report_pdf import generate_skill_report_pdf


def test_pdf_with_adaptations_renders():
    skill = {"code": "EF01LP01", "description": "Desc", "score": 2, "observation": "obs",
             "adaptations": [{"adaptation": "Usar cartões", "justification": "Gosta de imagens",
                              "actions": ["Mostrar cartões", "Pedir para ordenar"], "responsibles": ["Ana", "Bia"]}]}
    report = {"title": "R", "content": {"filters": {"include_observations": True}, "summary": {"total": 1, "average": 2, "by_score": {"2": 1}},
                                        "groups": [{"grade": "1º ano", "areas": [{"area": "Língua Portuguesa", "skills": [skill, {**skill, "adaptations": []}]}]}]}}
    assert generate_skill_report_pdf(report, "Aluno")[:4] == b"%PDF"
    report["content"]["filters"]["include_observations"] = False
    assert generate_skill_report_pdf(report, "Aluno")[:4] == b"%PDF"
