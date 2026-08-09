import os
import json
from typing import Optional, List, Dict, Any

from google import genai

from ..models.scheme import Scheme
from ..models.user_profile import UserProfile


def _get_gemini_api_key() -> Optional[str]:
    """
    Fetch the Gemini API key from AWS Secrets Manager if GEMINI_SECRET_NAME
    is set (used on EC2). Falls back to the GEMINI_API_KEY environment
    variable directly (used for local development, unchanged behavior).
    """
    secret_name = os.getenv("GEMINI_SECRET_NAME")
    if secret_name:
        try:
            import boto3

            region = os.getenv("AWS_REGION", "ap-south-1")
            client = boto3.client("secretsmanager", region_name=region)
            resp = client.get_secret_value(SecretId=secret_name)
            secret_string = resp.get("SecretString", "")
            try:
                secret_dict = json.loads(secret_string)
                return secret_dict.get("GEMINI_API_KEY", secret_string)
            except json.JSONDecodeError:
                # Secret was stored as a plain string, not JSON
                return secret_string
        except Exception:
            # If Secrets Manager fetch fails for any reason, fall through
            # to the env var below rather than crashing app startup.
            pass
    return os.getenv("GEMINI_API_KEY")


API_KEY = _get_gemini_api_key()
MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")


# -------------------------------------------------------------------
# Everything below this line is UNCHANGED from your current file.
# Keep _get_client() and every function after it exactly as they are —
# only the API_KEY/MODEL_NAME assignment above needs to be swapped in.
# -------------------------------------------------------------------