"""Stock chart viewer: a small Flask app used as the target codebase for agent evals."""

from __future__ import annotations

from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    from stockapp.routes import bp

    app.register_blueprint(bp)
    return app
