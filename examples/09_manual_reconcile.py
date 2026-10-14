from pathlib import Path

from ecommerce_automation import ProjectPaths, RunContext
from ecommerce_automation.tasks import SQLiteTaskStore, TaskStatus
from ecommerce_automation.workflow import TaskOutcome


def main():
    paths = ProjectPaths(Path(__file__).resolve().parent / "reconcile_demo")
    paths.ensure_runtime()
    store = SQLiteTaskStore(paths.data / "tasks.sqlite3")
    store.initialize()
    key = "inventory:shop_demo:SKU-001:v2"
    store.enqueue("inventory_sync_v2", key, {"sku": "SKU-001", "quantity": 18})
    task = store.claim("inventory_sync_v2", "worker-demo", lease_seconds=1)
    store.finish(task, TaskStatus.NEED_MANUAL, error="request timeout; remote result unknown",
                 business_state="sync_pending_confirmation", operation_id=f"stock:{key}")

    # 运维人员先到平台查询 SKU 的实际库存，确认远端已经同步后再写最终状态。
    manual_result = {"confirmed_quantity": 18, "checked_by": "operator"}
    store.resolve_manual(
        task.id, TaskStatus.SUCCEEDED, result=manual_result,
        business_state="synced", remote_id="remote-stock-001",
    )
    with RunContext("reconcile_demo", paths.logs) as run:
        resolved = store.get("inventory_sync_v2", key)
        run.logger.info("manual_resolved status=%s state=%s result=%s", resolved.status.value,
                        resolved.business_state, resolved.result)


if __name__ == "__main__":
    main()
