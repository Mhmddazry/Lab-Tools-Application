"""Composition root: wire the presentation, business, and data layers."""

import os
from pathlib import Path

from flask import Flask  # pyright: ignore[reportMissingImports]

from business_logic.services import EquipmentService, LoanService
from data_access.database import Database
from data_access.repositories import EquipmentRepository, LoanRepository
from presentation.routes import create_blueprint


PROJECT_DIR = Path(__file__).resolve().parent


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "local-demo-secret-key"),
        DATABASE=os.environ.get(
            "LAB_DATABASE_PATH", str(PROJECT_DIR / "instance" / "laboratorium.sqlite3")
        ),
    )
    if test_config:
        app.config.update(test_config)

    database = Database(app.config["DATABASE"])
    database.initialize()

    equipment_repository = EquipmentRepository(database)
    loan_repository = LoanRepository(database)
    equipment_service = EquipmentService(equipment_repository)
    loan_service = LoanService(loan_repository, equipment_repository)

    app.register_blueprint(create_blueprint(equipment_service, loan_service))

    @app.cli.command("init-db")
    def init_db_command():
        """Create any database tables that do not exist yet."""
        database.initialize()
        print(f"Database siap: {app.config['DATABASE']}")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
