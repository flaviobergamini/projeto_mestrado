# Documentação das Funcionalidades de Autenticação

Este documento descreve as novas funcionalidades de autenticação implementadas no sistema, incluindo verificação de email, recuperação de senha, troca de senha e refresh token.

## Índice
1. [Configuração](#configuração)
2. [Endpoints da API](#endpoints-da-api)
3. [Fluxos de Autenticação](#fluxos-de-autenticação)
4. [Migrações do Banco de Dados](#migrações-do-banco-de-dados)

## Configuração

### Variáveis de Ambiente

Adicione as seguintes variáveis ao seu arquivo `.env`:

```bash
# MailerSend Configuration
MAILERSEND_API_KEY=your_mailersend_api_key
MAILERSEND_FROM_EMAIL=noreply@yourdomain.com
MAILERSEND_FROM_NAME=Agents
FRONTEND_URL=http://localhost:3000
```

### Instalação de Dependências

Execute o seguinte comando para instalar as novas dependências:

```bash
pip install -r requirements.txt
```

### Migrações do Banco de Dados

Execute a migration para adicionar os novos campos na tabela de usuários:

```bash
alembic upgrade head
```

Isso adicionará os seguintes campos à tabela `users`:
- `email_verified` (Boolean): Indica se o email foi verificado
- `verification_token` (String): Token para verificação de email
- `reset_token` (String): Token para recuperação de senha
- `reset_token_expires` (DateTime): Data de expiração do token de recuperação
- O campo `email` foi expandido de 50 para 254 caracteres

## Endpoints da API

### 1. Registro de Usuário
**POST** `/auth/register`

Registra um novo usuário e envia email de verificação.

**Request Body:**
```json
{
  "name": "João Silva",
  "email": "joao@example.com",
  "password": "senha123"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "email_verified": false,
  "message": "Usuário criado com sucesso. Verifique seu email para ativar sua conta."
}
```

### 2. Login
**POST** `/auth/login`

Autentica um usuário existente.

**Request Body:**
```json
{
  "email": "joao@example.com",
  "password": "senha123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "email_verified": true
}
```

### 3. Verificação de Email
**POST** `/auth/verify-email`

Verifica o email do usuário usando o token enviado por email.

**Request Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "message": "Email verificado com sucesso",
  "email_verified": true
}
```

### 4. Recuperação de Senha (Forgot Password)
**POST** `/auth/forgot-password`

Solicita recuperação de senha. Envia email com link para redefinir senha.

**Request Body:**
```json
{
  "email": "joao@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Se o email estiver cadastrado, você receberá instruções para redefinir sua senha."
}
```

> **Nota de Segurança:** Por motivos de segurança, a resposta é sempre a mesma, independentemente de o email existir ou não no sistema.

### 5. Redefinir Senha (Reset Password)
**POST** `/auth/reset-password`

Redefine a senha do usuário usando o token enviado por email.

**Request Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "new_password": "novaSenha123"
}
```

**Response (200 OK):**
```json
{
  "message": "Senha redefinida com sucesso"
}
```

### 6. Refresh Token
**POST** `/auth/refresh-token`

Gera novos tokens de acesso e refresh usando um refresh token válido.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "email_verified": true
}
```

## Fluxos de Autenticação

### Fluxo de Registro e Verificação de Email

1. **Registro**: Usuário envia nome, email e senha para `/auth/register`
2. **Email Enviado**: Sistema envia email com link de verificação
3. **Verificação**: Usuário clica no link e é redirecionado para frontend com token
4. **Confirmação**: Frontend envia token para `/auth/verify-email`
5. **Sucesso**: Email marcado como verificado no banco de dados

### Fluxo de Recuperação de Senha

1. **Solicitação**: Usuário envia email para `/auth/forgot-password`
2. **Email Enviado**: Sistema envia email com link de recuperação (válido por 1 hora)
3. **Redefinição**: Usuário clica no link e é redirecionado para frontend com token
4. **Nova Senha**: Frontend envia token e nova senha para `/auth/reset-password`
5. **Sucesso**: Senha atualizada no banco de dados

### Fluxo de Refresh Token

1. **Expiração**: Access token expira (60 minutos de validade)
2. **Renovação**: Cliente envia refresh token para `/auth/refresh-token`
3. **Novos Tokens**: Sistema retorna novo access token e refresh token
4. **Continuidade**: Cliente continua usando a aplicação com novos tokens

## Tipos de Token

O sistema usa diferentes tipos de tokens JWT:

| Tipo | Duração | Uso |
|------|---------|-----|
| `access` | 60 minutos | Autenticação nas requisições da API |
| `refresh` | 7 dias | Renovação de access tokens |
| `verification` | 24 horas | Verificação de email |
| `reset` | 1 hora | Recuperação de senha |

## Estrutura de Email

### Email de Verificação
- **Assunto**: "Verifique seu email"
- **Conteúdo**: Link para verificação válido por 24 horas
- **Template**: HTML e texto plano

### Email de Recuperação de Senha
- **Assunto**: "Recuperação de senha"
- **Conteúdo**: Link para redefinir senha válido por 1 hora
- **Template**: HTML e texto plano

## Segurança

### Medidas Implementadas

1. **Tokens JWT Assinados**: Todos os tokens são assinados com HS256
2. **Expirações Apropriadas**: Cada tipo de token tem duração específica
3. **Validação de Token no Banco**: Tokens de verificação e reset são validados contra o banco de dados
4. **Hashing de Senha**: Senhas são hasheadas com bcrypt
5. **Proteção contra Enumeração**: Forgot password não revela se email existe
6. **Limpeza de Tokens**: Tokens são removidos do banco após uso

## Troubleshooting

### Email não está sendo enviado

1. Verifique se as credenciais do MailerSend estão corretas
2. Confirme que o domínio está verificado no MailerSend
3. Verifique os logs do servidor para erros de envio
4. Teste a API Key do MailerSend separadamente

### Token inválido ou expirado

1. Tokens de verificação expiram em 24 horas
2. Tokens de reset expiram em 1 hora
3. Refresh tokens expiram em 7 dias
4. Access tokens expiram em 60 minutos

### Usuário não recebe email

1. Verifique a pasta de spam
2. Confirme que o email está correto
3. Verifique se o MailerSend tem limites de envio atingidos
4. Verifique os logs do servidor

## Próximos Passos

Para integrar essas funcionalidades no frontend:

1. Criar páginas para verificação de email e reset de senha
2. Implementar interceptor HTTP para renovação automática de tokens
3. Adicionar indicador visual de email não verificado
4. Implementar formulários de forgot password e reset password
5. Armazenar tokens de forma segura (HttpOnly cookies ou localStorage com cuidado)

## Suporte

Para dúvidas ou problemas, consulte a documentação do MailerSend: https://www.mailersend.com/help
