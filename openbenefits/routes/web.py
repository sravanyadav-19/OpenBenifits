from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    redirect,
    url_for,
)

from ..models.user_profile import UserProfile
from ..services.eligibility_service import find_eligible_schemes
from ..services.rules_service import RulesService
from ..services.gemini_service import generate_scheme_explanation

web_bp = Blueprint("web", __name__)


@web_bp.route("/", methods=["GET"])
def index():
    """Landing page."""
    return render_template("index.html")


@web_bp.route("/questions", methods=["GET"])
def questions():
    """Step 1 – collect basic profile information."""
    return render_template("questions.html")


@web_bp.route("/results", methods=["GET", "POST"])
def results():
    """
    Step 2 – show matching schemes and AI explanations.

    - POST: normal flow from /questions form.
    - GET: direct access → redirect to /questions.
    """
    if request.method == "GET":
        return redirect(url_for("web.questions"))

    form = request.form

    user = UserProfile(
        age=int(form.get("age", 0)),
        employment_status=form.get("employment_status", "").strip(),
        income=int(form.get("income", 0)),
        location=form.get("location", "").strip(),
    )

    rules_service: RulesService = current_app.extensions["rules_service"]
    schemes = find_eligible_schemes(user, rules_service.schemes)

    explanations = {}
    for scheme in schemes:
        exp = generate_scheme_explanation(user, scheme)
        if exp:
            explanations[scheme.id] = exp

    schemes_json = [s.to_dict() for s in schemes]

    return render_template(
        "results.html",
        user=user,
        schemes=schemes,
        explanations=explanations,
        schemes_json=schemes_json,
    )