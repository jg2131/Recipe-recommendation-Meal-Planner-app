from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create a shared SQLAlchemy database object
db = SQLAlchemy()

import os

def create_app():
    """Initialize and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration settings (database URI, secret key, etc.)
    app.config.from_object('config.Config')

    # Initialize Flask extensions
    db.init_app(app)

    # Perform setup that requires the application context
    with app.app_context():
        # Register custom Jinja utilities and filters
        try:
            from .utilities import ingredient_with_emoji
            # Make the utility available in templates as a Jinja filter
            # Example usage: {{ ingredient_name | ingredient_emoji }}
            app.jinja_env.filters['ingredient_emoji'] = ingredient_with_emoji
        except Exception:
            # If the utility cannot be imported, continue without breaking the app
            pass

        # Import all route blueprints used by the application
        from .home.home import home
        from .meals.add import add
        from .meals.edit import edit
        from .meals.list_meals import list_meals
        from .meals.find import find
        from .meals.inspire import inspire
        from .meals.search import search
        from .meal_plans.create import create
        from .meal_plans.display import display
        from .meal_plans.load import load
        from .meal_plans.delete import delete

        # Register each blueprint with the Flask app
        app.register_blueprint(home)
        app.register_blueprint(add)
        app.register_blueprint(edit)
        app.register_blueprint(list_meals)
        app.register_blueprint(find)
        app.register_blueprint(inspire)
        app.register_blueprint(search)
        app.register_blueprint(create)
        app.register_blueprint(display)
        app.register_blueprint(load)
        app.register_blueprint(delete)

        # Return the fully configured Flask application
        return app
