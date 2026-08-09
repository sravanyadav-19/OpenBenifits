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


def _get_client() -> genai.Client:
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(api_key=API_KEY)


# -------------------------------------------------------------------
# LOCAL RULE-BASED HELPERS (fallback when Gemini is unavailable)
# -------------------------------------------------------------------


def _local_scheme_explanation(user: UserProfile, scheme: Scheme) -> str:
    c = scheme.criteria
    parts: List[str] = []

    parts.append(
        "This scheme appears because your profile is close to the group it is "
        "designed for in this demo."
    )

    if c.min_age is not None or c.max_age is not None:
        if c.min_age is not None and c.max_age is not None:
            parts.append(
                f" Your age ({user.age}) is within the age band from "
                f"{c.min_age} to {c.max_age} years."
            )
        elif c.min_age is not None:
            parts.append(
                f" Your age ({user.age}) is at or above the minimum age of "
                f"{c.min_age} years."
            )
        elif c.max_age is not None:
            parts.append(
                f" Your age ({user.age}) is at or below the maximum age of "
                f"{c.max_age} years."
            )

    if c.employment_status_in:
        parts.append(
            " The scheme targets people who are "
            f"{', '.join(c.employment_status_in)}, and you indicated that you "
            f"are {user.employment_status}."
        )

    if c.max_income is not None:
        parts.append(
            f" Your annual household income ({user.income}) is at or below the "
            f"limit of {c.max_income} used in this demo."
        )

    if c.location_in:
        parts.append(
            " The scheme is available in "
            f"{', '.join(c.location_in)} areas, and you selected that you live "
            f"in a {user.location} area."
        )

    if not parts:
        parts.append(
            "Based on the rules in this demo, your answers are close enough to the "
            "scheme's basic target group for it to be shown."
        )

    return " ".join(parts)


def _find_scheme_by_name_in_question(
    question: str, schemes: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    q = question.lower()
    for s in schemes:
        name = (s.get("name") or "").lower()
        if name and name in q:
            return s
    if len(schemes) == 1:
        return schemes[0]
    return None


def _local_documents_answer(scheme: Dict[str, Any]) -> str:
    """
    Fallback answer for 'documents required' questions when Gemini is not available.
    """
    name = scheme.get("name", "this scheme")
    link = scheme.get("official_link", "")

    base = (
        f"For {name}, this demo does not store the exact list of documents. "
        "However, typical documents asked for many government schemes include:\n\n"
        "- Identity proof (Aadhaar, voter ID, PAN)\n"
        "- Address proof (ration card, electricity bill, Aadhaar)\n"
        "- Income certificate for the family (for income-based schemes)\n"
        "- Caste / community certificate (if the scheme is for specific groups)\n"
        "- Bank account details if money is transferred directly\n"
        "- Education/eligibility proof where relevant (mark sheets, certificates)\n"
    )

    if link:
        base += (
            f"\nPlease read the 'Documents required' section on the official page "
            f"({link}) for the final, up-to-date list."
        )
    else:
        base += "\nPlease check the official government portal for this scheme for the final list of documents."

    return base


def _local_general_answer(question: str, user: UserProfile, schemes: List[Dict[str, Any]]) -> str:
    """
    General local fallback for scheme-related questions when Gemini fails.
    """
    q = question.lower()

    if (
        "more schemes" in q
        or "not more schemes" in q
        or "only one scheme" in q
        or "only 1 scheme" in q
    ):
        count = len(schemes)
        if count == 0:
            base = "No schemes in this demo matched the basic rules for your profile."
        elif count == 1:
            base = "In this demo we found only one scheme that clearly fits your profile."
        else:
            base = f"In this demo we found {count} schemes that clearly fit your profile."

        return (
            f"{base}\n\n"
            "Why you may not see more:\n"
            "- This is a demo dataset, not the full government catalogue.\n"
            "- Some schemes have strict age, income or location conditions.\n"
            "- Many schemes apply only to specific groups.\n\n"
            "In a full system, more schemes and detailed rules can be added."
        )

    if "before applying" in q or "what should i check" in q or "check before" in q:
        return (
            "Before applying, you should:\n"
            "1) Read the official scheme page.\n"
            "2) Confirm age, income, location and status match the latest rules.\n"
            "3) Check deadlines and whether applications are open.\n"
            "4) Confirm the documents required.\n"
            "5) If unsure, ask a local office, helpline or school/college help desk.\n\n"
            "This demo provides guidance only; final eligibility is decided by the scheme owner."
        )

    # Default local guidance
    if schemes:
        names = ", ".join([s.get("name", "a scheme") for s in schemes])
        return (
            "I can help you understand the schemes shown on this page.\n\n"
            f"Matched schemes: {names}\n"
            "Try asking: \u201cExplain <scheme name>\u201d, \u201cWhy did this scheme appear?\u201d, "
            "or \u201cWhat documents are usually needed for this scheme?\u201d."
        )

    return (
        "I can help with government scheme guidance, but no schemes matched this profile "
        "in this demo ruleset. Please check official government portals for more schemes."
    )


# -------------------------------------------------------------------
# GEMINI-BASED FUNCTIONS
# -------------------------------------------------------------------


def generate_scheme_explanation(user: UserProfile, scheme: Scheme) -> Optional[str]:
    """
    Primary path: use Gemini to explain why the scheme appears.
    Fallback path: local rules-based explanation.
    """
    if not API_KEY:
        return _local_scheme_explanation(user, scheme)

    try:
        client = _get_client()
        prompt = f"""
You are helping a resident understand why a government scheme may be relevant.

Resident profile:
- Age: {user.age}
- Employment status: {user.employment_status}
- Annual household income: {user.income}
- Location type: {user.location}

Scheme:
- Name: {scheme.name}
- Description: {scheme.description}
- Criteria:
  - min_age: {scheme.criteria.min_age}
  - max_age: {scheme.criteria.max_age}
  - employment_status_in: {scheme.criteria.employment_status_in}
  - max_income: {scheme.criteria.max_income}
  - location_in: {scheme.criteria.location_in}

Write 2-3 short sentences in simple English.
Do NOT guarantee eligibility; advise checking the official link and latest rules.
"""
        resp = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        text = (resp.text or "").strip()
        return text if text else _local_scheme_explanation(user, scheme)
    except Exception:
        return _local_scheme_explanation(user, scheme)


def assistant_answer(
    question: str, user: UserProfile, schemes: List[Dict[str, Any]]
) -> str:
    """
    Assistant focused on **clarifying schemes**.

    - If the question is about documents for a scheme:
      -> ask Gemini to summarise required/likely documents.
    - If the question is about explaining a scheme or why it appeared:
      -> ask Gemini using the schemes JSON.
    - If Gemini fails or key is missing:
      -> use robust local fallbacks.
    """
    question = (question or "").strip()
    if not question:
        return "Please enter a question so I can help."

    # If there are no schemes, stay local
    if not schemes:
        return (
            "No schemes matched this profile in the demo ruleset, so I cannot "
            "answer scheme-specific questions. Please try changing your answers or "
            "check official portals for more schemes."
        )

    # Try to find the scheme the user is referring to
    target_scheme = _find_scheme_by_name_in_question(question, schemes) or schemes[0]

    # If Gemini is not configured, fully local
    if not API_KEY:
        # If user is clearly asking about documents
        q_low = question.lower()
        if "document" in q_low or "docs" in q_low or "certificate" in q_low:
            return _local_documents_answer(target_scheme)
        return _local_general_answer(question, user, schemes)

    # Gemini path
    try:
        client = _get_client()
        schemes_json = json.dumps(schemes or [], ensure_ascii=False, indent=2)
        q_low = question.lower()

        if "document" in q_low or "docs" in q_low or "certificate" in q_low:
            # Documents-focused prompt
            prompt = f"""
You are OpenBenefits assistant helping Indian residents understand a government scheme.

Resident profile:
- Age: {user.age}
- Employment status: {user.employment_status}
- Annual household income: {user.income}
- Location type: {user.location}

Matched schemes JSON:
{schemes_json}

The resident asks about **documents required** for this scheme:
\"\"\"{question}\"\"\"


Instructions:
- Identify which scheme they most likely mean from the JSON.
- Provide a short list of typical documents required for that scheme
  (for example: ID proof, address proof, income certificate, caste certificate,
  bank details, education proof).
- If you are not sure about exact rules, say "exact list may vary by state/
  latest guidelines" and recommend checking the official site.
- Write in simple English suitable for students and parents.
"""
        else:
            # General scheme clarification prompt (explain, why appears, etc.)
            prompt = f"""
You are OpenBenefits assistant helping Indian residents understand government schemes.

Resident profile:
- Age: {user.age}
- Employment status: {user.employment_status}
- Annual household income: {user.income}
- Location type: {user.location}

Matched schemes JSON:
{schemes_json}

User question:
\"\"\"{question}\"\"\"


Instructions:
- Use the JSON as your main source for scheme names and descriptions.
- If the question is about a specific scheme, focus on that scheme by name.
- Explain in simple English; keep answer short and practical.
- Do NOT guarantee final eligibility; advise checking the official website if relevant.
"""

        resp = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        text = (resp.text or "").strip()
        if not text:
            # Fallback if Gemini returns empty
            if "document" in question.lower() or "docs" in question.lower():
                return _local_documents_answer(target_scheme)
            return _local_general_answer(question, user, schemes)
        return text

    except Exception:
        # If Gemini call fails (quota/timeout), use local fallbacks
        if "document" in question.lower() or "docs" in question.lower():
            return _local_documents_answer(target_scheme)
        return _local_general_answer(question, user, schemes)