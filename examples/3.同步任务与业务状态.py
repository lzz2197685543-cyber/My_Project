from ecommerce_automation import TaskOutcome
from ecommerce_automation.errors import PermanentError
from ecommerce_automation.tasks import SQLiteTaskStore, TaskRunner
from pathlib import Path
from ecommerce_automation import ProjectPaths,RunContext

paths = ProjectPaths(Path(__file__).resolve().parent / 'new_project')

store = SQLiteTaskStore(paths.data / "tasks.sqlite3")
store.initialize()
store.enqueue(
    "inventory_sync_v1", "inventory:shop1:sku1:v1",
    {"sku": "sku1", "quantity": 18}, business_state="normalized",
)

def handle(task):
    if task.payload["quantity"] < 0:
        raise PermanentError("库存不能为负数")
    return TaskOutcome.success(
        {"sku": task.payload["sku"], "quantity": task.payload["quantity"]},
        business_state="synced", operation_id=f"stock:{task.key}", remote_id="platform-request-1",
    )

with RunContext("catalog", paths.logs) as run:
    summary = TaskRunner(store, logger=run.logger).run("inventory_sync_v1", handle, limit=100)
