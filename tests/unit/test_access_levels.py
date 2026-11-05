from core.permissions.access_levels import blocks_write, keys_for_path, normalize_levels

READ_ONLY = {"schoolDiary": "read", "skillsTracking": "write", "schoolProfile": "write"}


def test_old_list_format_means_write_and_unconfigured_role_is_never_blocked():
    assert normalize_levels(["students", "caseStudy"]) == {"students": "write", "caseStudy": "write"}
    assert normalize_levels({"a": "read", "b": "write", "c": "none", "d": "x"}) == {"a": "read", "b": "write"}
    assert normalize_levels(None) is None
    assert blocks_write(None, "/diary/entries", "POST") is False
    assert blocks_write(normalize_levels(["schoolDiary"]), "/diary/entries", "POST") is False


def test_read_only_screen_blocks_writes_but_not_reads():
    assert blocks_write(READ_ONLY, "/diary", "POST") is True
    assert blocks_write(READ_ONLY, "/diary/abc", "DELETE") is True
    assert blocks_write(READ_ONLY, "/diary/abc", "GET") is False
    assert blocks_write(READ_ONLY, "/pei-kanban/x", "PATCH") is False      # essa tela está em "editar"


def test_screen_without_access_is_also_not_writable():
    assert blocks_write(READ_ONLY, "/case-studies", "POST") is True        # ausente do mapa = sem acesso


def test_longest_prefix_and_shared_routes():
    assert keys_for_path("/diary-summary/generate") == ("dailySummary",)   # não cai em /diary
    assert keys_for_path("/family/diary/therapy/1") == ("therapyDiary",)
    assert keys_for_path("/pei-kanban/from-skill") == ("skillsRegistry",)  # exportar do plano é da tela de habilidades
    assert blocks_write(READ_ONLY, "/schools/s1", "PUT") is False          # o questionário da escola grava em /schools


def test_unmapped_and_exempt_routes_are_free():
    for path in ("/chat/message", "/pei-kanban/report", "/auth/login", "/unknown/thing", "/family/transcribe-audio"):
        assert blocks_write({}, path, "POST") is False
