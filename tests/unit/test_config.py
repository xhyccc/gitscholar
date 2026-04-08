"""Tests for the configuration resolution module."""

from __future__ import annotations

import os
from unittest.mock import patch

from sci.core.config import resolve_git_config, resolve_llm_config, resolve_settings
from sci.models.scholar import AgentSettings, GitConfig, GlobalSettings, LLMProviderConfig


class TestResolveLLMConfig:
    """Tests for LLM configuration resolution."""

    def test_explicit_values_take_priority(self) -> None:
        agent = AgentSettings(
            llm=LLMProviderConfig(
                provider="openai",
                api_key="explicit-key",
                api_base="https://custom.api/v1",
                model="gpt-4o",
            )
        )
        resolved = resolve_llm_config(agent)
        assert resolved.provider == "openai"
        assert resolved.api_key == "explicit-key"
        assert resolved.api_base == "https://custom.api/v1"
        assert resolved.model == "gpt-4o"

    def test_env_vars_used_when_no_explicit_value(self) -> None:
        agent = AgentSettings()
        env = {
            "SCI_LLM_PROVIDER": "anthropic",
            "SCI_LLM_API_KEY": "env-key",
            "SCI_LLM_API_BASE": "https://api.anthropic.com",
            "SCI_LLM_MODEL": "claude-opus-4",
        }
        with patch.dict(os.environ, env, clear=False):
            resolved = resolve_llm_config(agent)
        assert resolved.provider == "anthropic"
        assert resolved.api_key == "env-key"
        assert resolved.api_base == "https://api.anthropic.com"
        assert resolved.model == "claude-opus-4"

    def test_legacy_api_key_env_fallback(self) -> None:
        agent = AgentSettings(api_key_env="CLAW_API_KEY")
        env = {"CLAW_API_KEY": "legacy-key"}
        with patch.dict(os.environ, env, clear=False):
            resolved = resolve_llm_config(agent)
        assert resolved.api_key == "legacy-key"

    def test_sci_env_key_overrides_legacy(self) -> None:
        agent = AgentSettings(api_key_env="CLAW_API_KEY")
        env = {"SCI_LLM_API_KEY": "new-key", "CLAW_API_KEY": "legacy-key"}
        with patch.dict(os.environ, env, clear=False):
            resolved = resolve_llm_config(agent)
        assert resolved.api_key == "new-key"

    def test_default_model_from_agent_settings(self) -> None:
        agent = AgentSettings(default_model="claude-sonnet-4")
        with patch.dict(os.environ, {}, clear=False):
            # Remove any SCI_LLM_MODEL that might be set
            os.environ.pop("SCI_LLM_MODEL", None)
            resolved = resolve_llm_config(agent)
        assert resolved.model == "claude-sonnet-4"

    def test_empty_defaults(self) -> None:
        agent = AgentSettings()
        with patch.dict(os.environ, {}, clear=False):
            for key in ("SCI_LLM_PROVIDER", "SCI_LLM_API_KEY", "SCI_LLM_API_BASE",
                        "SCI_LLM_MODEL", "CLAW_API_KEY"):
                os.environ.pop(key, None)
            resolved = resolve_llm_config(agent)
        assert resolved.provider == ""
        assert resolved.api_key == ""
        assert resolved.api_base == ""
        assert resolved.model == agent.default_model


class TestResolveGitConfig:
    """Tests for git configuration resolution."""

    def test_explicit_values_take_priority(self) -> None:
        git = GitConfig(
            user_name="Explicit Name",
            user_email="explicit@example.com",
            signing_key="EXPLICIT123",
        )
        with patch("sci.core.config._git_config_value", return_value="system-value"):
            resolved = resolve_git_config(git)
        assert resolved.user_name == "Explicit Name"
        assert resolved.user_email == "explicit@example.com"
        assert resolved.signing_key == "EXPLICIT123"

    def test_falls_back_to_git_config(self) -> None:
        git = GitConfig()

        def mock_git(key: str) -> str:
            return {
                "user.name": "Git User",
                "user.email": "git@example.com",
                "user.signingkey": "GITKEY",
            }.get(key, "")

        with patch("sci.core.config._git_config_value", side_effect=mock_git):
            resolved = resolve_git_config(git)
        assert resolved.user_name == "Git User"
        assert resolved.user_email == "git@example.com"
        assert resolved.signing_key == "GITKEY"

    def test_empty_when_no_git_config(self) -> None:
        git = GitConfig()
        with patch("sci.core.config._git_config_value", return_value=""):
            resolved = resolve_git_config(git)
        assert resolved.user_name == ""
        assert resolved.user_email == ""
        assert resolved.signing_key == ""


class TestResolveSettings:
    """Tests for full settings resolution."""

    def test_resolve_settings_returns_new_instance(self) -> None:
        settings = GlobalSettings()
        with patch("sci.core.config._git_config_value", return_value=""):
            resolved = resolve_settings(settings)
        assert resolved is not settings

    def test_resolve_settings_integrates_all(self) -> None:
        settings = GlobalSettings(
            git=GitConfig(user_name="Config Name"),
            agent=AgentSettings(
                llm=LLMProviderConfig(provider="openai", model="gpt-4o")
            ),
        )
        env = {"SCI_LLM_API_KEY": "test-key"}
        with (
            patch.dict(os.environ, env, clear=False),
            patch("sci.core.config._git_config_value", return_value=""),
        ):
            resolved = resolve_settings(settings)
        assert resolved.agent.llm.provider == "openai"
        assert resolved.agent.llm.api_key == "test-key"
        assert resolved.agent.llm.model == "gpt-4o"
        assert resolved.git.user_name == "Config Name"

    def test_non_agent_settings_preserved(self) -> None:
        from sci.models.scholar import CLISettings, CLITheme

        settings = GlobalSettings(cli=CLISettings(theme=CLITheme.LIGHT))
        with patch("sci.core.config._git_config_value", return_value=""):
            resolved = resolve_settings(settings)
        assert resolved.cli.theme == CLITheme.LIGHT
