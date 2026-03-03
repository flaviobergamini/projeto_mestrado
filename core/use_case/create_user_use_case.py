from datetime import datetime
from core.kernel.result import Result
from core.services.jwt_service import JwtService
from infrastructure.models.users import User
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository, jwt_service: JwtService, email_service: EmailService):
        self.user_repository = user_repository
        self.jwt_service = jwt_service
        self.email_service = email_service

    async def execute(self, user: User):
        try:
            check_user = await self.user_repository.get_by_email(user.email)

            if check_user:
                return Result.bad_request("E-mail já cadastrado")

            user.password = self.jwt_service.hash_password(user.password)
            user.created_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
            user.email_verified = False

            # Gerar token de verificação
            verification_token = self.jwt_service.create_verification_token({"email": user.email})
            user.verification_token = verification_token

                # Enviar email de verificação em background
            try:
                self.email_service.send_verification_email(
                    to_email=check_user.email,
                    to_name=check_user.name,
                    verification_token=verification_token
                )

                await self.user_repository.add(user)
            except Exception as email_error:
                logger.error(f"Erro ao enviar email de verificação: {str(email_error)}")
                return Result.error(f"Erro ao cadastrar usuário no sistema")

            token = self.jwt_service.create_access_token({"sub": str(check_user.id)})
            refresh_token = self.jwt_service.create_refresh_token({"sub": str(check_user.id)})

            return Result.ok({
                "access_token": token,
                "refresh_token": refresh_token,
                "email_verified": False,
                "message": "Usuário criado com sucesso. Verifique seu email para ativar sua conta."
            })

        except Exception as e:
            logger.error(f"Erro ao cadastrar usuário: {str(e)}")
            return Result.error(f"Erro ao cadastrar usuário")