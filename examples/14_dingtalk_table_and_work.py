"""List/query DingTalk sheets and optionally test work-notification ID lookups."""

import os

from ecommerce_automation.dingtalk import (
    delete_dingtalk_records,
    list_dingtalk_sheets,
    query_dingtalk_records,
)
from ecommerce_automation.dingtalk_work import (
    get_dingtalk_operator_id_by_mobile,
    get_dingtalk_user_id_by_mobile,
    send_dingtalk_work_text,
)


def main():
    client_id = os.getenv("DINGTALK_CLIENT_ID")
    client_secret = os.getenv("DINGTALK_CLIENT_SECRET")
    base_id = os.getenv("DINGTALK_BASE_ID")
    operator_id = os.getenv("DINGTALK_OPERATOR_ID")
    sheet_id = os.getenv("DINGTALK_SHEET_ID")
    required = {
        "DINGTALK_CLIENT_ID": client_id,
        "DINGTALK_CLIENT_SECRET": client_secret,
        "DINGTALK_BASE_ID": base_id,
        "DINGTALK_OPERATOR_ID": operator_id,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        print("Set these environment variables first: " + ", ".join(missing))
        return

    sheets = list_dingtalk_sheets(
        client_id=client_id,
        client_secret=client_secret,
        base_id=base_id,
        operator_id=operator_id,
    )
    for sheet in sheets:
        print(f"{sheet.get('name')} -> {sheet.get('id')}")

    if sheet_id:
        page = query_dingtalk_records(
            client_id=client_id,
            client_secret=client_secret,
            base_id=base_id,
            sheet_id=sheet_id,
            operator_id=operator_id,
            max_results=20,
        )
        print(f"查询到 {len(page.get('records', []))} 条记录")

    mobile = os.getenv("DINGTALK_TEST_MOBILE")
    if mobile:
        user_id = get_dingtalk_user_id_by_mobile(
            mobile, client_id=client_id, client_secret=client_secret,
        )
        operator = get_dingtalk_operator_id_by_mobile(
            mobile, client_id=client_id, client_secret=client_secret,
        )
        print(f"userId: {user_id}")
        print(f"operatorId (unionId): {operator}")

        agent_id = os.getenv("DINGTALK_AGENT_ID")
        if agent_id and os.getenv("DINGTALK_SEND_WORK_MESSAGE") == "1":
            send_dingtalk_work_text(
                user_id,
                "工具包测试通知",
                "钉钉工作通知发送成功",
                client_id=client_id,
                client_secret=client_secret,
                agent_id=agent_id,
            )

    record_id = os.getenv("DINGTALK_DELETE_RECORD_ID")
    if record_id and sheet_id and os.getenv("DINGTALK_CONFIRM_DELETE") == "1":
        delete_dingtalk_records(
            [record_id],
            client_id=client_id,
            client_secret=client_secret,
            base_id=base_id,
            sheet_id=sheet_id,
            operator_id=operator_id,
        )
        print(f"已删除记录: {record_id}")


if __name__ == "__main__":
    main()
