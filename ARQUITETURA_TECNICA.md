# Documentação Técnica da Arquitetura
## Agente de IA para Educação Inclusiva - TEA

**Versão:** 1.0
**Data:** Janeiro 2026
**Projeto:** Mestrado em Educação Inclusiva

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Estrutura de Camadas](#4-estrutura-de-camadas)
5. [Modelo de Dados](#5-modelo-de-dados)
6. [Serviços e Funcionalidades](#6-serviços-e-funcionalidades)
7. [Sistema RAG (Retrieval-Augmented Generation)](#7-sistema-rag-retrieval-augmented-generation)
8. [Fluxos Principais](#8-fluxos-principais)
9. [Segurança e Autenticação](#9-segurança-e-autenticação)
10. [Infraestrutura e Deploy](#10-infraestrutura-e-deploy)
11. [Configuração de Ambiente](#11-configuração-de-ambiente)

---

## 1. Visão Geral

### 1.1 Propósito do Sistema

O sistema é uma **plataforma de suporte à educação inclusiva** voltada para alunos com **Transtorno do Espectro Autista (TEA)**. Desenvolvido como projeto de mestrado, o sistema utiliza **Inteligência Artificial Generativa** para auxiliar educadores, terapeutas e famílias no acompanhamento e planejamento educacional de beneficiários.

### 1.2 Principais Objetivos

- **Registro diário estruturado** de comportamento, socialização, comunicação e autonomia
- **Geração automatizada de PEI** (Plano Educacional Individualizado) com IA
- **Análise de padrões comportamentais** usando embeddings e busca semântica
- **Gestão integrada** de beneficiários, escolas, clínicas e profissionais
- **Armazenamento de mídia** (fotos e vídeos) para documentação visual
- **Sistema RAG** para consultas contextuais sobre histórico de alunos

### 1.3 Arquitetura de Alto Nível

**[SUGESTÃO DE IMAGEM 1: Diagrama de Contexto]**
*Descrição:* Diagrama C4 Level 1 mostrando o sistema central "Agente IA TEA" no centro, com as seguintes entidades externas conectadas por setas:
- Educadores (seta bidirecional: "Registra diários, visualiza relatórios")
- Terapeutas (seta bidirecional: "Cria planos terapêuticos, consulta histórico")
- Familiares (seta entrada: "Visualiza progressos")
- Google Gemini API (seta saída: "Geração de texto e embeddings")
- PostgreSQL + pgvector (seta bidirecional: "Persistência de dados e vetores")
- MailerSend (seta saída: "Envio de emails")
- Supabase Storage (seta bidirecional: "Upload/download de arquivos")

---

## 2. Arquitetura do Sistema

### 2.1 Estilo Arquitetural

O sistema adota **Clean Architecture** combinada com **Domain-Driven Design (DDD)**, organizando o código em camadas bem definidas com dependências unidirecionais.

**[SUGESTÃO DE IMAGEM 2: Diagrama de Camadas Clean Architecture]**
*Descrição:* Diagrama concêntrico (círculos) mostrando de fora para dentro:
- Camada externa (azul): "Infrastructure Layer" - PostgreSQL, Supabase, MailerSend, Gemini API
- Segunda camada (verde): "Interface Adapters" - FastAPI Routers (17 routers), Repositories (23+), DTOs Pydantic
- Terceira camada (laranja): "Application Layer" - Use Cases (88 casos), Services (JWT, LLM)
- Camada central (amarelo): "Domain Layer" - Entities, Business Rules, Result<T,E>
- Setas apontando de fora para dentro indicando "dependências"

### 2.2 Padrões Arquiteturais Implementados

#### 2.2.1 Clean Architecture (Layered)
```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                         │
│                   (FastAPI Routers)                          │
│  - auth_routes, diary_routes, pei_routes, etc.             │
├─────────────────────────────────────────────────────────────┤
│                   Application Layer                          │
│                  (Use Cases + Services)                      │
│  - 88 Use Cases (CreateDiary, GeneratePEI, etc.)           │
│  - JWTService, LLMService                                   │
├─────────────────────────────────────────────────────────────┤
│                    Domain Layer                              │
│               (Pydantic Schemas + Result Type)              │
│  - DTOs de Request/Response                                 │
│  - Result<T,E> para tratamento funcional de erros          │
├─────────────────────────────────────────────────────────────┤
│                 Infrastructure Layer                         │
│        (Repositories + Models + External Services)          │
│  - 23+ Repositories (Data Access)                           │
│  - 30+ SQLAlchemy Models                                    │
│  - EmailService, StorageService                             │
├─────────────────────────────────────────────────────────────┤
│                      Data Layer                              │
│             PostgreSQL + pgvector Extension                  │
└─────────────────────────────────────────────────────────────┘
```

#### 2.2.2 Dependency Injection Container

Implementado com a biblioteca **dependency-injector**:

```python
# core/kernel/container.py
class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["api.auth_routes", "api.diary_routes", ...]
    )

    # Database
    db = providers.Singleton(SessionLocal)

    # Repositories
    user_repository = providers.Factory(UserRepository, db)
    diary_repository = providers.Factory(DiaryRepository, db)

    # Use Cases
    create_diary_use_case = providers.Factory(
        CreateDiaryUseCase,
        diary_repository=diary_repository
    )
```

**Benefícios:**
- Inversão de controle automática
- Facilita testes unitários (mocking)
- Reduz acoplamento entre módulos

#### 2.2.3 Repository Pattern

Abstração da camada de acesso a dados:

```python
class DiaryRepository:
    async def create(self, diary: Diary) -> Diary
    async def get_by_id(self, diary_id: int) -> Optional[Diary]
    async def get_by_beneficiary(self, beneficiary_id: int) -> List[Diary]
    async def update(self, diary: Diary) -> Diary
    async def delete(self, diary_id: int) -> bool
```

#### 2.2.4 Use Case Pattern (Single Responsibility)

Cada caso de uso encapsula uma ação de negócio:

```python
class CreateDiaryUseCase:
    def __init__(self, diary_repository: DiaryRepository):
        self._repository = diary_repository

    async def execute(self, request: CreateDiaryRequest) -> Result[Diary, str]:
        # 1. Validação
        # 2. Lógica de negócio
        # 3. Persistência via repository
        # 4. Retorno do Result
```

#### 2.2.5 Result Type (Functional Error Handling)

Inspirado em Rust, evita exceções para controle de fluxo:

```python
# Sucesso
Result.ok(diary)

# Erros tipados
Result.bad_request("Invalid date format")
Result.not_found("Beneficiary not found")
Result.unauthorized("Invalid token")
Result.error("Database connection failed")
```

**[SUGESTÃO DE IMAGEM 3: Diagrama de Sequência - Criação de Diário]**
*Descrição:* Diagrama UML de sequência mostrando:
- Atores: Usuario, FastAPI Router, CreateDiaryUseCase, DiaryRepository, PostgreSQL
- Fluxo:
  1. Usuario -> Router: POST /diary/create (JSON)
  2. Router -> CreateDiaryUseCase: execute(request)
  3. CreateDiaryUseCase -> DiaryRepository: create(diary)
  4. DiaryRepository -> PostgreSQL: INSERT INTO diary
  5. PostgreSQL -> DiaryRepository: diary_id
  6. DiaryRepository -> CreateDiaryUseCase: Result.ok(diary)
  7. CreateDiaryUseCase -> Router: Result.ok(diary)
  8. Router -> Usuario: 201 Created (JSON)

---

## 3. Stack Tecnológico

### 3.1 Backend Framework

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **FastAPI** | 0.116.1 | Framework web assíncrono de alta performance |
| **Uvicorn** | 0.35.0 | Servidor ASGI para desenvolvimento |
| **Gunicorn** | 23.0.0 | Servidor WSGI para produção |
| **Python** | 3.11+ | Linguagem base |

**Justificativa FastAPI:**
- Performance superior (comparável a Node.js e Go)
- Documentação automática (OpenAPI/Swagger)
- Type hints nativos com validação Pydantic
- Suporte async/await nativo

### 3.2 Banco de Dados

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **PostgreSQL** | 15+ | Banco de dados relacional principal |
| **pgvector** | 0.4.1 | Extensão para armazenar embeddings (vetores 768D) |
| **SQLAlchemy** | 2.0.42 | ORM assíncrono |
| **asyncpg** | 0.30.0 | Driver PostgreSQL assíncrono |
| **Alembic** | 1.16.4 | Sistema de migrações |

**Justificativa pgvector:**
- Permite busca semântica diretamente no banco
- Suporta operações de similaridade (cosine, L2, inner product)
- Performance superior a soluções externas para datasets médios

### 3.3 Inteligência Artificial

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **Google Gemini API** | 1.5 Pro/Flash | LLM principal para geração de texto |
| **langchain-google-genai** | 2.1.12 | Integração com Gemini |
| **langchain-text-splitters** | 0.3.9 | Chunking de textos para RAG |
| **numpy** | 2.2.0 | Operações com vetores |

**Modelos utilizados:**
- **Gemini 1.5 Pro** - Geração de PEI, análises complexas
- **Gemini 1.5 Flash** - Embeddings rápidos, consultas simples
- **models/embedding-001** - Geração de embeddings (768 dimensões)

### 3.4 Autenticação e Segurança

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **PyJWT** | 2.10.1 | Geração e validação de tokens JWT |
| **passlib[bcrypt]** | 1.7.4 | Hashing de senhas com bcrypt |
| **email-validator** | 2.3.0 | Validação de formato de email |

**Características de Segurança:**
- Senhas hasheadas com bcrypt (salt automático)
- JWT com algoritmo HS256
- Tokens com expiração diferenciada:
  - Access token: 60 minutos
  - Refresh token: 7 dias
  - Verification token: 24 horas
  - Reset password token: 1 hora

### 3.5 Serviços Externos

| Serviço | Tecnologia | Propósito |
|---------|------------|-----------|
| **Email** | MailerSend 2.0.0 | Envio de emails transacionais |
| **Storage** | Supabase 2.23.2 | Armazenamento de arquivos (fotos/vídeos) |
| **PDF Generation** | ReportLab 4.2.5 | Geração de relatórios PDF |

### 3.6 Validação e Configuração

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **Pydantic** | 2.11.7 | Validação de dados e serialização |
| **python-dotenv** | 1.1.1 | Gerenciamento de variáveis de ambiente |
| **dependency-injector** | 4.48.1 | Container de injeção de dependências |

**[SUGESTÃO DE IMAGEM 4: Diagrama de Componentes - Stack Tecnológico]**
*Descrição:* Diagrama mostrando componentes principais em blocos retangulares agrupados:
- Grupo "Presentation": FastAPI, Uvicorn/Gunicorn
- Grupo "Business Logic": Use Cases (88), Services (JWT, LLM, Email)
- Grupo "Data Access": SQLAlchemy, asyncpg, Repositories (23+)
- Grupo "External Services": Gemini API, MailerSend, Supabase
- Grupo "Database": PostgreSQL + pgvector
- Setas conectando os componentes

---

## 4. Estrutura de Camadas

### 4.1 Presentation Layer (API)

**Localização:** `api/`

Responsável por expor endpoints HTTP e receber requisições.

#### Routers Implementados (17)

| Router | Endpoint Base | Responsabilidade |
|--------|---------------|------------------|
| `auth_routes.py` | `/auth` | Login, registro, verificação de email |
| `diary_routes.py` | `/diary` | CRUD de diários, análise de comportamento |
| `beneficiary_routes.py` | `/beneficiary` | CRUD de beneficiários (alunos) |
| `pei_routes.py` | `/pei` | Geração e gerenciamento de PEI |
| `case_study_routes.py` | `/case-study` | Estudos de caso com IA |
| `institution_routes.py` | `/institution` | Análise de instituições escolares |
| `therapeutic_plan_routes.py` | `/therapeutic-plan` | Planos terapêuticos |
| `school_routes.py` | `/school` | CRUD de escolas |
| `clinic_routes.py` | `/clinic` | CRUD de clínicas |
| `professional_routes.py` | `/professional` | CRUD de profissionais |
| `supervisor_routes.py` | `/supervisor` | Supervisores de caso |
| `storage_routes.py` | `/storage` | Upload/download de arquivos |

**Exemplo de Endpoint:**

```python
# api/diary_routes.py
@router.post("/create", response_model=DiaryResponse)
async def create_diary(
    request: CreateDiaryRequest,
    use_case: CreateDiaryUseCase = Depends(Provide[Container.create_diary_use_case])
):
    result = await use_case.execute(request)
    if result.is_ok:
        return result.value
    raise HTTPException(status_code=400, detail=result.error)
```

### 4.2 Application Layer (Use Cases)

**Localização:** `core/use_case/`

Contém a lógica de negócio pura, independente de frameworks.

#### Estatísticas
- **88 Use Cases implementados**
- Média de 50-200 linhas por caso de uso
- Todos retornam `Result<T, E>`

#### Categorias de Use Cases

**Autenticação (6):**
- `CreateUserUseCase` - Registro com email verification
- `LoginUserUseCase` - Autenticação com JWT
- `VerifyEmailUseCase` - Confirmação de email
- `ForgotPasswordUseCase` - Solicitação de reset
- `ResetPasswordUseCase` - Alteração de senha
- `RefreshTokenUseCase` - Renovação de tokens

**Diários (10+):**
- `CreateDiaryUseCase` - Criação de registro diário
- `GetDiaryByIdUseCase`, `ListDiaryUseCase`, `UpdateDiaryUseCase`, `DeleteDiaryUseCase`
- `GetDiaryByBeneficiaryUseCase` - Histórico de um aluno
- `GenerateDiaryEmbeddingUseCase` - Gera embeddings
- `QueryDiaryRAGUseCase` - Busca semântica
- `AnalyzeBehaviorPatternsUseCase` - Análise com IA

**PEI (5):**
- `GeneratePEIUseCase` - Gera plano educacional com IA
- `GeneratePEIPDFUseCase` - Converte para PDF
- `ListPEIUseCase`, `GetPEIByIdUseCase`, `UpdatePEIUseCase`

**Estudos de Caso (3):**
- `StudyCaseUseCase` - Gera análise com IA
- `CreateStudyCaseEmbeddingUseCase` - Embeddings
- `QueryStudyCaseRAGUseCase` - Busca semântica

**Beneficiários (5):**
- `CreateBeneficiaryUseCase`, `GetBeneficiaryByIdUseCase`, `ListBeneficiaryUseCase`, `UpdateBeneficiaryUseCase`, `DeleteBeneficiaryUseCase`

**Outros (59+):**
- Terapias, clínicas, profissionais, escolas, feedbacks, etc.

### 4.3 Domain Layer (Schemas)

**Localização:** `domain/schema.py`

Define contratos de dados usando Pydantic.

**Exemplo de Schema:**

```python
class CreateDiaryRequest(BaseModel):
    beneficiary_id: int
    diary_date: date
    behavior_description: Optional[str] = None
    behavior_rating: Optional[int] = Field(None, ge=1, le=5)
    activity_performance: Optional[str] = None
    socialization: Optional[str] = None
    crisis_occurred: Optional[bool] = False
    crisis_description: Optional[str] = None
    emotional_state: Optional[str] = None
    photos: Optional[List[str]] = None
    videos: Optional[List[str]] = None

class DiaryResponse(BaseModel):
    id: int
    beneficiary_id: int
    diary_date: date
    created_at: datetime

    class Config:
        from_attributes = True
```

**Características:**
- Validação automática de tipos
- Conversão de ORM para JSON automática
- Documentação OpenAPI gerada automaticamente

### 4.4 Infrastructure Layer

**Localização:** `infrastructure/`

#### 4.4.1 Models (SQLAlchemy)

**Localização:** `infrastructure/models/`

**Modelos principais:**

```python
# users.py
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    email_verified: Mapped[bool] = mapped_column(default=False)
    verification_token: Mapped[Optional[str]]
    reset_token: Mapped[Optional[str]]
    reset_token_expires: Mapped[Optional[datetime]]

# diary.py
class Diary(Base):
    __tablename__ = "diary"
    id: Mapped[int] = mapped_column(primary_key=True)
    beneficiary_id: Mapped[int] = mapped_column(ForeignKey("beneficiary.id"))
    diary_date: Mapped[date]
    behavior_description: Mapped[Optional[str]]
    behavior_rating: Mapped[Optional[int]]
    crisis_occurred: Mapped[bool] = mapped_column(default=False)
    photos: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    videos: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))

# diary_embedding_gemini.py
class DiaryEmbeddingGemini(Base):
    __tablename__ = "diary_embedding_gemini"
    id: Mapped[int] = mapped_column(primary_key=True)
    diary_id: Mapped[int] = mapped_column(ForeignKey("diary.id"))
    beneficiary_id: Mapped[int] = mapped_column(ForeignKey("beneficiary.id"))
    content: Mapped[str]
    embedding = mapped_column(Vector(768))  # pgvector
```

#### 4.4.2 Repositories

**Localização:** `infrastructure/repositories/`

**Exemplo - DiaryEmbeddingGeminiRepository:**

```python
class DiaryEmbeddingGeminiRepository:
    async def create(self, embedding: DiaryEmbeddingGemini):
        # INSERT com vetor

    async def search_similar(
        self,
        query_embedding: List[float],
        beneficiary_id: int,
        limit: int = 5
    ) -> List[DiaryEmbeddingGemini]:
        # SELECT usando cosine distance
        # ORDER BY embedding <=> query_embedding
        # WHERE beneficiary_id = ?
        # LIMIT ?
```

#### 4.4.3 Services

**Localização:** `infrastructure/services/` e `core/services/`

**EmailService:**
```python
class EmailService:
    async def send_verification_email(self, to: str, token: str)
    async def send_password_reset_email(self, to: str, token: str)
```

**LLMService:**
```python
class LLMService:
    def configure(self, provider: str):  # "gemini", "openai", "groq"

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: str = None
    ) -> str:
        # Chama Gemini API

    async def generate_embeddings(self, text: str) -> List[float]:
        # Retorna vetor 768D

    def split_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        # Text splitting para RAG
```

**JWTService:**
```python
class JWTService:
    def create_access_token(self, user_id: int) -> str:
        # Expira em 60 minutos

    def create_refresh_token(self, user_id: int) -> str:
        # Expira em 7 dias

    def decode_token(self, token: str) -> Dict:
        # Valida e decodifica JWT

    def hash_password(self, password: str) -> str:
        # bcrypt hash

    def verify_password(self, plain: str, hashed: str) -> bool:
        # Verifica hash
```

**[SUGESTÃO DE IMAGEM 5: Diagrama de Classes - Principais Entidades]**
*Descrição:* Diagrama UML de classes mostrando:
- Classe User (id, name, email, password_hash, email_verified)
- Classe Beneficiary (id, name, date_of_birth, diagnosis)
- Classe Diary (id, beneficiary_id, diary_date, behavior_rating, crisis_occurred)
- Classe DiaryEmbeddingGemini (id, diary_id, beneficiary_id, content, embedding: Vector768)
- Classe PEI (id, beneficiary_id, pei_data: JSON)
- Setas de relacionamento: User 1-N Beneficiary, Beneficiary 1-N Diary, Diary 1-1 DiaryEmbeddingGemini, Beneficiary 1-N PEI

---

## 5. Modelo de Dados

### 5.1 Diagrama Entidade-Relacionamento

**[SUGESTÃO DE IMAGEM 6: Diagrama ER - Banco de Dados Completo]**
*Descrição:* Diagrama ERD mostrando todas as tabelas com relacionamentos:

**Grupo "Autenticação":**
- users (PK: id, UK: email)

**Grupo "Beneficiários e Escolas":**
- beneficiary (PK: id, FK: school_id, health_plan_id)
- school (PK: id)
- health_plan (PK: id)

**Grupo "Acompanhamento":**
- diary (PK: id, FK: beneficiary_id)
- diary_embedding_gemini (PK: id, FK: diary_id, beneficiary_id, campo especial: embedding VECTOR(768))

**Grupo "Terapia":**
- clinic (PK: id)
- professional (PK: id, FK: clinic_id)
- beneficiary_clinic (PK: id, FK: beneficiary_id, clinic_id)
- therapeutic_plan (PK: id, FK: beneficiary_id)
- therapeutic_sessions (PK: id, FK: therapeutic_plan_id)

**Grupo "IA/RAG":**
- pei (PK: id, FK: beneficiary_id, campo: pei_data JSONB)
- pei_embedding_gemini (PK: id, FK: beneficiary_id, campo: embedding VECTOR(768))
- study_case_embedding_gemini (PK: id, FK: beneficiary_id, campo: embedding VECTOR(768))
- institution_embedding_gemini (PK: id, FK: beneficiary_id, campo: embedding VECTOR(768))

**Grupo "Feedback":**
- school_feedback (PK: id, FK: beneficiary_id)
- family_reunion (PK: id, FK: beneficiary_id)
- supervisor (PK: id, FK: beneficiary_id)

Relacionamentos indicados com setas:
- 1:N entre beneficiary e diary
- 1:1 entre diary e diary_embedding_gemini
- 1:N entre beneficiary e pei
- etc.

### 5.2 Tabelas Principais

#### 5.2.1 Tabela: users

| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | INTEGER | PRIMARY KEY | Identificador único |
| name | VARCHAR | NOT NULL | Nome completo |
| email | VARCHAR | UNIQUE, NOT NULL | Email (login) |
| password_hash | VARCHAR | NOT NULL | Senha hasheada (bcrypt) |
| email_verified | BOOLEAN | DEFAULT FALSE | Email confirmado? |
| verification_token | VARCHAR | NULL | Token de verificação |
| reset_token | VARCHAR | NULL | Token de reset de senha |
| reset_token_expires | TIMESTAMP | NULL | Expiração do reset token |
| created_at | TIMESTAMP | DEFAULT NOW() | Data de criação |

#### 5.2.2 Tabela: beneficiary

| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | INTEGER | PRIMARY KEY | Identificador único |
| name | VARCHAR | NOT NULL | Nome do aluno |
| date_of_birth | DATE | NOT NULL | Data de nascimento |
| diagnosis | TEXT | NULL | Diagnóstico de TEA |
| school_id | INTEGER | FOREIGN KEY | Escola vinculada |
| healthplan_id | INTEGER | FOREIGN KEY | Plano de saúde |
| entry_date | DATE | NULL | Data de entrada no programa |
| exit_date | DATE | NULL | Data de saída |

#### 5.2.3 Tabela: diary

| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | INTEGER | PRIMARY KEY | Identificador único |
| beneficiary_id | INTEGER | FOREIGN KEY | Aluno relacionado |
| diary_date | DATE | NOT NULL | Data do registro |
| behavior_description | TEXT | NULL | Descrição do comportamento |
| behavior_rating | INTEGER | CHECK (1-5) | Avaliação 1 a 5 |
| activity_performance | TEXT | NULL | Desempenho em atividades |
| socialization | TEXT | NULL | Interação social |
| crisis_occurred | BOOLEAN | DEFAULT FALSE | Houve crise? |
| crisis_description | TEXT | NULL | Descrição da crise |
| crisis_trigger | TEXT | NULL | Gatilho da crise |
| crisis_duration | INTEGER | NULL | Duração (minutos) |
| emotional_state | TEXT | NULL | Estado emocional |
| communication_verbal | TEXT | NULL | Comunicação verbal |
| communication_nonverbal | TEXT | NULL | Comunicação não-verbal |
| autonomy | TEXT | NULL | Autonomia e autocuidado |
| observations | TEXT | NULL | Observações gerais |
| suggestions | TEXT | NULL | Sugestões para próximos passos |
| photos | TEXT[] | NULL | URLs de fotos (array) |
| videos | TEXT[] | NULL | URLs de vídeos (array) |
| created_at | TIMESTAMP | DEFAULT NOW() | Data de criação |

#### 5.2.4 Tabela: diary_embedding_gemini

| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | INTEGER | PRIMARY KEY | Identificador único |
| diary_id | INTEGER | FOREIGN KEY | Diário relacionado |
| beneficiary_id | INTEGER | FOREIGN KEY | Aluno relacionado |
| content | TEXT | NOT NULL | Texto concatenado do diário |
| **embedding** | **VECTOR(768)** | NOT NULL | **Vetor de embedding (Gemini)** |
| created_at | TIMESTAMP | DEFAULT NOW() | Data de criação |

**Índices:**
```sql
CREATE INDEX idx_diary_embedding_cosine
ON diary_embedding_gemini
USING ivfflat (embedding vector_cosine_ops);
```

#### 5.2.5 Tabela: pei

| Coluna | Tipo | Restrições | Descrição |
|--------|------|------------|-----------|
| id | INTEGER | PRIMARY KEY | Identificador único |
| beneficiary_id | INTEGER | FOREIGN KEY | Aluno relacionado |
| **pei_data** | **JSONB** | NOT NULL | **Dados estruturados do PEI** |
| meta_data | JSONB | NULL | Metadados adicionais |
| created_at | TIMESTAMP | DEFAULT NOW() | Data de geração |
| updated_at | TIMESTAMP | NULL | Última atualização |

**Exemplo de pei_data (JSON):**
```json
{
  "student_profile": {
    "name": "João Silva",
    "age": 8,
    "diagnosis": "TEA Nível 1"
  },
  "goals": [
    {
      "area": "Comunicação",
      "objective": "Aumentar uso de frases completas",
      "strategies": ["Modelagem", "Reforço positivo"]
    }
  ],
  "accommodations": [
    "Tempo estendido para atividades",
    "Ambiente silencioso para provas"
  ],
  "support_services": ["Fonoaudiologia", "Terapia Ocupacional"]
}
```

### 5.3 Sistema de Migrações (Alembic)

**Localização:** `alembic/versions/`

#### Histórico de Migrações

| Revisão | Descrição | Data |
|---------|-----------|------|
| d0ba2680b262 | Criação de tabelas base | 2025-01 |
| eb466dbf3dbc | diary_embedding_groq (deprecated) | 2025-02 |
| 68572a580ac4 | Tabela diary completa | 2025-03 |
| 45e4ef002e66 | diary_embedding_gemini | 2025-04 |
| 729ce661dd04 | Campos de mídia (photos, videos) | 2025-05 |
| 6c33f8933ebd | Ajuste vetor para 768D | 2025-06 |
| 2542021886dd | FKs em embeddings | 2025-07 |
| b5534522224d | study_case_embedding_gemini | 2025-08 |
| fa4ed68a894e | institution_embedding_gemini | 2025-09 |
| a1b2c3d4e5f6 | pei + pei_embedding_gemini | 2025-10 |
| 94fe8070fe14 | Email verification e password reset | 2025-11 |

**Comandos Alembic:**
```bash
# Criar nova migração
alembic revision --autogenerate -m "Descrição"

# Aplicar migrações
alembic upgrade head

# Reverter uma migração
alembic downgrade -1

# Ver histórico
alembic history
```

---

## 6. Serviços e Funcionalidades

### 6.1 Autenticação e Gerenciamento de Usuários

#### 6.1.1 Fluxo de Registro

**[SUGESTÃO DE IMAGEM 7: Diagrama de Sequência - Registro de Usuário]**
*Descrição:* Diagrama mostrando:
1. Usuario -> API: POST /auth/register (name, email, password)
2. API -> CreateUserUseCase: execute()
3. CreateUserUseCase -> UserRepository: check_email_exists()
4. UserRepository -> CreateUserUseCase: false
5. CreateUserUseCase -> JWTService: hash_password()
6. CreateUserUseCase -> UserRepository: create(user)
7. CreateUserUseCase -> JWTService: create_verification_token()
8. CreateUserUseCase -> EmailService: send_verification_email()
9. EmailService -> MailerSend: API request
10. CreateUserUseCase -> API: Result.ok(user)
11. API -> Usuario: 201 Created

#### 6.1.2 Fluxo de Login

1. Usuario envia email + senha
2. `LoginUserUseCase` busca usuário por email
3. Valida senha com bcrypt
4. Verifica se email está confirmado
5. Gera access_token (60min) + refresh_token (7d)
6. Retorna tokens

#### 6.1.3 Fluxo de Verificação de Email

1. Usuario clica no link do email (contém token)
2. Frontend chama `POST /auth/verify-email?token=...`
3. `VerifyEmailUseCase` valida token
4. Marca `email_verified = true`
5. Remove token de verificação

#### 6.1.4 Fluxo de Recuperação de Senha

**[SUGESTÃO DE IMAGEM 8: Diagrama de Fluxo - Password Reset]**
*Descrição:* Flowchart mostrando:
- Início: Usuario clica "Esqueci senha"
- Passo 1: POST /auth/forgot-password (email)
- Decision: Email existe? (sim -> continua, não -> erro 404)
- Passo 2: Gera reset_token (UUID) com expiração 1h
- Passo 3: Envia email com link
- Passo 4: Usuario clica link (frontend)
- Passo 5: POST /auth/reset-password (token, new_password)
- Decision: Token válido e não expirado? (sim -> continua, não -> erro 400)
- Passo 6: Hash nova senha
- Passo 7: Atualiza password_hash, limpa reset_token
- Fim: Senha redefinida

### 6.2 Sistema de Diários (Core Feature)

#### 6.2.1 Estrutura de um Diário

Um registro de diário captura múltiplas dimensões do desenvolvimento:

**Comportamento:**
- Descrição qualitativa
- Rating quantitativo (1-5)

**Desempenho:**
- Atividades realizadas
- Nível de engajamento

**Socialização:**
- Interação com pares
- Interação com adultos

**Crises:**
- Ocorrência (sim/não)
- Descrição detalhada
- Gatilhos identificados
- Duração (minutos)

**Emoções:**
- Estado emocional
- Mood rating

**Comunicação:**
- Verbal (fala, vocabulário usado)
- Não-verbal (gestos, expressões faciais)

**Autonomia:**
- Autocuidado
- Independência em tarefas

**Mídia:**
- Fotos (array de URLs)
- Vídeos (array de URLs)

#### 6.2.2 Fluxo de Criação com Embedding

**[SUGESTÃO DE IMAGEM 9: Diagrama de Atividades - Criação de Diário + Embedding]**
*Descrição:* Diagrama de atividades mostrando fluxo paralelo:

**Swim Lane 1 - Usuario/API:**
1. Usuario preenche formulário de diário
2. POST /diary/create

**Swim Lane 2 - CreateDiaryUseCase:**
3. Valida beneficiary_id
4. Verifica duplicação de data
5. Salva no banco (INSERT)
6. Retorna diary_id

**Swim Lane 3 - GenerateDiaryEmbeddingUseCase (async):**
7. Concatena todos os campos textuais
8. Chama LLMService.generate_embeddings()
9. LLMService -> Gemini API (retorna vetor 768D)
10. Salva em diary_embedding_gemini com:
    - diary_id
    - beneficiary_id
    - content (texto)
    - embedding (vetor)

### 6.3 Sistema RAG (Retrieval-Augmented Generation)

#### 6.3.1 O que é RAG?

**RAG** combina busca semântica (retrieval) com geração de texto (generation):

1. **Indexação:** Textos são convertidos em vetores (embeddings)
2. **Busca:** Query do usuário vira vetor e busca os mais similares
3. **Contexto:** Resultados relevantes são injetados no prompt da IA
4. **Geração:** LLM gera resposta baseada no contexto recuperado

#### 6.3.2 Implementação no Sistema

**Tipos de Embeddings:**

| Tabela | Conteúdo Indexado | Dimensão | Uso |
|--------|-------------------|----------|-----|
| `diary_embedding_gemini` | Diários completos | 768D | Análise de padrões, geração de PEI |
| `pei_embedding_gemini` | PEIs anteriores | 768D | Recomendações baseadas em casos similares |
| `study_case_embedding_gemini` | Estudos de caso | 768D | Contextualizar histórico do aluno |
| `institution_embedding_gemini` | Análises de escolas | 768D | Avaliar adequação da instituição |

**Busca Semântica (Cosine Similarity):**

```sql
-- Exemplo de query de similaridade
SELECT
    id,
    content,
    1 - (embedding <=> query_embedding) AS similarity
FROM diary_embedding_gemini
WHERE beneficiary_id = ?
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

**Operadores pgvector:**
- `<=>` : Cosine distance (usado no ORDER BY)
- `<->` : L2 distance (Euclidean)
- `<#>` : Inner product

#### 6.3.3 Use Case: QueryDiaryRAGUseCase

**Entrada:**
```json
{
  "beneficiary_id": 123,
  "query": "Como João reagiu a mudanças na rotina?"
}
```

**Fluxo:**
1. Gera embedding da query (768D)
2. Busca top 5 diários mais similares via pgvector
3. Concatena os diários encontrados
4. Monta prompt para Gemini:
```
Contexto (diários relevantes):
[Diário 1: ...]
[Diário 2: ...]

Pergunta: Como João reagiu a mudanças na rotina?

Responda baseando-se apenas no contexto fornecido.
```
5. Retorna resposta do Gemini

**[SUGESTÃO DE IMAGEM 10: Diagrama de Fluxo - Sistema RAG]**
*Descrição:* Diagrama ilustrando pipeline RAG:
- Bloco 1: "Usuario envia pergunta" -> seta para
- Bloco 2: "Query vira embedding (Gemini API)" -> seta para
- Bloco 3: "Busca vetores similares (pgvector)" -> retorna documentos
- Bloco 4: "Top 5 diários recuperados" -> seta para
- Bloco 5: "Prompt + contexto enviado para Gemini" -> seta para
- Bloco 6: "Resposta contextualizada retorna ao usuário"

### 6.4 Geração de PEI (Plano Educacional Individualizado)

#### 6.4.1 O que é PEI?

O **Plano Educacional Individualizado** é um documento legal (em muitos países) que define:
- Objetivos educacionais personalizados
- Estratégias pedagógicas adaptadas
- Acomodações necessárias
- Serviços de suporte
- Métricas de avaliação

#### 6.4.2 Fluxo de Geração Automatizada

**[SUGESTÃO DE IMAGEM 11: Diagrama de Sequência - Geração de PEI]**
*Descrição:* Diagrama detalhado mostrando:

1. **Usuario -> API:** POST /pei/generate (beneficiary_id)

2. **API -> GeneratePEIUseCase:** execute()

3. **GeneratePEIUseCase -> Repositories (paralelo):**
   - BeneficiaryRepository: get_by_id()
   - DiaryRepository: get_last_30_days()
   - DiaryEmbeddingRepository: search_similar()
   - StudyCaseEmbeddingRepository: search_similar()
   - InstitutionEmbeddingRepository: search_similar()

4. **GeneratePEIUseCase -> LLMService:**
   - configure("gemini")
   - generate_completion(prompt)

5. **Prompt estruturado:**
```
Você é um especialista em educação inclusiva para TEA.

INFORMAÇÕES DO ALUNO:
Nome: João Silva
Idade: 8 anos
Diagnóstico: TEA Nível 1

HISTÓRICO RECENTE (últimos 30 dias):
[Resumo de diários...]

CASOS SIMILARES:
[PEIs de outros alunos com perfil similar...]

CONTEXTO DA INSTITUIÇÃO:
[Capacidades e recursos da escola...]

Gere um PEI estruturado em JSON com:
{
  "student_profile": {...},
  "strengths": [...],
  "challenges": [...],
  "annual_goals": [...],
  "accommodations": [...],
  "support_services": [...],
  "assessment_methods": [...]
}
```

6. **LLMService -> Gemini API:** Request

7. **Gemini API -> LLMService:** JSON Response

8. **GeneratePEIUseCase:**
   - Parseia JSON
   - Salva em tabela `pei`
   - Gera embedding do PEI completo
   - Salva em `pei_embedding_gemini`

9. **API -> Usuario:** 201 Created (pei_id)

#### 6.4.3 Geração de PDF

`GeneratePEIPDFUseCase` converte o JSON do PEI em documento formatado usando ReportLab:

- Cabeçalho com dados do aluno
- Seções bem formatadas
- Tabelas para objetivos
- Lista de acomodações
- Assinaturas (espaço)

### 6.5 Análise de Padrões Comportamentais

#### 6.5.1 Use Case: AnalyzeBehaviorPatternsUseCase

**Objetivo:** Identificar tendências, gatilhos e progressos.

**Fluxo:**
1. Busca últimos N diários do beneficiário (padrão: 30 dias)
2. Extrai métricas quantitativas:
   - Taxa de crises (crises/dia)
   - Mood médio
   - Comportamento médio (rating)
   - Tendências de comunicação
3. Identifica padrões com IA:
```
Analise os seguintes registros e identifique:
- Padrões de comportamento
- Gatilhos recorrentes de crises
- Progressos observados
- Áreas que requerem atenção

[Diários...]
```
4. Retorna relatório textual

**Saída Exemplo:**
```
ANÁLISE DE PADRÕES - João Silva (últimos 30 dias)

MÉTRICAS:
- Taxa de crises: 2/30 dias (6.6%)
- Comportamento médio: 4.2/5
- Mood predominante: Calmo

PADRÕES IDENTIFICADOS:
1. Crises ocorrem principalmente em segundas-feiras
2. Gatilho recorrente: Mudança de rotina
3. Boa resposta a atividades estruturadas

PROGRESSOS:
- Aumento de frases completas (3 para 7 por dia)
- Melhora na interação com pares

RECOMENDAÇÕES:
- Preparar transições de fim de semana com antecedência
- Continuar atividades estruturadas
```

### 6.6 Gestão de Mídia (Storage)

#### 6.6.1 Upload de Arquivos

**Endpoint:** `POST /storage/upload`

**Fluxo:**
1. Usuario envia arquivo via multipart/form-data
2. `StorageService` valida tipo (foto ou vídeo)
3. Upload para Supabase Storage (bucket: `uploads/`)
4. Retorna URL pública
5. URL é salva no campo `photos[]` ou `videos[]` do diário

**Formatos suportados:**
- Fotos: JPG, PNG, WEBP
- Vídeos: MP4, MOV, AVI

#### 6.6.2 Download de Arquivos

**Endpoint:** `GET /storage/download/{file_path}`

Retorna arquivo via streaming do Supabase.

---

## 7. Sistema RAG (Retrieval-Augmented Generation)

### 7.1 Arquitetura do RAG

**[SUGESTÃO DE IMAGEM 12: Arquitetura RAG - Visão Detalhada]**
*Descrição:* Diagrama de componentes mostrando:

**Camada 1 - Ingestão:**
- Input: Diários, Estudos de Caso, PEIs
- Componente: LLMService.split_text() (chunking)
- Componente: LLMService.generate_embeddings() (Gemini)
- Output: Vetores 768D

**Camada 2 - Armazenamento:**
- PostgreSQL + pgvector
- Tabelas: diary_embedding_gemini, pei_embedding_gemini, etc.
- Índices: ivfflat para busca rápida

**Camada 3 - Retrieval:**
- Input: Query do usuário
- Componente: Query -> Embedding
- Componente: Cosine Similarity Search (SQL)
- Output: Top K documentos relevantes

**Camada 4 - Generation:**
- Input: Contexto recuperado + Query original
- Componente: Prompt Engineering
- Componente: Gemini API (generate_completion)
- Output: Resposta contextualizada

### 7.2 Estratégias de Chunking

Textos longos são divididos antes de gerar embeddings:

```python
# LLMService.split_text()
def split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return text_splitter.split_text(text)
```

**Parâmetros:**
- `chunk_size=1000`: Máximo de caracteres por chunk
- `overlap=200`: Sobreposição para manter contexto

### 7.3 Índices Vetoriais

Para performance em buscas, pgvector usa índices especializados:

```sql
CREATE INDEX idx_diary_embedding_cosine
ON diary_embedding_gemini
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Tipos de índice:**
- **ivfflat:** Inverted File Flat (rápido, bom para até 1M vetores)
- **hnsw:** Hierarchical Navigable Small World (mais preciso, para >1M)

**Trade-off:**
- ivfflat: Busca aproximada (recall ~90%), muito rápida
- hnsw: Busca mais precisa (recall ~99%), moderadamente rápida

### 7.4 Exemplo Completo de RAG Query

**Request:**
```json
POST /diary/query-rag
{
  "beneficiary_id": 42,
  "query": "Quais atividades João mais gostou no último mês?"
}
```

**SQL Executado (simplificado):**
```sql
-- Gera embedding da query
embedding_query = gemini.embed("Quais atividades João mais gostou...")

-- Busca vetores similares
SELECT
    d.id,
    d.content,
    d.created_at,
    1 - (d.embedding <=> embedding_query) AS similarity
FROM diary_embedding_gemini d
WHERE d.beneficiary_id = 42
ORDER BY d.embedding <=> embedding_query
LIMIT 5;
```

**Prompt para Gemini:**
```
Contexto (diários relevantes de João):

[Diário 1 - 2026-01-15]
João participou de atividade de pintura. Mostrou muito interesse,
permaneceu engajado por 30 minutos. Sorriu ao ver o resultado.

[Diário 2 - 2026-01-10]
Atividade de música. João dançou e bateu palmas. Interagiu com
outras crianças durante a música.

[Diário 3 - 2026-01-05]
Leitura de história. João ficou quieto, mas atento. Apontou para
figuras que gostou.

---

Pergunta: Quais atividades João mais gostou no último mês?

Responda baseando-se apenas nos diários fornecidos acima.
```

**Response:**
```json
{
  "answer": "Baseado nos registros, João demonstrou preferência por
             atividades artísticas e musicais. A pintura foi a atividade
             com maior engajamento (30 minutos contínuos), seguida pela
             música, onde ele interagiu socialmente. A leitura também foi
             bem recebida, com participação visual.",
  "sources": [
    {"diary_id": 1234, "date": "2026-01-15", "similarity": 0.92},
    {"diary_id": 1230, "date": "2026-01-10", "similarity": 0.88},
    {"diary_id": 1225, "date": "2026-01-05", "similarity": 0.85}
  ]
}
```

---

## 8. Fluxos Principais

### 8.1 Fluxo Completo: Novo Beneficiário até PEI

**[SUGESTÃO DE IMAGEM 13: Diagrama de Processo - Onboarding de Beneficiário]**
*Descrição:* BPMN ou flowchart mostrando:

**Fase 1: Cadastro**
1. Educador registra novo beneficiário (POST /beneficiary/create)
   - Dados pessoais
   - Diagnóstico
   - Escola vinculada

**Fase 2: Estudo de Caso Inicial**
2. Educador preenche formulário de estudo de caso (POST /case-study/create)
   - Perguntas customizadas
   - Contexto familiar
   - Histórico médico

**Fase 3: Análise da Instituição**
3. Sistema gera análise da escola (POST /institution/analyze)
   - Recursos disponíveis
   - Capacidade inclusiva
   - Recomendações

**Fase 4: Período de Observação (30 dias)**
4. Educador registra diários diariamente
   - 30 registros mínimos
   - Embeddings gerados automaticamente

**Fase 5: Geração do PEI**
5. Sistema consolida dados (POST /pei/generate)
   - Busca RAG em diários
   - Busca casos similares
   - Gera PEI com IA
   - Salva em JSON + embedding

**Fase 6: Revisão e Aprovação**
6. Educador revisa PEI gerado
7. Gera PDF para assinaturas (POST /pei/generate-pdf)
8. Compartilha com família e equipe

**Fase 7: Acompanhamento Contínuo**
9. Diários continuam sendo registrados
10. Análises de padrões mensais (POST /diary/analyze)
11. Revisão semestral do PEI

### 8.2 Fluxo: Detecção de Padrões Críticos

**[SUGESTÃO DE IMAGEM 14: Diagrama de Decisão - Alerta de Crises]**
*Descrição:* Flowchart mostrando lógica de alerta:

1. **Trigger:** Novo diário criado com `crisis_occurred = true`

2. **Decision:** É a 3ª crise em 7 dias?
   - Não: Continua normalmente
   - Sim: Ativa alerta

3. **Ação 1:** Sistema busca últimas 10 crises (RAG)

4. **Ação 2:** Identifica gatilhos comuns com IA

5. **Ação 3:** Gera relatório de urgência:
   - Padrão identificado
   - Recomendações imediatas
   - Sugestão de reunião com equipe

6. **Notificação:** Email para educador + supervisor

7. **Dashboard:** Marca beneficiário com flag de "atenção"

---

## 9. Segurança e Autenticação

### 9.1 Camadas de Segurança

**[SUGESTÃO DE IMAGEM 15: Diagrama de Segurança - Camadas de Proteção]**
*Descrição:* Diagrama de camadas de segurança tipo "cebola":

**Camada 1 - Rede:**
- HTTPS/TLS obrigatório
- CORS configurado (domínios permitidos)

**Camada 2 - Autenticação:**
- JWT com assinatura HS256
- Tokens com expiração
- Refresh tokens para renovação

**Camada 3 - Autorização:**
- Middleware de verificação de token
- Role-based access (futuro)

**Camada 4 - Dados:**
- Senhas hasheadas com bcrypt (salt rounds: 12)
- Tokens de reset criptografados
- Dados sensíveis em variáveis de ambiente

**Camada 5 - Banco de Dados:**
- Conexões via SSL
- Prepared statements (SQLAlchemy ORM)
- Backup automático

### 9.2 Fluxo de Autenticação JWT

```
┌─────────┐                  ┌─────────┐                  ┌──────────┐
│ Cliente │                  │   API   │                  │   JWT    │
└────┬────┘                  └────┬────┘                  └────┬─────┘
     │                            │                            │
     │  1. POST /auth/login       │                            │
     │  {email, password}         │                            │
     ├───────────────────────────>│                            │
     │                            │  2. Valida credenciais     │
     │                            │  (bcrypt verify)           │
     │                            │                            │
     │                            │  3. create_access_token()  │
     │                            ├───────────────────────────>│
     │                            │                            │
     │                            │  4. JWT assinado (HS256)   │
     │                            │<───────────────────────────┤
     │  5. 200 OK                 │                            │
     │  {access_token, refresh}   │                            │
     │<───────────────────────────┤                            │
     │                            │                            │
     │  6. GET /diary/list        │                            │
     │  Header: Authorization:    │                            │
     │          Bearer <token>    │                            │
     ├───────────────────────────>│                            │
     │                            │  7. decode_token(token)    │
     │                            ├───────────────────────────>│
     │                            │                            │
     │                            │  8. Payload válido         │
     │                            │  {user_id, exp}            │
     │                            │<───────────────────────────┤
     │                            │                            │
     │  9. 200 OK + Dados         │                            │
     │<───────────────────────────┤                            │
     │                            │                            │
```

### 9.3 Estrutura do JWT

**Payload do Access Token:**
```json
{
  "user_id": 123,
  "type": "access",
  "exp": 1737738000,
  "iat": 1737734400
}
```

**Payload do Refresh Token:**
```json
{
  "user_id": 123,
  "type": "refresh",
  "exp": 1738339200,
  "iat": 1737734400
}
```

**Assinatura:** HMAC-SHA256 com `JWT_SECRET` do .env

### 9.4 Middleware de Autenticação

```python
# Dependency para rotas protegidas
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    jwt_service: JWTService = Depends(Provide[Container.jwt_service])
) -> int:
    try:
        payload = jwt_service.decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Uso em routers
@router.get("/diary/list")
async def list_diaries(
    current_user: int = Depends(get_current_user),
    use_case: ListDiaryUseCase = Depends(...)
):
    # current_user já é o user_id validado
    result = await use_case.execute(current_user)
    ...
```

### 9.5 Segurança de Senhas

**Hashing com bcrypt:**
```python
# Geração de hash
password_hash = bcrypt.hashpw(
    password.encode('utf-8'),
    bcrypt.gensalt(rounds=12)
)

# Verificação
is_valid = bcrypt.checkpw(
    password.encode('utf-8'),
    stored_hash
)
```

**Características:**
- **Salt automático:** Cada senha tem salt único
- **Slow by design:** 12 rounds = ~150ms (resistente a brute force)
- **Future-proof:** Pode aumentar rounds conforme hardware evolui

### 9.6 Proteção contra Ataques Comuns

| Ataque | Proteção Implementada |
|--------|-----------------------|
| **SQL Injection** | SQLAlchemy ORM com prepared statements |
| **XSS** | FastAPI escapa HTML automaticamente, Pydantic valida inputs |
| **CSRF** | Não aplicável (API stateless), frontend pode usar tokens |
| **Brute Force** | Rate limiting (futuro), bcrypt slow hashing |
| **JWT Replay** | Tokens com expiração curta, refresh tokens rotativos (futuro) |
| **Password Reset** | Tokens de uso único com expiração de 1h |

---

## 10. Infraestrutura e Deploy

### 10.1 Arquitetura de Deploy

**[SUGESTÃO DE IMAGEM 16: Diagrama de Deploy - Arquitetura de Produção]**
*Descrição:* Diagrama de infraestrutura mostrando:

**Camada 1 - Cliente:**
- Browser/Mobile App -> HTTPS

**Camada 2 - Load Balancer/CDN:**
- Nginx ou AWS ALB
- SSL/TLS termination

**Camada 3 - Aplicação:**
- Múltiplas instâncias FastAPI
- Gunicorn + Uvicorn workers
- Horizontal scaling (Kubernetes pods ou Docker Swarm)

**Camada 4 - Serviços Externos:**
- Gemini API (Google Cloud)
- MailerSend
- Supabase Storage

**Camada 5 - Banco de Dados:**
- PostgreSQL (managed service)
- Read replicas para queries RAG
- Backup automático diário

**Camada 6 - Monitoramento:**
- Logs centralizados (ELK stack)
- Métricas (Prometheus + Grafana)
- Alertas (PagerDuty)

### 10.2 Configuração de Produção

**Gunicorn + Uvicorn:**
```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

**Docker Compose (exemplo):**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - db
    command: gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

  db:
    image: ankane/pgvector:latest
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=agents_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### 10.3 Escalabilidade

**Horizontal Scaling:**
- API stateless permite múltiplas instâncias
- Load balancer distribui requisições
- Sessões via JWT (sem estado no servidor)

**Database Scaling:**
- **Write queries:** Master único (PRIMARY)
- **Read queries:** Read replicas (RAG queries são read-heavy)
- Connection pooling (SQLAlchemy AsyncEngine)

**Caching (futuro):**
- Redis para cache de embeddings frequentes
- Cache de resultados de análises

### 10.4 Monitoramento e Observabilidade

**Métricas Chave:**
- Request latency (p50, p95, p99)
- Error rate (5xx)
- Database query time
- Gemini API latency
- Embeddings generation time

**Logs Estruturados:**
```python
# Exemplo de log estruturado
logger.info("pei_generated", extra={
    "beneficiary_id": 123,
    "pei_id": 456,
    "generation_time_ms": 1200,
    "embeddings_count": 15
})
```

**Health Checks:**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_db_connection(),
        "gemini_api": await check_gemini_api(),
        "timestamp": datetime.utcnow()
    }
```

---

## 11. Configuração de Ambiente

### 11.1 Variáveis de Ambiente (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/agents_db

# JWT
JWT_SECRET=your-super-secret-key-min-32-chars

# Gemini (Principal)
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-1.5-pro
GEMINI_EMBEDDING_MODEL=models/embedding-001

# Email
MAILERSEND_API_KEY=mlsn...
MAILERSEND_FROM_EMAIL=noreply@yourdomain.com
FRONTEND_URL=http://localhost:3000

# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbG...
SUPABASE_BUCKET=uploads

# OpenAI (Opcional)
# OPENAI_API_KEY=sk-...
# GPT_MODEL=gpt-4

# Groq (Opcional)
# GROQ_API_KEY=gsk_...
# GROQ_MODEL=mixtral-8x7b-32768

# Ambiente
ENVIRONMENT=production  # ou development
LOG_LEVEL=INFO
```

### 11.2 Instalação Local

**Pré-requisitos:**
- Python 3.11+
- PostgreSQL 15+ com pgvector
- Git

**Passos:**

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/agents.git
cd agents
```

2. **Crie ambiente virtual:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure PostgreSQL:**
```sql
CREATE DATABASE agents_db;
\c agents_db
CREATE EXTENSION vector;
```

5. **Configure .env:**
```bash
cp .env.example .env
# Edite .env com suas credenciais
```

6. **Execute migrações:**
```bash
alembic upgrade head
```

7. **Inicie o servidor:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

8. **Acesse documentação:**
```
http://localhost:8000/docs
```

### 11.3 Estrutura de Arquivos

```
agents/
├── alembic/                    # Migrações de banco
│   ├── versions/              # Arquivos de migração
│   └── env.py                 # Config Alembic
├── api/                       # Routers FastAPI
│   ├── auth_routes.py
│   ├── diary_routes.py
│   └── ...
├── core/                      # Lógica de negócio
│   ├── config.py             # Configurações
│   ├── kernel/
│   │   ├── container.py      # DI Container
│   │   └── result.py         # Result type
│   ├── services/
│   │   └── jwt_service.py
│   └── use_case/             # 88 use cases
├── domain/                    # Schemas Pydantic
│   └── schema.py
├── infrastructure/            # Detalhes técnicos
│   ├── database_context/
│   │   └── database.py       # SQLAlchemy config
│   ├── models/               # ORM models (30+ tabelas)
│   ├── repositories/         # Data access (23+ repos)
│   └── services/             # Serviços externos
│       ├── email_service.py
│       ├── llm_service.py
│       └── storage_service.py
├── main.py                    # Aplicação FastAPI
├── requirements.txt           # Dependências
├── .env.example              # Template de variáveis
├── alembic.ini               # Config Alembic
└── README.md                 # Documentação geral
```

---

## 12. Considerações Finais

### 12.1 Pontos Fortes da Arquitetura

1. **Separação de Responsabilidades:** Clean Architecture permite evolução independente das camadas
2. **Testabilidade:** Dependency Injection facilita mocks e testes unitários
3. **Performance:** Async/await + pgvector para buscas rápidas
4. **IA Contextual:** RAG fornece respostas baseadas em dados reais do aluno
5. **Escalabilidade:** API stateless permite horizontal scaling
6. **Manutenibilidade:** 88 use cases pequenos e focados, fáceis de modificar

### 12.2 Próximos Passos Sugeridos

**Curto Prazo:**
- [ ] Implementar testes unitários (pytest)
- [ ] Adicionar rate limiting (slowapi)
- [ ] Implementar RBAC (Role-Based Access Control)
- [ ] Cache com Redis para embeddings

**Médio Prazo:**
- [ ] Dashboard analytics (métricas agregadas)
- [ ] Notificações push (Firebase)
- [ ] Suporte multi-tenancy (múltiplas instituições)
- [ ] API versioning (v2)

**Longo Prazo:**
- [ ] Mobile app (React Native)
- [ ] Integração com prontuários eletrônicos
- [ ] Fine-tuning de modelo Gemini com dados do sistema
- [ ] Sistema de recomendações proativas

### 12.3 Referências Técnicas

**Documentações:**
- [FastAPI](https://fastapi.tiangolo.com)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [pgvector](https://github.com/pgvector/pgvector)
- [Gemini API](https://ai.google.dev/docs)
- [Pydantic V2](https://docs.pydantic.dev/2.0/)

**Papers Relacionados:**
- RAG: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)
- Embeddings: "Attention Is All You Need" (Vaswani et al., 2017)

---

**Documento elaborado em:** Janeiro 2026
**Versão:** 1.0
**Autor:** Equipe de Desenvolvimento
**Projeto:** Mestrado em Educação Inclusiva - Agente IA para TEA
