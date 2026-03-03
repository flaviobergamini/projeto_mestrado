from datetime import datetime, timedelta
from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

class ForgotPasswordUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService, email_service: EmailService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service
        self.email_service = email_service

    async def execute(self, email: str):
        try:
            # Buscar usuário pelo email
            user = await self.user_repository.get_by_email(email)

            # Por segurança, sempre retornar sucesso mesmo se o usuário não existir
            # Isso evita que atacantes descubram emails cadastrados no sistema
            if not user:
                logger.info(f"Tentativa de reset de senha para email não cadastrado: {email}")
                return Result.ok({
                    "message": "Se o email estiver cadastrado, você receberá instruções para redefinir sua senha."
                })

            # Gerar token de reset de senha
            reset_token = self.jwt_service.create_reset_token({"sub": str(user.id), "email": user.email})

            # Salvar token e data de expiração no banco
            user.reset_token = reset_token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            user.updated_at = datetime.utcnow()

            await self.user_repository.update(user)

            # Enviar email de recuperação de senha
            try:
                self.email_service.send_password_reset_email(
                    to_email=user.email,
                    to_name=user.name,
                    reset_token=reset_token
                )
            except Exception as email_error:
                logger.error(f"Erro ao enviar email de recuperação: {str(email_error)}")
                return Result.error("Erro ao enviar email de recuperação")

            return Result.ok({
                "message": "Se o email estiver cadastrado, você receberá instruções para redefinir sua senha."
            })

        except Exception as e:
            logger.error(f"Erro ao processar recuperação de senha: {str(e)}")
            return Result.error("Erro ao processar solicitação")
