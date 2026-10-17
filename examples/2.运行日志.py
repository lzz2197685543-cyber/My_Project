from ecommerce_automation import RunContext
from pathlib import Path
from ecommerce_automation import ProjectPaths, Settings, load_json

paths = ProjectPaths(Path(__file__).resolve().parent / 'new_project')
settings = Settings.load(env_file=paths.config / ".env")

with RunContext("temu_project", paths.logs, secrets=[settings.require("API_KEY")]) as run:
    logger = run.logger.bind(stage="publish", shop="shop_01")
    logger.info("prepared_count=%s", 25)