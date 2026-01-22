import dataclasses
import logging
import os
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any
from typing import cast

import yaml

from standup_report.exceptions import SettingsError

logger = logging.getLogger(__name__)

_CONFIG_FILE_NAME = "config.yml"

_GOOGLE_CREDENTIALS_FILE = "credentials.json"
_GOOGLE_TOKEN_FILE = "google_token.json"


@dataclass
class GoogleSettings:
    IGNORED_CALENDARS: set[str]  # calendar title(summary)
    IGNORED_MEETINGS: set[str]  # event title(summary)

    @property
    def CREDENTIALS_FILE_NAME(self) -> str:
        return _GOOGLE_CREDENTIALS_FILE

    @property
    def TOKEN_FILE_NAME(self) -> str:
        return _GOOGLE_TOKEN_FILE

    @property
    def HAS_CREDENTIALS(self) -> bool:
        return os.path.exists(self.CREDENTIALS_FILE_NAME)

    @property
    def HAS_TOKEN(self) -> bool:
        return os.path.exists(self.TOKEN_FILE_NAME)

    @property
    def is_setup(self) -> bool:
        return bool(self.HAS_CREDENTIALS and self.HAS_TOKEN)


@dataclass
class Settings:
    GH_LOGIN: str
    GH_TOKEN: str
    GH_USERNAME: str
    LINEAR_TOKEN: str
    LINEAR_EMAIL: str
    IGNORED_REPOS: set[str]
    GOOGLE: GoogleSettings

    @property
    def as_dict(self) -> dict[str, str | int | list[str]]:
        # Exclude google from the dict display (it's optional and has its own UI)
        d = dataclasses.asdict(self)
        # d.pop("GOOGLE", None)
        return d

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
    required_env_vars: dict[str, str | None] = {
        "GH_LOGIN": os.getenv("GH_LOGIN"),
        "GH_API_TOKEN": os.getenv("GH_API_TOKEN"),
        "GH_USERNAME": os.getenv(
            "GH_USERNAME"
        ),  # this could be the same as GH_LOGIN or it can not be
        "LINEAR_TOKEN": os.getenv("LINEAR_TOKEN"),
        "LINEAR_EMAIL": os.getenv("LINEAR_EMAIL"),
    }
    if missing_vars := [name for name, value in required_env_vars.items() if not value]:
        raise SettingsError(
            f"Missing environment variable(s): {', '.join(missing_vars)}."
        )
    env_vars: dict[str, str] = cast(dict[str, str], required_env_vars)

    config = _load_yaml_config()

    ignored_repos = config.get("ignored_repos", [])
    ignored_calendars: list[str] = config.get("ignored_calendars", [])
    ignored_meetings: list[str] = config.get("ignored_meetings", [])

    return Settings(
        GH_LOGIN=env_vars["GH_LOGIN"],
        GH_TOKEN=env_vars["GH_API_TOKEN"],
        GH_USERNAME=env_vars["GH_USERNAME"],
        LINEAR_TOKEN=env_vars["LINEAR_TOKEN"],
        LINEAR_EMAIL=env_vars["LINEAR_EMAIL"],
        IGNORED_REPOS=set(ignored_repos),
        GOOGLE=GoogleSettings(
            IGNORED_CALENDARS=set(ignored_calendars),
            IGNORED_MEETINGS=set(ignored_meetings),
        ),
    )
