"""Process entry point kept for backwards-compatible ``python app.py`` runs."""

from api import app, create_app

# Preserve the objects exposed by the previous entrypoint for integrations
# that imported them directly.
repository = app.extensions["library_repository"]
service = app.extensions["soap_service"]

__all__ = ["app", "create_app", "repository", "service"]


if __name__ == "__main__":
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
    )
