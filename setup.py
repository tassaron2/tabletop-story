from setuptools import setup

setup(
    name="Tabletop Story",
    version="20.11.02",  # year.month.day
    packages=["tabletop_story", "tabletop_story.blueprints"],
    package_dir={
        "tabletop_story": "app",
        "tabletop_story.blueprints": "app/blueprints",
    },
    include_package_data=True,
    install_requires=[
        "uwsgi",
        "flask",
        "flask-bcrypt",
        "flask-login",
        "flask-sqlalchemy",
        "flask_wtf",
        "flask_migrate",
        # "flask_monitoringdashboard",
        "email_validator",
        "is_safe_url",
        "mistune==2.0.0a5",
        "python-dotenv",
        "dnd_character",
    ],
)
