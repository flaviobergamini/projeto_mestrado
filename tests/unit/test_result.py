"""Testa o tipo Result<T,E> — usado em toda a camada core/use_case no lugar
de exceções para caminhos de falha esperados (bad_request, not_found, unauthorized)."""

from core.kernel.result import Result


def test_ok_carries_value_and_is_ok():
    result = Result.ok({"id": "abc"})
    assert result.is_ok
    assert not result.is_bad_request
    assert not result.is_not_found
    assert not result.is_unauthorized
    assert result.value == {"id": "abc"}


def test_err_is_not_ok():
    result = Result.err("erro genérico")
    assert not result.is_ok
    assert result.error == "erro genérico"


def test_bad_request_sets_only_bad_request_flag():
    result = Result.bad_request("dados inválidos")
    assert result.is_bad_request
    assert not result.is_not_found
    assert not result.is_unauthorized
    assert result.bad_request_error == "dados inválidos"


def test_not_found_sets_only_not_found_flag():
    result = Result.not_found("aluno não encontrado")
    assert result.is_not_found
    assert not result.is_bad_request
    assert result.not_found_error == "aluno não encontrado"


def test_unauthorized_sets_only_unauthorized_flag():
    result = Result.unauthorized("token inválido")
    assert result.is_unauthorized
    assert not result.is_bad_request
    assert result.unauthorized_error == "token inválido"
