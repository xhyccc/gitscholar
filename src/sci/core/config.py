"""Configuration resolution — merges file settings with env vars and system defaults."""

from __future__ import annotations

import os
import subprocess

from sci.models.scholar import AgentSettings, GitConfig, GlobalSettings, LLMProviderConfig


def _git_config_value(key: str) -> str:
    """Read a value from git config, returning empty string on failure."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def resolve_llm_config(agent: AgentSettings) -> LLMProviderConfig:
    """Resolve the effective LLM configuration.

    Priority (highest to lowest):
      1. Explicit values in settings.yaml ``agent.llm.*``
      2. Environment variables (``SCI_LLM_*``)
      3. Legacy environment variable for API key (``CLAW_API_KEY``)
      4. Built-in defaults (model from ``agent.default_model``)
    """
    llm = agent.llm

    provider = (
        llm.provider
        or os.environ.get("SCI_LLM_PROVIDER", "")
    )
    api_key = (
        llm.api_key
        or os.environ.get("SCI_LLM_API_KEY", "")
        or os.environ.get(agent.api_key_env, "")
    )
    api_base = (
        llm.api_base
        or os.environ.get("SCI_LLM_API_BASE", "")
    )
    model = (
        llm.model
        or os.environ.get("SCI_LLM_MODEL", "")
        or agent.default_model
    )

    return LLMProviderConfig(
        provider=provider,
        api_key=api_key,
        api_base=api_base,
        model=model,
    )


def resolve_git_config(git: GitConfig) -> GitConfig:
    """Resolve the effective git configuration.

    Priority (highest to lowest):
      1. Explicit values in settings.yaml ``git.*``
      2. System git config (``git config --get``)
    """
    return GitConfig(
        user_name=git.user_name or _git_config_value("user.name"),
        user_email=git.user_email or _git_config_value("user.email"),
        signing_key=git.signing_key or _git_config_value("user.signingkey"),
    )


def resolve_settings(settings: GlobalSettings) -> GlobalSettings:
    """Return a copy of *settings* with all values resolved from env / git defaults."""
    resolved_llm = resolve_llm_config(settings.agent)
    resolved_git = resolve_git_config(settings.git)

    return settings.model_copy(
        update={
            "agent": settings.agent.model_copy(update={"llm": resolved_llm}),
            "git": resolved_git,
        }
    )
