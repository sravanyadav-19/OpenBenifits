from __future__ import annotations

import os
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    BASE_DIR = BASE_DIR
    RULES_FILE_PATH = BASE_DIR / "rules" / "schemes.v1.json"


class DevConfig(BaseConfig):
    DEBUG = True