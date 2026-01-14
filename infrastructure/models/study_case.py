from pydantic import BaseModel
from typing import Optional


class StudyCase(BaseModel):
    beneficiary_id: int
    custom_questions: Optional[dict] = None

    '''# Informações gerais do aluno
    student_difficulties: str | None
    student_likes_school: bool | None
    observation_question_above: str | None
    student_has_friends: bool | None
    which_friends: str | None
    student_has_favorite_classmate: bool | None
    which_favorite_classmate: str | None
    students_favorite_activities: str | None
    students_difficult_tasks_and_reasons: str | None
    students_express_needs_in_what_way: str | None
    student_asks_teachers_for_help_why: str | None
    # Novas perguntas — seção de percepções e apoios
    student_opinion_about_teachers: str | None
    student_opinion_about_school_importance: str | None
    student_school_supports: str | None
    student_satisfied_with_supports: str | None
    student_wants_other_supports: str | None
    student_special_interest: str | None
    student_participation_in_activities: str | None
    student_easy_and_difficult_activities: str | None
    student_participation_level: str | None
    student_specific_needs_and_barriers: str | None
    student_clinical_or_educational_services: str | None
    teachers_opinion_about_student_expectations: str | None
    teachers_evaluation_about_student_performance: str | None
    teachers_concerns_and_suggested_supports: str | None
    school_community_perception_about_interaction: str | None
    teachers_expectations_about_student: str | None
    student_skills_and_potential: str | None
    reason_for_requesting_aee_services: str | None
    school_accessibility_resources: str | None
    school_resources_evaluation: str | None
    student_affective_and_social_involvement: str | None
    school_opinion_about_student_development: str | None
    # Família
    family_opinion_about_school_life: str | None
    family_involvement_with_school: str | None
    family_awareness_of_inclusive_rights: str | None
    family_identified_skills_and_difficulties: str | None
    family_expectations_about_development: str | None
    # Aspectos socioemocionais e comportamentais
    interacts_without_constant_mediation: bool | None
    initiates_social_interactions_spontaneously: bool | None
    participates_with_stimuli: bool | None
    waits_turn_and_handles_frustration: bool | None
    shares_experiences_or_limited_interactions: bool | None
    expresses_basic_emotions_clearly: bool | None
    reacts_positively_to_praise: bool | None
    seeks_emotional_support: bool | None
    emotionally_dysregulated_with_routine_changes: bool | None
    calms_down_with_minimal_help: bool | None
    interested_in_learning_new_things: bool | None
    follows_simple_instructions: bool | None
    maintains_attention_appropriately: bool | None
    solves_simple_problems_independently: bool | None
    learns_better_with_visual_support: bool | None
    # Aspectos motores e de autocuidado
    fine_motor_coordination: bool | None
    gross_motor_coordination: bool | None
    performs_self_care_independently: bool | None
    participates_in_physical_activities_without_fatigue: bool | None
    shows_repetitive_motor_behaviors: bool | None
    # Alimentação
    limited_food_repertoire: str | None
    needs_physical_assistance_to_eat: str | None
    discomfort_with_food_touching: str | None
    eats_better_in_quiet_environment: str | None
    challenging_behavior_during_meals: str | None
    # Comunicação escola-família
    frequent_school_family_communication: bool | None
    family_provides_emotional_support: bool | None
    family_collaboration_in_therapeutic_resources: bool | None
    family_open_to_new_approaches: bool | None
    family_participates_in_events: bool | None
    # Contatos e informações adicionais
    family_email: str | None
    pedagogical_adaptations: str | None
    pedagogical_development: str | None
    additional_personal_information: str | None
    # Identificação
    mother_name: str | None
    father_name: str | None
    school_name: str | None
    main_teacher_name: str | None
    assistant_teacher_name: str | None

    def get_info_to_string(self) -> str:
        info = f"Estudo de Caso \n\n"

        info += "=== INFORMAÇÕES GERAIS DO ALUNO ===\n"
        info += f"Dificuldades do aluno: {self.student_difficulties}\n"
        info += f"Gosta da escola: {self.student_likes_school}\n"
        info += f"Observações adicionais: {self.observation_question_above}\n"
        info += f"Possui amigos: {self.student_has_friends}\n"
        info += f"Quais amigos: {self.which_friends}\n"
        info += f"Possui colega favorito: {self.student_has_favorite_classmate}\n"
        info += f"Qual colega favorito: {self.which_favorite_classmate}\n"
        info += f"Atividades favoritas: {self.students_favorite_activities}\n"
        info += f"Tarefas difíceis e motivos: {self.students_difficult_tasks_and_reasons}\n"
        info += f"Forma de expressar necessidades: {self.students_express_needs_in_what_way}\n"
        info += f"Quando pede ajuda aos professores, por quê: {self.student_asks_teachers_for_help_why}\n\n"

        info += "=== PERCEPÇÕES E APOIOS ===\n"
        info += f"Opinião do aluno sobre os professores: {self.student_opinion_about_teachers}\n"
        info += f"Opinião sobre a importância da escola: {self.student_opinion_about_school_importance}\n"
        info += f"Apoios disponíveis na escola: {self.student_school_supports}\n"
        info += f"Satisfação com os apoios recebidos: {self.student_satisfied_with_supports}\n"
        info += f"Gostaria de outros apoios: {self.student_wants_other_supports}\n"
        info += f"Interesses especiais: {self.student_special_interest}\n"
        info += f"Participação em atividades: {self.student_participation_in_activities}\n"
        info += f"Atividades fáceis e difíceis: {self.student_easy_and_difficult_activities}\n"
        info += f"Nível de participação: {self.student_participation_level}\n"
        info += f"Necessidades específicas e barreiras: {self.student_specific_needs_and_barriers}\n"
        info += f"Serviços clínicos ou educacionais: {self.student_clinical_or_educational_services}\n\n"

        info += "=== ASPECTOS SOCIOEMOCIONAIS ===\n"
        info += f"Interage sem mediação constante: {self.interacts_without_constant_mediation}\n"
        info += f"Inicia interações sociais espontaneamente: {self.initiates_social_interactions_spontaneously}\n"
        info += f"Participa com estímulos: {self.participates_with_stimuli}\n"
        info += f"Espera sua vez e lida com frustrações: {self.waits_turn_and_handles_frustration}\n"
        info += f"Compartilha experiências: {self.shares_experiences_or_limited_interactions}\n"
        info += f"Expressa emoções básicas claramente: {self.expresses_basic_emotions_clearly}\n"
        info += f"Reage positivamente a elogios: {self.reacts_positively_to_praise}\n"
        info += f"Busca apoio emocional: {self.seeks_emotional_support}\n"
        info += f"Fica desregulado com mudanças de rotina: {self.emotionally_dysregulated_with_routine_changes}\n"
        info += f"Acalma-se com ajuda mínima: {self.calms_down_with_minimal_help}\n"
        info += f"Interesse em aprender coisas novas: {self.interested_in_learning_new_things}\n"
        info += f"Segue instruções simples: {self.follows_simple_instructions}\n"
        info += f"Mantém atenção adequadamente: {self.maintains_attention_appropriately}\n"
        info += f"Resolve problemas simples sozinho: {self.solves_simple_problems_independently}\n"
        info += f"Aprende melhor com suporte visual: {self.learns_better_with_visual_support}\n\n"

        info += "=== ASPECTOS MOTORES E DE AUTOCUIDADO ===\n"
        info += f"Coordenação motora fina: {self.fine_motor_coordination}\n"
        info += f"Coordenação motora grossa: {self.gross_motor_coordination}\n"
        info += f"Realiza autocuidado de forma independente: {self.performs_self_care_independently}\n"
        info += f"Participa de atividades físicas sem fadiga: {self.participates_in_physical_activities_without_fatigue}\n"
        info += f"Apresenta comportamentos motores repetitivos: {self.shows_repetitive_motor_behaviors}\n\n"

        info += "=== ALIMENTAÇÃO ===\n"
        info += f"Repertório alimentar limitado: {self.limited_food_repertoire}\n"
        info += f"Necessita assistência física para comer: {self.needs_physical_assistance_to_eat}\n"
        info += f"Desconforto com alimentos que se tocam: {self.discomfort_with_food_touching}\n"
        info += f"Alimenta-se melhor em ambiente silencioso: {self.eats_better_in_quiet_environment}\n"
        info += f"Comportamentos desafiadores durante refeições: {self.challenging_behavior_during_meals}\n\n"

        info += "=== COMUNICAÇÃO ESCOLA-FAMÍLIA ===\n"
        info += f"Comunicação frequente entre escola e família: {self.frequent_school_family_communication}\n"
        info += f"Família oferece apoio emocional: {self.family_provides_emotional_support}\n"
        info += f"Família colabora em recursos terapêuticos: {self.family_collaboration_in_therapeutic_resources}\n"
        info += f"Família aberta a novas abordagens: {self.family_open_to_new_approaches}\n"
        info += f"Família participa de eventos: {self.family_participates_in_events}\n\n"

        info += "=== INFORMAÇÕES ADICIONAIS ===\n"
        info += f"E-mail da família: {self.family_email}\n"
        info += f"Adaptações pedagógicas: {self.pedagogical_adaptations}\n"
        info += f"Desenvolvimento pedagógico: {self.pedagogical_development}\n"
        info += f"Informações pessoais adicionais: {self.additional_personal_information}\n\n"

        info += "=== IDENTIFICAÇÃO ===\n"
        info += f"Nome da mãe: {self.mother_name}\n"
        info += f"Nome do pai: {self.father_name}\n"
        info += f"Nome da escola: {self.school_name}\n"
        info += f"Professor(a) principal: {self.main_teacher_name}\n"
        info += f"Professor(a) auxiliar: {self.assistant_teacher_name}\n"

        return info'''
