"""Offline example: keep the normal project flow simple and readable."""

from pathlib import Path

from ecommerce_automation import ProjectPaths, RunContext, load_json

from services.prepare import collect_products, prepare_products, save_products


def main() -> int:
    root = Path(__file__).resolve().parent
    config = load_json(root / "config" / "business.json")
    paths = ProjectPaths(root)
    paths.ensure_runtime()
    with RunContext(config["project"], paths.logs) as run:
        products = collect_products(config["products"])
        run.logger.info("collected=%s", len(products))
        prepared = prepare_products(products)
        run.logger.info("prepared=%s", len(prepared))
        saved = save_products(paths.data / "prepared.json", prepared)
        run.logger.info("saved=%s", saved)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
