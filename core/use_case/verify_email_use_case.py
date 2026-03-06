from core.kernel.result import Result


class VerifyEmailUseCase:
    async def execute(self, token: str):
        # A verificação de email é gerenciada pelo Supabase Authentication.
        # O usuário recebe um link por email e confirma diretamente pelo Supabase.
        return Result.ok({
            "message": "A verificação de email é gerenciada pelo Supabase. Verifique seu email e clique no link enviado."
        })
