"""DingTalk group-bot message; sends only when credentials are configured."""

import os

from ecommerce_automation.notify import send_dingtalk_markdown


def main():
    token = os.getenv("DINGTALK_BOT_TOKEN")
    secret = os.getenv("DINGTALK_BOT_SECRET")
    if not token or not secret:
        print("Set DINGTALK_BOT_TOKEN and DINGTALK_BOT_SECRET to run this example.")
        return
    send_dingtalk_markdown(
        token,
        secret,
        "工具包测试",
        "ecommerce_automation **DingTalk** 工具调用成功",
    )


if __name__ == "__main__":
    main()
