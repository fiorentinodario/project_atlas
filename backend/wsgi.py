import os

from project_atlas import create_app

app = create_app(os.getenv("APP_ENV", "development"))
