from pathlib import Path

from ecommerce_automation import ProjectPaths, RunContext, TaskOutcome
from ecommerce_automation.tasks import SQLiteTaskStore, TaskRunner


def reconcile_month(task):
    month = task.payload["month"]
    # 真实项目会下载结算单、订单、退款、费用，再按订单号/SKU/店铺匹配。
    matched = 1280
    unmatched = 3
    if unmatched:
        # 也可以返回 succeeded，同时把“存在未匹配行”作为业务结果交给审核阶段。
        return TaskOutcome.success(
            {"month": month, "matched": matched, "unmatched": unmatched},
            business_state="reconciled_with_exceptions",
            remote_id=f"report:{month}:shop_demo",
        )
    return TaskOutcome.success(
        {"month": month, "matched": matched, "unmatched": 0},
        business_state="reconciled",
    )


def main():
    paths = ProjectPaths(Path(__file__).resolve().parent / "finance_demo")
    paths.ensure_runtime()
    store = SQLiteTaskStore(paths.data / "tasks.sqlite3")
    store.initialize()
    key = "temu:shop_demo:2026-10"
    store.enqueue("finance_reconcile_v1", key, {"month": "2026-10", "platform": "temu"},
                  business_state="downloaded")
    with RunContext("finance_demo", paths.logs) as run:
        TaskRunner(store, logger=run.logger).run("finance_reconcile_v1", reconcile_month)
        task = store.get("finance_reconcile_v1", key)
        run.logger.info("finance_status=%s result=%s", task.business_state, task.result)


if __name__ == "__main__":
    main()
