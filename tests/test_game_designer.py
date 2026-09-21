from unittest.mock import MagicMock, patch

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


def test_design_falls_back_when_anthropic_call_fails():
    """Un run public ne doit pas mourir sur un aléa de l'API Claude (réseau,
    rate limit, JSON malformé) — il doit retomber sur le starter kit."""
    logs: list[str] = []
    with patch("problox.game_designer.Anthropic") as MockAnthropic:
        MockAnthropic.return_value.messages.create.side_effect = RuntimeError("boom")
        d = game_designer.design("obby de test", "fake-api-key", log=logs.append)

    assert d.genre == "obby + simulator hybride"  # repli obby (mot-clé "obby")
    assert any("Claude a échoué" in line for line in logs)


def test_design_falls_back_on_malformed_json_response():
    logs: list[str] = []
    fake_block = MagicMock(type="text", text="ceci n'est pas du JSON valide {{{")
    fake_response = MagicMock(content=[fake_block])
    with patch("problox.game_designer.Anthropic") as MockAnthropic:
        MockAnthropic.return_value.messages.create.return_value = fake_response
        d = game_designer.design("tycoon de test", "fake-api-key", log=logs.append)

    assert d.genre == "tycoon"
    assert any("Claude a échoué" in line for line in logs)
