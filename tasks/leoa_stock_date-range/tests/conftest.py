import pytest
from flask.testing import FlaskClient

from stockapp import create_app


@pytest.fixture
def client() -> FlaskClient:
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
