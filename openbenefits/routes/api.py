from http import HTTPStatus

from flask import Blueprint, current_app, jsonify, request

from ..models.user_profile import UserProfile
from ..services.eligibility_service import find_eligible_schemes
from ..services.rules_service import RulesService
from ..services.gemini_service import assistant_answer

api_bp = Blueprint("api", __name__)


@api_bp.route("/rules", methods=["GET"])
def get_rules():
    """
    Return the current list of schemes and their criteria as JSON.
    """
    rules_service: RulesService = current_app.extensions["rules_service"]
    return jsonify({"schemes": rules_service.as_dict()})


@api_bp.route("/check", methods=["POST"])
def check():
    """
    Programmatic eligibility check.
    Body: { age, employment_status, income, location }
    """
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), HTTPStatus.BAD_REQUEST

    try:
        user = UserProfile(
            age=int(data.get("age", 0)),
            employment_status=str(data.get("employment_status", "")).strip(),
            income=int(data.get("income", 0)),
            location=str(data.get("location", "")).strip(),
        )
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid field types"}), HTTPStatus.BAD_REQUEST

    rules_service: RulesService = current_app.extensions["rules_service"]
    eligible = find_eligible_schemes(user, rules_service.schemes)

    return jsonify({"eligible_schemes": [s.to_dict() for s in eligible]})


@api_bp.route("/assistant", methods=["POST"])
def assistant():
    """
    Ask OpenBenefits (Gemini-powered) about the current profile and schemes.
    Body: { "question": "...", "user": {...}, "schemes": [...] }
    """
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()
    user_data = data.get("user") or {}
    schemes_data = data.get("schemes") or []

    if not question:
        return jsonify({"answer": "Please enter a question so I can help."})

    try:
        user = UserProfile(
            age=int(user_data.get("age", 0)),
            employment_status=str(user_data.get("employment_status", "")),
            income=int(user_data.get("income", 0)),
            location=str(user_data.get("location", "")),
        )
    except (TypeError, ValueError):
        return jsonify(
            {"answer": "I could not read your profile correctly. Please try again."}
        )

    answer = assistant_answer(question, user, schemes_data)
    return jsonify({"answer": answer})