"""Sanidade básica: a aplicação sobe e o /health responde — sem autenticação,
sem banco de dados real. Se este teste falhar, algo quebrou no boot da app
(import circular, container mal configurado, rota com erro de sintaxe etc.)
antes mesmo de qualquer lógica de negócio ser exercitada."""

from fastapi.testclient import TestClient

from main import app


def test_health_check_returns_ok():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "TEA AI Agent API is running"}


def test_protected_route_without_token_returns_401():
    with TestClient(app) as client:
        response = client.get("/students")
    assert response.status_code in (401, 403)
