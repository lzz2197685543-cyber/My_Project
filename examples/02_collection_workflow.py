from pathlib import Path

from ecommerce_automation import ProjectPaths, RunContext, TaskOutcome
from ecommerce_automation.tasks import SQLiteTaskStore, TaskRunner


def collect_one(task):
    source = task.payload["source"]
    # 真实项目在这里调用 1688/Temu/聚水潭/平台接口并做字段清洗。
    products = [{"source": source, "sku": f"{source}-001", "title": "示例商品"}]
    return TaskOutcome.success(
        {"items": products, "count": len(products)},
        business_state="collected",
        operation_id=f"collect:{task.key}",
    )


def main():
    paths = ProjectPaths(Path(__file__).resolve().parent / "collection_demo")
    paths.ensure_runtime()
    store = SQLiteTaskStore(paths.data / "tasks.sqlite3")
    store.initialize()
    store.enqueue("collect_products_v1", "1688:shop_demo:2026-10-13", {"source": "1688"})
    with RunContext("collection_demo", paths.logs) as run:
        summary = TaskRunner(store, logger=run.logger).run("collect_products_v1", collect_one)
        task = store.get("collect_products_v1", "1688:shop_demo:2026-10-13")
        run.logger.info("summary=%s business_state=%s result=%s", summary.as_dict(), task.business_state, task.result)


if __name__ == "__main__":
    main()
