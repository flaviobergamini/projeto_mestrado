from pydantic import BaseModel


class Institution(BaseModel):
    beneficiary_id: int
    institution_name: str
    institution_cnpj: str | None
    institution_type: str | None
    operating_hours: str | None
    full_address: str | None
    contact_phone: str | None
    institutional_email: str | None
    website: str | None
    education_levels_offered: str | None
    total_students: str | None
    total_students_with_tea: str | None
    max_capacity_students_with_tea: str | None
    total_classrooms: str | None
    has_multifunctional_resource_rooms: str | None
    has_sensory_or_relaxation_rooms: str | None
    physical_accessibility_adaptations: str | None
    total_teachers: str | None
    teachers_with_special_education_training: str | None
    teachers_with_tea_training: str | None
    has_multidisciplinary_team: str | None
    tea_training_frequency: str | None
    tea_training_methodologies: str | None
    mediators_or_support_teachers_count: str | None
    student_mediator_ratio: str | None
    curriculum_adaptation_practices: str | None
    teaching_methods_for_tea_students: str | None
    individualized_education_plan_creation: str | None
    evaluation_process_for_tea_students: str | None
    alternative_communication_resources: str | None
    visual_resources_for_routine_and_organization: str | None
    neurotypical_and_tea_students_integration: str | None
    sensory_stimulus_control: str | None
    adapted_materials_available: str | None
    has_spaces_for_crisis_or_sensory_overload: str | None
    provides_recess_or_break_adaptations: str | None
    technological_resources_for_tea_support: str | None
    provides_weighted_materials_for_sensory_regulation: str | None
    daily_communication_with_families: str | None
    meetings_with_parents_frequency: str | None
    provides_home_continuity_guidance: str | None
    has_support_group_for_families: str | None
    promotes_family_inclusive_events: str | None
    allows_external_therapists: str | None
    partnerships_with_specialized_clinics: str | None
    pedagogical_and_therapeutic_integration: str | None
    participates_in_inclusion_support_networks: str | None
    medication_administration_protocol: str | None
    has_certification_for_tea_service: str | None
    required_documents_for_enrollment: str | None
    issues_periodic_development_reports: str | None
    has_public_agency_agreements: str | None
    student_progress_tracking_method: str | None

    def get_info_to_string(self) -> str:
        info = f"Cadastro de Instituição\n\n"

        info += "=== INFORMAÇÕES BÁSICAS ===\n"
        info += f"Nome da Instituição: {self.institution_name}\n"
        info += f"CNPJ: {self.institution_cnpj}\n"
        info += f"Tipo de Instituição: {self.institution_type}\n"
        info += f"Horário de Funcionamento: {self.operating_hours}\n"
        info += f"Endereço Completo: {self.full_address}\n"
        info += f"Telefone de Contato: {self.contact_phone}\n"
        info += f"E-mail Institucional: {self.institutional_email}\n"
        info += f"Website: {self.website}\n\n"

        info += "=== INFORMAÇÕES SOBRE CAPACIDADE E ESTRUTURA ===\n"
        info += f"Níveis de Ensino Oferecidos: {self.education_levels_offered}\n"
        info += f"Total de Alunos: {self.total_students}\n"
        info += f"Total de Alunos com TEA: {self.total_students_with_tea}\n"
        info += f"Capacidade Máxima de Alunos com TEA: {self.max_capacity_students_with_tea}\n"
        info += f"Total de Salas de Aula: {self.total_classrooms}\n"
        info += f"Possui Salas de Recursos Multifuncionais: {self.has_multifunctional_resource_rooms}\n"
        info += f"Possui Salas Sensoriais ou de Relaxamento: {self.has_sensory_or_relaxation_rooms}\n"
        info += f"Adaptações de Acessibilidade Física: {self.physical_accessibility_adaptations}\n\n"

        info += "=== RECURSOS HUMANOS E CAPACITAÇÃO ===\n"
        info += f"Total de Professores: {self.total_teachers}\n"
        info += f"Professores com Formação em Educação Especial: {self.teachers_with_special_education_training}\n"
        info += f"Professores com Formação em TEA: {self.teachers_with_tea_training}\n"
        info += f"Possui Equipe Multidisciplinar: {self.has_multidisciplinary_team}\n"
        info += f"Frequência de Capacitação sobre TEA: {self.tea_training_frequency}\n"
        info += f"Metodologias de Capacitação sobre TEA: {self.tea_training_methodologies}\n"
        info += f"Quantidade de Mediadores ou Professores de Apoio: {self.mediators_or_support_teachers_count}\n"
        info += f"Proporção Aluno/Mediador: {self.student_mediator_ratio}\n\n"

        info += "=== PRÁTICAS PEDAGÓGICAS E METODOLOGIAS ===\n"
        info += f"Práticas de Adaptação Curricular: {self.curriculum_adaptation_practices}\n"
        info += f"Métodos de Ensino para Alunos com TEA: {self.teaching_methods_for_tea_students}\n"
        info += f"Criação de Plano Educacional Individualizado: {self.individualized_education_plan_creation}\n"
        info += f"Processo de Avaliação para Alunos com TEA: {self.evaluation_process_for_tea_students}\n\n"

        info += "=== RECURSOS DE COMUNICAÇÃO E ORGANIZAÇÃO ===\n"
        info += f"Recursos de Comunicação Alternativa: {self.alternative_communication_resources}\n"
        info += f"Recursos Visuais para Rotina e Organização: {self.visual_resources_for_routine_and_organization}\n"
        info += f"Integração entre Alunos Neurotípicos e com TEA: {self.neurotypical_and_tea_students_integration}\n"
        info += f"Controle de Estímulos Sensoriais: {self.sensory_stimulus_control}\n\n"

        info += "=== APOIOS E SUPORTES ESPECIALIZADOS ===\n"
        info += f"Materiais Adaptados Disponíveis: {self.adapted_materials_available}\n"
        info += f"Possui Espaços para Crises ou Sobrecarga Sensorial: {self.has_spaces_for_crisis_or_sensory_overload}\n"
        info += f"Oferece Adaptações no Recreio ou Intervalos: {self.provides_recess_or_break_adaptations}\n"
        info += f"Recursos Tecnológicos de Apoio ao TEA: {self.technological_resources_for_tea_support}\n"
        info += f"Oferece Materiais Pesados para Regulação Sensorial: {self.provides_weighted_materials_for_sensory_regulation}\n\n"

        info += "=== COMUNICAÇÃO E ENVOLVIMENTO COM FAMÍLIAS ===\n"
        info += f"Comunicação Diária com Famílias: {self.daily_communication_with_families}\n"
        info += f"Frequência de Reuniões com Pais: {self.meetings_with_parents_frequency}\n"
        info += f"Oferece Orientações de Continuidade em Casa: {self.provides_home_continuity_guidance}\n"
        info += f"Possui Grupo de Apoio para Famílias: {self.has_support_group_for_families}\n"
        info += f"Promove Eventos Inclusivos com Famílias: {self.promotes_family_inclusive_events}\n\n"

        info += "=== PARCERIAS E INTEGRAÇÕES ===\n"
        info += f"Permite Terapeutas Externos: {self.allows_external_therapists}\n"
        info += f"Parcerias com Clínicas Especializadas: {self.partnerships_with_specialized_clinics}\n"
        info += f"Integração Pedagógica e Terapêutica: {self.pedagogical_and_therapeutic_integration}\n"
        info += f"Participa de Redes de Apoio à Inclusão: {self.participates_in_inclusion_support_networks}\n\n"

        info += "=== PROTOCOLOS E CERTIFICAÇÕES ===\n"
        info += f"Protocolo de Administração de Medicamentos: {self.medication_administration_protocol}\n"
        info += f"Possui Certificação para Atendimento a TEA: {self.has_certification_for_tea_service}\n"
        info += f"Documentos Exigidos para Matrícula: {self.required_documents_for_enrollment}\n"
        info += f"Emite Relatórios Periódicos de Desenvolvimento: {self.issues_periodic_development_reports}\n"
        info += f"Possui Convênios com Órgãos Públicos: {self.has_public_agency_agreements}\n"
        info += f"Método de Acompanhamento do Progresso do Aluno: {self.student_progress_tracking_method}\n"

        return info
