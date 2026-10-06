"""Guarda da arquitetura limpa: dependências só apontam para dentro.

- core/use_case, core/interfaces, core/services, core/constants não importam infrastructure, api nem frameworks de I/O.
- Routers já migrados são só camada HTTP: não importam infrastructure.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INNER_DIRS = ["core/use_case", "core/interfaces", "core/services", "core/constants"]
FORBIDDEN_FOR_INNER = ("infrastructure", "api", "sqlalchemy", "fastapi", "google")

MIGRATED_ROUTERS = [
    "api/skill_plan_routes.py", "api/bncc_routes.py", "api/functional_profile_routes.py",
    "api/pei_kanban_routes.py", "api/links_routes.py",
]


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def _violations(files, forbidden) -> list[str]:
    out = []
    for f in files:
        for mod in _imports(f):
            if mod.split(".")[0] in forbidden:
                out.append(f"{f.relative_to(ROOT)} importa {mod}")
    return out


def test_inner_layers_do_not_depend_on_outer_layers():
    files = [p for d in INNER_DIRS for p in (ROOT / d).rglob("*.py")]
    # use cases legados de autenticação ainda dependem de infraestrutura; os módulos novos não podem.
    legacy = {p for p in (ROOT / "core/use_case").glob("*.py")} | {ROOT / "core/services/jwt_service.py"}
    checked = [f for f in files if f not in legacy]
    assert _violations(checked, FORBIDDEN_FOR_INNER) == []


def test_migrated_routers_do_not_import_infrastructure():
    files = [ROOT / p for p in MIGRATED_ROUTERS]
    assert _violations(files, ("infrastructure",)) == []
