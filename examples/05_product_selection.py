import json
from pathlib import Path

from ecommerce_automation import ProjectPaths, RunContext, TaskOutcome
from ecommerce_automation.tasks import SQLiteTaskStore, TaskRunner


def export_selection(task):
    candidates = task.payload["candidates"]
    selected = [item for item in candidates if item["sales_30d"] >= 100 and item["margin"] >= 0.25]
    return TaskOutcome.success(
        {"selected": selected, "count": len(selected)},
        business_state="exported",
        operation_id=f"selection:{task.key}",
    )


def main():
    paths = ProjectPaths(Path(__file__).resolve().parent / "selection_demo")
    paths.ensure_runtime()
    store = SQLiteTaskStore(paths.data / "tasks.sqlite3")
    store.initialize()
    key = "seller_sprite:2026-10-13:shop_demo"
    payload = {"candidates": [
        {"sku": "A", "sales_30d": 180, "margin": 0.31},
        {"sku": "B", "sales_30d": 40, "margin": 0.45},
    ]}
    store.enqueue("selection_export_v1", key, payload, business_state="filtered")
    with RunContext("selection_demo", paths.logs) as run:
        TaskRunner(store, logger=run.logger).run("selection_export_v1", export_selection)
        task = store.get("selection_export_v1", key)
        output = paths.data / "selected.json"
        output.write_text(json.dumps(task.result, ensure_ascii=False, indent=2), encoding="utf-8")
        run.logger.info("selection_exported path=%s count=%s", output, task.result["count"])


if __name__ == "__main__":
    main()
