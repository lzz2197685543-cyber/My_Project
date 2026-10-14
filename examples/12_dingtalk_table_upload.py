"""Upload sample rows to a configured DingTalk multidimensional table."""

import os

from ecommerce_automation.dingtalk import upload_dingtalk_records


def main():
    names = ("DINGTALK_CLIENT_ID", "DINGTALK_CLIENT_SECRET", "DINGTALK_BASE_ID", "DINGTALK_SHEET_ID", "DINGTALK_OPERATOR_ID")
    values = {name: os.getenv(name) for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        print("Set these environment variables to upload rows: " + ", ".join(missing))
        return

    records = [{"SKU": "DEMO-001", "库存": 18}, {"SKU": "DEMO-002", "库存": 6}]
    print(upload_dingtalk_records(
        records,
        client_id=values["DINGTALK_CLIENT_ID"],
        client_secret=values["DINGTALK_CLIENT_SECRET"],
        base_id=values["DINGTALK_BASE_ID"],
        sheet_id=values["DINGTALK_SHEET_ID"],
        operator_id=values["DINGTALK_OPERATOR_ID"],
        batch_size=100,
    ))


if __name__ == "__main__":
    main()
