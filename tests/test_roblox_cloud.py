from unittest.mock import MagicMock, patch

from problox import roblox_cloud


def _client() -> roblox_cloud.RobloxCloudClient:
    return roblox_cloud.RobloxCloudClient(universe_id="1", place_id="2", api_key="fake")


def test_execute_luau_success():
    create_resp = MagicMock(status_code=200, json=lambda: {"path": "universes/1/places/2/versions/3/luau-execution-sessions/abc"})
    poll_resp = MagicMock(
        status_code=200,
        json=lambda: {
            "state": "COMPLETE",
            "output": {"results": [{"message": "SMOKE_OK"}]},
        },
    )
    with patch("problox.roblox_cloud.httpx.post", return_value=create_resp), patch(
        "problox.roblox_cloud.httpx.get", return_value=poll_resp
    ):
        result = _client().execute_luau(3, "print('SMOKE_OK')")

    assert result.success
    assert result.output_lines == ["SMOKE_OK"]


def test_execute_luau_reports_script_error():
    create_resp = MagicMock(status_code=200, json=lambda: {"path": "universes/1/places/2/versions/3/luau-execution-sessions/abc"})
    poll_resp = MagicMock(
        status_code=200,
        json=lambda: {"state": "FAILED", "error": {"message": "attempt to call a nil value"}},
    )
    with patch("problox.roblox_cloud.httpx.post", return_value=create_resp), patch(
        "problox.roblox_cloud.httpx.get", return_value=poll_resp
    ):
        result = _client().execute_luau(3, "broken()")

    assert not result.success
    assert "nil value" in result.error


def test_execute_luau_raises_on_start_failure():
    create_resp = MagicMock(status_code=403, text="missing scope")
    with patch("problox.roblox_cloud.httpx.post", return_value=create_resp):
        try:
            _client().execute_luau(3, "print(1)")
            assert False, "should have raised"
        except roblox_cloud.RobloxCloudError as exc:
            assert "403" in str(exc)
