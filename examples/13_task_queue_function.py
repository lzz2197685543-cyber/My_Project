"""Persistent queue through a function; handler receives an ordinary dict."""

from pathlib import Path

from ecommerce_automation.tasks import run_tasks


def prepare_product(product):
    title = " ".join(product.get("title", "").split())
    if not title:
        raise ValueError(f"Missing title for {product.get('sku', '?')}")
    return {"sku": product["sku"], "title": title}


def main():
    products = [
        {"sku": "DEMO-001", "title": " 儿童  积木玩具 "},
        {"sku": "DEMO-002", "title": "木制 拼图"},
    ]
    summary = run_tasks(
        products,
        prepare_product,
        db_path=Path(__file__).resolve().parent / "task_demo" / "data" / "tasks.sqlite3",
        key="sku",
        queue="prepare_products",
    )
    print(summary)


if __name__ == "__main__":
    main()
