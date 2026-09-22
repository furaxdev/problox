import json
from unittest.mock import patch

from problox.hermes_bot import agent, sandbox
from problox.hermes_bot.config import HermesConfig


def _config(**overrides) -> HermesConfig:
    base = dict(
        discord_token="fake",
        deepseek_api_key="fake",
        admin_user_ids={42},
    )
    base.update(overrides)
    return HermesConfig(**base)


def test_config_admin_and_guild_gating():
    config = _config(allowed_guild_ids={100})
    assert config.is_admin(42)
    assert not config.is_admin(1)
    assert config.guild_allowed(100)
    assert not config.guild_allowed(200)


def test_config_no_guild_restriction_means_open():
    config = _config()
    assert config.guild_allowed(999)


def test_sandbox_runs_simple_script():
    result = sandbox.run_python("print('hello')", timeout_seconds=5.0, memory_limit_mb=128)
    assert result.exit_code == 0
    assert "hello" in result.stdout


def test_sandbox_times_out_on_infinite_loop():
    result = sandbox.run_python("while True: pass", timeout_seconds=1.0, memory_limit_mb=128)
    assert result.timed_out


def test_admin_only_tool_blocked_for_non_admin():
    config = _config()
    result = agent.run_tool(
        "execute_code",
        {"code": "print(1)"},
        config=config,
        channel_id=1,
        is_admin=False,
        subagent_depth=0,
    )
    assert "réservé" in result


def test_run_turn_returns_direct_answer_without_tools():
    config = _config()

    fake_message = {"role": "assistant", "content": "salut !"}
    with patch("problox.hermes_bot.agent.DeepSeekClient.chat", return_value=fake_message):
        reply, new_messages = agent.run_turn(
            history=[],
            user_message="salut",
            config=config,
            channel_id=1,
            is_admin=False,
        )

    assert reply == "salut !"
    assert new_messages[0] == {"role": "user", "content": "salut"}


def test_run_turn_executes_tool_call_then_answers():
    config = _config(admin_user_ids={7})

    tool_call_msg = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_1",
                "function": {"name": "web_search", "function_args": None, "arguments": json.dumps({"query": "roblox"})},
            }
        ],
    }
    final_msg = {"role": "assistant", "content": "voilà ce que j'ai trouvé"}

    with patch("problox.hermes_bot.agent.DeepSeekClient.chat", side_effect=[tool_call_msg, final_msg]), patch(
        "problox.hermes_bot.tools.web_search", return_value="résultat bidon"
    ):
        reply, new_messages = agent.run_turn(
            history=[],
            user_message="cherche des infos sur roblox",
            config=config,
            channel_id=1,
            is_admin=True,
        )

    assert reply == "voilà ce que j'ai trouvé"
    tool_messages = [m for m in new_messages if m.get("role") == "tool"]
    assert len(tool_messages) == 1
    assert tool_messages[0]["content"] == "résultat bidon"
