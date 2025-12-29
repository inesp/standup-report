import dataclasses
import logging
import os
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import yaml

from standup_report.exceptions import SettingsError

logger = logging.getLogger(__name__)

_CONFIG_FILE_NAME = "config.yml"


@dataclass
class Settings:
    GH_LOGIN: str
    GH_TOKEN: str
    GH_USERNAME: str
    REPOSITORIES: list[tuple[str, str]]

    @property
    def as_dict(self) -> dict[str, str | int | list[str]]:
        return dataclasses.asdict(self)

    @property
    def CONFIG_FILE_NAME(self) -> str:
        return _CONFIG_FILE_NAME


def _load_yaml_config() -> dict[str, Any]:
    config_path = Path(_CONFIG_FILE_NAME)
    if not config_path.exists():
        logger.info(f"Config file not found: {_CONFIG_FILE_NAME}")
        return {}

    try:
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Could not load {_CONFIG_FILE_NAME}: {e}")
        return {}



@cache
def get_settings() -> Settings:
    gh_token = os.getenv("GH_API_TOKEN")
    gh_login = os.getenv("GH_LOGIN")
    gh_user_login = os.getenv("GH_USERNAME")  # this could be the same as GH_LOGIN or it can not be

    if not gh_token or not gh_login or not gh_user_login:
        raise SettingsError("GH_API_TOKEN and GH_LOGIN and GH_USERNAME must be set in .env")

    config = _load_yaml_config()

    raw_repos = config.get("repositories", [])
    repositories = [(one_repo["owner"], one_repo["name"]) for one_repo in raw_repos]

    return Settings(
        GH_LOGIN=gh_login,
        GH_TOKEN=gh_token,
        GH_USERNAME=gh_user_login,
        REPOSITORIES=repositories,
    )
