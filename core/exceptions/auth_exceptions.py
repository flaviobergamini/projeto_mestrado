class AuthException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class UserAlreadyExistsError(AuthException):
    pass


class InvalidCredentialsError(AuthException):
    pass


class UserNotConfirmedError(AuthException):
    pass


class InvalidCodeError(AuthException):
    pass


class UserNotFoundError(AuthException):
    pass


class TooManyRequestsError(AuthException):
    pass
