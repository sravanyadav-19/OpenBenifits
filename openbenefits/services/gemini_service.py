"""
Local explanation and assistant service.

This version does NOT call Google APIs at runtime. It uses the scheme rules
and user profile to generate clear, rule-based explanations.

The interface (generate_scheme_explanation, assistant_answer) is compatible
with earlier Gemini-based designs, so a real model can be plugged in later
if API access becomes available.
"""

from typing import Optional, List, Dict, Any

from ..models.scheme import Scheme
from ..models.user_profile import UserProfile


# ---------- Per-scheme explanation (used under each card) ----------


def generate_scheme_explanation(user: UserProfile, scheme: Scheme) -> Optional[str]:
    """
    Generate a simple, local explanation of why this scheme may be relevant
    for the user, based on the encoded rules.
    """
    c = scheme.criteria
    parts: List[str] = []

    parts.append(
        "This scheme appears because your profile is close to the group it is "
        "designed for."
    )

    # Age
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

    # Employment status
    if c.employment_status_in:
        parts.append(
            " The scheme targets people who are "
            f"{', '.join(c.employment_status_in)}, and you indicated that you "
            f"are {user.employment_status}."
        )

    # Income
    if c.max_income is not None:
        parts.append(
            f" Your annual household income ({user.income}) is at or below the "
            f"limit of {c.max_income} used in this demo."
        )

    # Location
    if c.location_in:
        parts.append(
            " The scheme is available in "
            f"{', '.join(c.location_in)} areas, and you selected that you live "
            f"in a {user.location} area."
        )

    if not parts:
        parts.append(
            "Based on the rules in this demo, your answers are close enough to the "
            "scheme’s basic target group for it to be shown."
        )

    return " ".join(parts)


# ---------- Helper: find scheme mentioned by name in the question ----------


def _find_scheme_by_name_in_question(
    question: str, schemes: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    q = question.lower()
    best_match = None
    for s in schemes:
        name = (s.get("name") or "").lower()
        if name and name in q:
            best_match = s
            break
    if best_match:
        return best_match
    if len(schemes) == 1:
        return schemes[0]
    return None


# ---------- Assistant Q&A (Ask OpenBenefits) ----------


def assistant_answer(
    question: str, user: UserProfile, schemes: List[Dict[str, Any]]
) -> str:
    """
    Local assistant: answers common questions using the schemes JSON and
    the user profile, without calling external APIs.

    Patterns handled include:
    - "Why are there not more schemes for me?"
    - "Why did this scheme appear?"
    - "Explain / tell me about <scheme>"
    - "Who can apply / am I eligible / do I qualify?"
    - "What should I check before applying?"
    - "How do I apply / where do I apply?"
    - "What documents do I need?"
    - "How much money / what benefit does this give?"
    - "Can I apply for more than one scheme?"
    - "Which schemes did you find / list the schemes"
    """
    question = (question or "").strip()
    if not question:
        return "Please enter a question so I can help."

    q = question.lower()

    # ---------- 1) Why not more schemes? ----------
    if (
        "more schemes" in q
        or "not more schemes" in q
        or "only one scheme" in q
        or "only 1 scheme" in q
    ):
        count = len(schemes)
        if count == 0:
            base = (
                "No schemes in this demo matched the basic rules for your profile."
            )
        elif count == 1:
            base = (
                "In this demo dataset we found only one scheme that clearly fits the "
                "basic rules for your profile."
            )
        else:
            base = (
                f"In this demo dataset we found {count} schemes that clearly fit the "
                "basic rules for your profile."
            )

        return (
            f"{base} There are a few reasons why you may not see more:\n\n"
            "- This is a demonstration with only a small number of schemes loaded, "
            "not the full list used by government.\n"
            "- Some schemes have strict age, income or location limits, so they may "
            "not match the information you entered.\n"
            "- Certain schemes are designed for very specific groups (for example, "
            "particular categories of students or workers).\n\n"
            "In a real system, more departments and schemes could be added. You can "
            "also check the official government portals for additional programmes "
            "that may not be included in this demo."
        )

    # ---------- 2) What to check before applying ----------
    if "before applying" in q or "what should i check" in q or "check before" in q:
        return (
            "Before applying for any scheme, it is a good idea to:\n\n"
            "1. Read the official scheme page carefully, especially the 'Eligibility' "
            "and 'Documents required' sections.\n"
            "2. Confirm that your age, income, location and work or study status match "
            "the latest rules.\n"
            "3. Check the application dates, last date for submission and whether the "
            "scheme is currently open.\n"
            "4. Collect supporting documents such as ID proof, address proof, income "
            "certificate, mark sheets or bank details, as listed on the official site.\n"
            "5. If you are unsure, speak to a helpline, school/college office or "
            "local government office before submitting.\n\n"
            "The matches shown here are a starting point only. The final decision "
            "always rests with the department that runs the scheme."
        )

    # ---------- 3) Why did this scheme appear? ----------
    if (
        "why did this scheme" in q
        or "why this scheme" in q
        or "why did this appear" in q
        or "why did the scheme appear" in q
        or "why did this come up" in q
    ):
        if not schemes:
            return (
                "A scheme appears in your results when your age, income, location and "
                "work or study status are reasonably close to the scheme’s target "
                "group. You can see a more detailed breakdown under “Why this scheme "
                "is shown” on the card."
            )

        s = schemes[0]
        c = s.get("criteria") or {}
        lines: List[str] = []
        lines.append(
            "This scheme appears in your results because your answers match one or "
            "more of its key eligibility rules."
        )

        min_age = c.get("min_age")
        max_age = c.get("max_age")
        if min_age is not None or max_age is not None:
            if min_age is not None and max_age is not None:
                lines.append(
                    f"- Your age ({user.age}) is within the age band from "
                    f"{min_age} to {max_age} years."
                )
            elif min_age is not None:
                lines.append(
                    f"- Your age ({user.age}) is at or above the minimum age of "
                    f"{min_age} years."
                )
            elif max_age is not None:
                lines.append(
                    f"- Your age ({user.age}) is at or below the maximum age of "
                    f"{max_age} years."
                )

        allowed_status = c.get("employment_status_in")
        if allowed_status:
            lines.append(
                "- The scheme is designed for "
                f"{', '.join(allowed_status)}, and you indicated that you are "
                f"{user.employment_status}."
            )

        max_income = c.get("max_income")
        if max_income is not None:
            lines.append(
                "- Your annual household income "
                f"({user.income}) is at or below the current income limit of "
                f"{max_income} used in this demo."
            )

        loc_in = c.get("location_in")
        if loc_in:
            lines.append(
                "- The scheme is available in "
                f"{', '.join(loc_in)}, and you selected that you live in a "
                f"{user.location} area."
            )

        if len(lines) == 1:
            lines.append(
                "- Based on the rules in this demo, your answers are close enough to "
                "the scheme’s target group for it to be shown."
            )

        lines.append(
            "\nIf you expand “Why this scheme is shown” on the scheme card, you can "
            "see the same information in more detail."
        )

        return "\n".join(lines)

    # ---------- 4) Explain / tell me about <scheme> ----------
    if (
        "explain" in q
        or "tell me about" in q
        or "what is" in q
        or "details about" in q
    ):
        matched = _find_scheme_by_name_in_question(question, schemes)
        if matched:
            name = matched.get("name") or "this scheme"
            desc = matched.get("description") or ""
            c = matched.get("criteria") or {}
            min_age = c.get("min_age")
            max_age = c.get("max_age")
            allowed_status = c.get("employment_status_in")
            max_income = c.get("max_income")
            loc_in = c.get("location_in")

            lines: List[str] = []
            lines.append(f"{name} is a government scheme described as follows:")
            if desc:
                lines.append(f"\n- {desc}")

            details: List[str] = []
            if min_age is not None or max_age is not None:
                if min_age is not None and max_age is not None:
                    details.append(
                        f"Age: usually between {min_age} and {max_age} years."
                    )
                elif min_age is not None:
                    details.append(f"Age: from {min_age} years and above.")
                elif max_age is not None:
                    details.append(f"Age: up to {max_age} years.")

            if allowed_status:
                details.append(
                    "Target group: intended for "
                    f"{', '.join(allowed_status)}."
                )

            if max_income is not None:
                details.append(
                    f"Income: annual household income generally up to {max_income}."
                )

            if loc_in:
                details.append(
                    "Location: available in "
                    f"{', '.join(loc_in)} areas."
                )

            if details:
                lines.append("\nKey points from the basic rules in this demo:")
                for d in details:
                    lines.append(f"- {d}")

            link = matched.get("official_link")
            if link:
                lines.append(
                    f"\nFor full details, you should always read the official scheme "
                    f"page: {link}"
                )
            else:
                lines.append(
                    "\nFor full details, please read the official scheme page on the "
                    "relevant government portal."
                )

            return "\n".join(lines)

    # ---------- 5) Who can apply / am I eligible / do I qualify? ----------
    if (
        "who can apply" in q
        or "who is eligible" in q
        or "who can benefit" in q
        or "am i eligible" in q
        or "am i qualify" in q
        or "do i qualify" in q
        or ("eligible" in q and "i" in q)
    ):
        if not schemes:
            return (
                "In this demo, no schemes matched the basic rules for your profile. "
                "That does not mean you are ineligible for all real schemes. "
                "It only means that, for the small set of rules loaded here, "
                "none were a close match.\n\n"
                "To check eligibility in real life, please read the official "
                "eligibility section for each scheme and, if needed, speak to a "
                "helpline or local office."
            )

        names = ", ".join([s.get("name", "a scheme") for s in schemes])
        return (
            f"In this demo, your answers matched these schemes: {names}.\n\n"
            "This suggests that you may fit the basic age, income, location and "
            "work or study conditions for them. However, this tool cannot confirm "
            "final eligibility. The full rules may include additional conditions "
            "(such as category, marks, specific courses or other factors) that are "
            "not captured here.\n\n"
            "Please use this as a starting point and always check the official "
            "scheme website or office before applying."
        )

    # ---------- 6) How to apply / where to apply / application process ----------
    if (
        "how do i apply" in q
        or "how can i apply" in q
        or "application process" in q
        or "how to apply" in q
        or "where do i apply" in q
        or "where can i apply" in q
    ):
        matched = _find_scheme_by_name_in_question(question, schemes)
        if matched:
            name = matched.get("name", "this scheme")
            link = matched.get("official_link")
            base = f"For {name}, the exact application process is not stored in this demo."
            if link:
                return (
                    f"{base} You should:\n\n"
                    "1. Open the official scheme page (link shown on the card).\n"
                    "2. Look for sections such as 'How to Apply', 'Online Application' "
                    "or 'Application Process'.\n"
                    "3. Follow the steps given there. Many schemes now use online "
                    "portals, but some still allow offline forms through schools, "
                    "colleges or local offices.\n\n"
                    "If you find the process confusing, you can ask a teacher, "
                    "counsellor or local government office to guide you."
                )
            else:
                return (
                    f"{base} In general you should:\n\n"
                    "1. Search for the scheme name on the official government portal.\n"
                    "2. Look for 'How to Apply' or 'Application Process'.\n"
                    "3. If still unclear, visit a local office or helpline for support."
                )

        return (
            "The exact application process for each scheme is not stored in this demo. "
            "In general, you should:\n\n"
            "1. Open the official scheme page from a trusted government website.\n"
            "2. Read the 'How to Apply' or 'Application Process' section carefully.\n"
            "3. Follow the online steps, or submit forms through the school, college "
            "or local office if required.\n"
            "4. If needed, ask a teacher, counsellor or local office for help."
        )

    # ---------- 7) Documents required / what documents ----------
    if (
        "what documents" in q
        or "documents required" in q
        or "which documents" in q
        or "docs required" in q
        or "what do i need to submit" in q
        or "proof" in q
        or "certificate" in q
    ):
        return (
            "The exact list of documents is not stored in this demo. In many schemes, "
            "you may be asked for some of the following:\n\n"
            "- Identity proof (for example, Aadhaar card, voter ID, PAN).\n"
            "- Address proof (for example, ration card, electricity bill, Aadhaar).\n"
            "- Income certificate for the family.\n"
            "- Mark sheets or proof of education, if it is a student or education "
            "scheme.\n"
            "- Caste or community certificate, if the scheme is for a specific group.\n"
            "- Bank account details if money will be transferred directly.\n\n"
            "Please always check the 'Documents required' section on the official "
            "scheme website for the final list."
        )

    # ---------- 8) Benefit / amount / what do I get ----------
    if (
        "how much" in q
        or "amount" in q
        or "benefit" in q
        or "money" in q
        or "scholarship" in q and "amount" in q
        or "what will i get" in q
    ):
        matched = _find_scheme_by_name_in_question(question, schemes)
        if matched:
            name = matched.get("name", "this scheme")
            link = matched.get("official_link")
            base = (
                f"This demo does not store the exact money or benefit amounts for {name}."
            )
            if link:
                return (
                    f"{base} The amount can change over time and may depend on your "
                    "category, course or other factors.\n\n"
                    "Please open the official scheme page using the link shown on the "
                    "card and check the 'Benefits' or 'Amount' section for the latest "
                    "information."
                )
            else:
                return (
                    f"{base} The amount can change with policy updates. Please refer "
                    "to the official scheme website or local office for the latest "
                    "amounts and benefits."
                )

        return (
            "This demo does not store the exact money or benefit amounts for schemes. "
            "Amounts can change over time and may depend on your category, course or "
            "other factors.\n\n"
            "To know the current benefit, please open the official scheme page on a "
            "trusted government portal and read the 'Benefits' or 'Amount' section."
        )

    # ---------- 9) Can I apply for more than one scheme? ----------
    if (
        "more than one scheme" in q
        or "multiple schemes" in q
        or "apply for all schemes" in q
        or "two schemes" in q
        or "many schemes" in q
    ):
        return (
            "Whether you can receive benefits from more than one scheme at the same "
            "time depends on the rules of each scheme.\n\n"
            "- Some schemes allow you to apply even if you are already receiving "
            "benefits from another programme.\n"
            "- Other schemes may say that you cannot take two similar benefits at the "
            "same time (for example, two scholarships for the same course).\n\n"
            "You should always read the 'Conditions' section on the official scheme "
            "page or ask a local office. This demo cannot check those overlaps."
        )

    # ---------- 10) List schemes / which schemes did you find ----------
    if (
        "which schemes" in q
        or "what schemes" in q
        or "list the schemes" in q
        or "show the schemes" in q
    ):
        if not schemes:
            return (
                "In this demo, no schemes matched the basic rules for your profile. "
                "Please try changing your answers or check official portals for more "
                "schemes that may not be included here."
            )

        lines: List[str] = []
        lines.append("Based on your answers, these schemes were matched in this demo:")
        for s in schemes:
            name = s.get("name", "Unnamed scheme")
            desc = s.get("description", "")
            if desc:
                lines.append(f"- {name}: {desc}")
            else:
                lines.append(f"- {name}")
        lines.append(
            "\nYou can read more details on each card and open the official link for "
            "full information."
        )
        return "\n".join(lines)

    # ---------- 11) Generic fallback ----------
    if schemes:
        names = ", ".join([s.get("name", "a scheme") for s in schemes])
        return (
            "I can give only general guidance in this demo.\n\n"
            f"- Your answers matched these schemes: {names}.\n"
            "- You can read the short description on each card and open the official "
            "link for full information.\n"
            "- The “Why this scheme is shown” section on each card explains how your "
            "profile relates to the rules in this demo.\n\n"
            "If you have a very specific question, it is safest to check the official "
            "scheme website or speak to a trusted advisor."
        )

    return (
        "I do not have enough information in this demo to answer that question. "
        "Please check the official scheme portals or speak to a trusted advisor."
    )