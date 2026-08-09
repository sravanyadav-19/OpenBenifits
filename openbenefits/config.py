from __future__ import annotations

import os
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    BASE_DIR = BASE_DIR
    RULES_FILE_PATH = BASE_DIR / "rules" / "schemes.v1.json"

    # When USE_DYNAMODB=true (set as an env var on EC2), the app reads
    # scheme data from DynamoDB instead of the local JSON file.
    USE_DYNAMODB = os.getenv("USE_DYNAMODB", "false").lower() == "true"
    DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "Schemes")
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")


class DevConfig(BaseConfig):
    DEBUG = True