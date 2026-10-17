from pathlib import Path
from ecommerce_automation import ProjectPaths, Settings, load_json

paths = ProjectPaths(Path(__file__).resolve().parent / 'new_project')

settings = Settings.load(env_file=paths.config / ".env")

business = load_json(paths.config / "business.json")
print(business)
database = settings.require("DB_PASSWORD")
port = settings.integer("DB_PORT", 3306, minimum=1)

print(database)
print(port)