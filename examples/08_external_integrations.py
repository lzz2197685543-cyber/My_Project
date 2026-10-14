"""Template only: fill credentials in the calling project environment first."""

import os

from ecommerce_automation import Settings
from ecommerce_automation.notify import DingTalkNotifier
from ecommerce_automation.storage import MySQLConfig, MySQLPool, RedisDeduplicator


def main():
    settings = Settings.load()
    required = (
        "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "REDIS_URL",
        "DINGTALK_ACCESS_TOKEN", "DINGTALK_SECRET",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print("Set these environment variables before connecting: " + ", ".join(missing))
        return
    mysql_config = MySQLConfig(
        host=settings.require("DB_HOST"), user=settings.require("DB_USER"),
        password=settings.require("DB_PASSWORD"), database=settings.require("DB_NAME"),
        port=settings.integer("DB_PORT", 3306, minimum=1),
    )
    with MySQLPool(mysql_config) as pool:
        connection = pool.connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                print("MySQL ok:", cursor.fetchone())
        finally:
            connection.close()

    with RedisDeduplicator.from_url(settings.require("REDIS_URL"), namespace="demo") as dedup:
        print("new keys:", dedup.filter_new(["sku-1", "sku-2"]))

    with DingTalkNotifier(
        settings.require("DINGTALK_ACCESS_TOKEN"), settings.require("DINGTALK_SECRET"),
    ) as notifier:
        notifier.send_text("基础包外部服务连接测试")


if __name__ == "__main__":
    main()
