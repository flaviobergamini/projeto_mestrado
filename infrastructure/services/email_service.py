from mailersend import MailerSendClient, EmailBuilder
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = settings.MAILERSEND_API_KEY
        self.from_email = settings.MAILERSEND_FROM_EMAIL
        self.from_name = settings.MAILERSEND_FROM_NAME
        self.client = MailerSendClient(api_key=self.api_key)

    def send_verification_email(self, to_email: str, to_name: str, verification_token: str) -> bool:
        """
        Envia email de verificação para o usuário.
        """
        try:
            verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={verification_token}"

            html_content = f"""
            <html>
                <body>
                    <h1>Bem-vindo(a), {to_name}!</h1>
                    <p>Obrigado por se cadastrar. Por favor, verifique seu email clicando no link abaixo:</p>
                    <p><a href="{verification_url}">Verificar Email</a></p>
                    <p>Ou copie e cole este link no seu navegador:</p>
                    <p>{verification_url}</p>
                    <p>Este link expira em 24 horas.</p>
                </body>
            </html>
            """

            text_content = f"Bem-vindo(a), {to_name}! Verifique seu email acessando: {verification_url}"

            email = (
                EmailBuilder()
                .from_email(self.from_email, self.from_name)
                .to(to_email, to_name)
                .subject("Verifique seu email")
                .html(html_content)
                .text(text_content)
                .build()
            )

            response = self.client.emails.send(email)
            logger.info(f"Verification email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending verification email to {to_email}: {str(e)}")
            return False

    def send_password_reset_email(self, to_email: str, to_name: str, reset_token: str) -> bool:
        """
        Envia email de recuperação de senha para o usuário.
        """
        try:
            reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"

            html_content = f"""
            <html>
                <body>
                    <h1>Olá, {to_name}!</h1>
                    <p>Você solicitou a recuperação de senha. Clique no link abaixo para redefinir sua senha:</p>
                    <p><a href="{reset_url}">Redefinir Senha</a></p>
                    <p>Ou copie e cole este link no seu navegador:</p>
                    <p>{reset_url}</p>
                    <p>Este link expira em 1 hora.</p>
                    <p>Se você não solicitou esta recuperação, ignore este email.</p>
                </body>
            </html>
            """

            text_content = f"Olá, {to_name}! Recupere sua senha acessando: {reset_url}"

            email = (
                EmailBuilder()
                .from_email(self.from_email, self.from_name)
                .to(to_email, to_name)
                .subject("Recuperação de senha")
                .html(html_content)
                .text(text_content)
                .build()
            )

            response = self.client.emails.send(email)
            logger.info(f"Password reset email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending password reset email to {to_email}: {str(e)}")
            return False
