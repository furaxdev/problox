from problox import game_designer


def test_fallback_picks_tycoon_from_keyword():
    d = game_designer.design("usine a coins", None)
    assert d.genre == "tycoon"
    assert "PlotService" not in d.core_loop  # sanity: pas de fuite de détail technique


def test_fallback_picks_obby_from_keyword():
    d = game_designer.design("parkour de la mort", None)
    assert "obby" in d.genre


def test_fallback_picks_arena_from_keyword():
    d = game_designer.design("battle royale casual entre amis", None)
    assert d.genre == "battle royale casual"


def test_fallback_is_deterministic_for_generic_theme():
    a = game_designer.design("un thème quelconque", None)
    b = game_designer.design("un thème quelconque", None)
    assert a.genre == b.genre


def test_fallback_generic_theme_is_still_a_valid_archetype():
    d = game_designer.design("zzz totally generic zzz", None)
    assert d.genre in ("obby + simulator hybride", "tycoon", "battle royale casual")
