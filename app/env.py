"""Environment-file loading helpers for local development."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_env_files() -> None:
    """Load local env files with shell vars highest, then .env.local, then .env."""
    project_root = Path(__file__).resolve().parent.parent
    for filename in (".env.local", ".env"):
        env_path = project_root / filename
        if env_path.exists():
            load_dotenv(env_path, override=False)
