import json
from pathlib import Path


def collect_products(products: list[dict]) -> list[dict]:
    return list(products)


def prepare_products(products: list[dict]) -> list[dict]:
    prepared = []
    for product in products:
        title = " ".join(product.get("title", "").split())
        if not title:
            raise ValueError(f"Product title is empty: {product.get('sku', '?')}")
        prepared.append({**product, "title": title, "prepared": True})
    return prepared


def save_products(path: Path, products: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(products)
