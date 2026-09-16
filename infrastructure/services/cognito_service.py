import hmac
import hashlib
import base64
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Optional
from core.config import settings
from core.interfaces.i_auth_service import IAuthService
from core.exceptions.auth_exceptions import (
    UserAlreadyExistsError, InvalidCredentialsError, UserNotConfirmedError,
    InvalidCodeError, UserNotFoundError, TooManyRequestsError, AuthException,
)

logger = logging.getLogger(__name__)

_COGNITO_ERROR_MAP = {
    "UsernameExistsException": UserAlreadyExistsError,
    # Pool usa UsernameAttributes=['email']: trocar o atributo email pra um
    # valor já usado por OUTRO usuário levanta AliasExistsException, não
    # UsernameExistsException (essa é só pra criação de usuário novo).
    "AliasExistsException": UserAlreadyExistsError,
    "UserNotFoundException": UserNotFoundError,
    "NotAuthorizedException": InvalidCredentialsError,
    "UserNotConfirmedException": UserNotConfirmedError,
    "CodeMismatchException": InvalidCodeError,
    "ExpiredCodeException": InvalidCodeError,
    "LimitExceededException": TooManyRequestsError,
    "TooManyRequestsException": TooManyRequestsError,
}

_COGNITO_MESSAGES = {
    "UsernameExistsException": "Usuário já cadastrado",
    "AliasExistsException": "Este e-mail já está em uso por outro usuário",
    "InvalidPasswordException": "Senha inválida — use ao menos 8 caracteres, letras maiúsculas, minúsculas, números e símbolos",
    "UserNotFoundException": "Usuário não encontrado",
    "NotAuthorizedException": "Usuário ou senha inválidos",
    "UserNotConfirmedException": "E-mail não confirmado — verifique sua caixa de entrada",
    "CodeMismatchException": "Código inválido",
    "ExpiredCodeException": "Código expirado — solicite um novo",
    "LimitExceededException": "Muitas tentativas — aguarde alguns minutos",
    "TooManyRequestsException": "Muitas requisições — tente mais tarde",
    "InvalidParameterException": "Parâmetros inválidos",
}


def _to_domain_exception(error: ClientError) -> AuthException:
    code = error.response["Error"]["Code"]
    raw_message = error.response["Error"].get("Message", "")
    logger.error(f"[Cognito] {code}: {raw_message}")
    message = _COGNITO_MESSAGES.get(code, f"Erro de autenticação: {code} — {raw_message}")
    exc_class = _COGNITO_ERROR_MAP.get(code, AuthException)
    return exc_class(message)


class CognitoService(IAuthService):
    def __init__(self):
        self.client = boto3.client("cognito-idp", region_name=settings.COGNITO_REGION)
        self.user_pool_id = settings.COGNITO_USER_POOL_ID
        self.client_id = settings.COGNITO_APP_CLIENT_ID
        self.client_secret = settings.COGNITO_APP_CLIENT_SECRET

    def _secret_hash(self, username: str) -> str:
        message = username + self.client_id
        secret = self.client_secret.encode("utf-8")
        digest = hmac.new(secret, message.encode("utf-8"), hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    def _base_kwargs(self, username: str) -> dict:
        kwargs = {"ClientId": self.client_id}
        if self.client_secret:
            kwargs["SecretHash"] = self._secret_hash(username)
        return kwargs

    def admin_create_user(self, username: str, password: str, email: str, full_name: Optional[str] = None) -> str:
        """Cria usuário via API admin — já confirma o e-mail automaticamente, sem código de verificação."""
        user_attributes = [{"Name": "email", "Value": email}, {"Name": "email_verified", "Value": "true"}]
        if full_name:
            user_attributes.append({"Name": "name", "Value": full_name})
        try:
            response = self.client.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=username,
                TemporaryPassword=password,
                UserAttributes=user_attributes,
            )
            sub = next(
                a["Value"] for a in response["User"]["Attributes"] if a["Name"] == "sub"
            )
            # Define a senha permanente imediatamente, evitando o fluxo FORCE_CHANGE_PASSWORD
            self.client.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=username,
                Password=password,
                Permanent=True,
            )
            return sub
        except ClientError as e:
            raise _to_domain_exception(e)

    def sign_up(self, username: str, password: str, email: str, full_name: Optional[str] = None) -> str:
        user_attributes = [{"Name": "email", "Value": email}]
        if full_name:
            user_attributes.append({"Name": "name", "Value": full_name})
        try:
            response = self.client.sign_up(
                **self._base_kwargs(username),
                Username=username,
                Password=password,
                UserAttributes=user_attributes,
            )
            return response["UserSub"]
        except ClientError as e:
            raise _to_domain_exception(e)

    def confirm_sign_up(self, username: str, code: str) -> None:
        try:
            self.client.confirm_sign_up(
                **self._base_kwargs(username),
                Username=username,
                ConfirmationCode=code,
            )
        except ClientError as e:
            raise _to_domain_exception(e)

    def resend_confirmation_code(self, username: str) -> None:
        try:
            self.client.resend_confirmation_code(
                **self._base_kwargs(username),
                Username=username,
            )
        except ClientError as e:
            raise _to_domain_exception(e)

    def sign_in(self, username: str, password: str) -> dict:
        auth_params = {"USERNAME": username, "PASSWORD": password}
        if self.client_secret:
            auth_params["SECRET_HASH"] = self._secret_hash(username)
        try:
            response = self.client.initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters=auth_params,
                ClientId=self.client_id,
            )
            tokens = response["AuthenticationResult"]
            return {
                "access_token": tokens["AccessToken"],
                "id_token": tokens["IdToken"],
                "refresh_token": tokens["RefreshToken"],
                "expires_in": tokens.get("ExpiresIn", 3600),
            }
        except ClientError as e:
            raise _to_domain_exception(e)

    def refresh_token(self, username: str, refresh_token: str) -> dict:
        auth_params = {"REFRESH_TOKEN": refresh_token}
        if self.client_secret:
            auth_params["SECRET_HASH"] = self._secret_hash(username)
        try:
            response = self.client.initiate_auth(
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters=auth_params,
                ClientId=self.client_id,
            )
            tokens = response["AuthenticationResult"]
            return {
                "access_token": tokens["AccessToken"],
                "id_token": tokens["IdToken"],
                "expires_in": tokens.get("ExpiresIn", 3600),
            }
        except ClientError as e:
            raise _to_domain_exception(e)

    def forgot_password(self, username: str) -> None:
        try:
            self.client.forgot_password(
                **self._base_kwargs(username),
                Username=username,
            )
        except ClientError as e:
            raise _to_domain_exception(e)

    def confirm_forgot_password(self, username: str, code: str, new_password: str) -> None:
        try:
            self.client.confirm_forgot_password(
                **self._base_kwargs(username),
                Username=username,
                ConfirmationCode=code,
                Password=new_password,
            )
        except ClientError as e:
            raise _to_domain_exception(e)

    def update_email(self, username: str, new_email: str) -> None:
        """Troca o e-mail de login de um usuário existente. O pool usa
        UsernameAttributes=['email'] (confirmado via describe_user_pool) — o
        Cognito sincroniza automaticamente quem o usuário deve digitar pra
        logar com o novo valor do atributo `email`, sem precisar recriar a
        conta. `username` é o identificador atual (email antigo) do usuário."""
        try:
            self.client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=username,
                UserAttributes=[
                    {"Name": "email", "Value": new_email},
                    {"Name": "email_verified", "Value": "true"},
                ],
            )
        except ClientError as e:
            raise _to_domain_exception(e)

    def delete_user(self, username: str) -> None:
        """Remove o usuário do Cognito User Pool pelo username (email)."""
        try:
            self.client.admin_delete_user(
                UserPoolId=self.user_pool_id,
                Username=username,
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "UserNotFoundException":
                return  # já removido, não é erro
            raise _to_domain_exception(e)

    def get_username_from_token(self, access_token: str) -> str:
        """
        Retorna o 'sub' (UUID estável) do usuário Cognito a partir do access token.
        Usamos 'sub' em vez de 'Username' porque, quando o User Pool está configurado
        com email como alias de login, o campo Username pode retornar o UUID interno
        em vez do email — tornando a busca por username inconsistente.
        O 'sub' é sempre o UUID do usuário e corresponde ao campo 'id' em user_profiles.
        """
        try:
            response = self.client.get_user(AccessToken=access_token)
            attrs = {a["Name"]: a["Value"] for a in response.get("UserAttributes", [])}
            sub = attrs.get("sub")
            if not sub:
                # fallback: usa Username se sub não estiver nos atributos
                sub = response["Username"]
            return sub
        except ClientError as e:
            raise _to_domain_exception(e)
