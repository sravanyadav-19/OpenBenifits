from flask import Flask

from .config import DevConfig
from .services.rules_service import RulesService


def create_app(config_object=DevConfig) -> Flask:
    """
    Application factory.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Load config
    if isinstance(config_object, str):
        app.config.from_object(config_object)
    else:
        app.config.from_object(config_object)

    # Core services — reads from DynamoDB if USE_DYNAMODB=true, else
    # falls back to the local JSON file (used for local development).
    if app.config.get("USE_DYNAMODB"):
        app.extensions["rules_service"] = RulesService(
            dynamodb_table=app.config["DYNAMODB_TABLE_NAME"],
            aws_region=app.config["AWS_REGION"],
        )
    else:
        app.extensions["rules_service"] = RulesService(
            rules_path=app.config["RULES_FILE_PATH"]
        )

    # Register blueprints
    from .routes.web import web_bp
    from .routes.api import api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app