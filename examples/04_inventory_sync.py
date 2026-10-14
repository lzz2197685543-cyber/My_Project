from pathlib import Path

from ecommerce_automation import ProjectPaths, RunContext, TaskOutcome
from ecommerce_automation.errors import OutcomeUnknown
from ecommerce_automation.tasks import SQLiteTaskStore, TaskRunner


def sync_stock(task):
    sku = task.payload["sku"]
    quantity = task.payload["quantity"]
    # 真正的 POST/PATCH 需要传 idempotency_key，并使用平台的查询接口确认结果。
    idempotency_key = f"stock:{task.key}"
    platform_response = {"accepted": True, "request_id": f"req-{sku}"}
    if not platform_response.get("accepted"):
        raise OutcomeUnknown("库存请求结果不明确，先查询平台库存")
    return TaskOutcome.success(
        {"sku": sku, "quantity": quantity, "request": platform_response},
        business_state="synced",
        operation_id=idempotency_key,
        remote_id=platform_response["request_id"],
    )


def main():
    paths = ProjectPaths(Path(__file__).resolve().parent / "inventory_demo")
    paths.ensure_runtime()
    store = SQLiteTaskStore(paths.data / "tasks.sqlite3")
    store.initialize()
    key = "temu:shop_demo:SKU-001:v2"
    store.enqueue("inventory_sync_v2", key, {"sku": "SKU-001", "quantity": 18},
                  business_state="normalized", operation_id=f"stock:{key}")
    with RunContext("inventory_demo", paths.logs) as run:
        TaskRunner(store, logger=run.logger).run("inventory_sync_v2", sync_stock)
        task = store.get("inventory_sync_v2", key)
        run.logger.info("inventory_status=%s remote_id=%s", task.business_state, task.remote_id)


if __name__ == "__main__":
    main()
