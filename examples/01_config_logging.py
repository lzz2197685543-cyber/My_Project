from pathlib import Path

from ecommerce_automation import ProjectPaths, RunContext, Settings, load_json

def main():
    paths = ProjectPaths(Path(__file__).resolve().parent / "demo_project")
    paths.ensure_runtime()
    settings = Settings.load(
        defaults={"BATCH_SIZE": "50", "DRY_RUN": "true"},
        environ={"BATCH_SIZE": "20"},
    )

    config_path = paths.config / "business.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('{"workflow": "inventory_sync", "version": 2}', encoding="utf-8")
    business = load_json(config_path)
    with RunContext("config_demo", paths.logs, secrets=["example-secret"]) as run:
        logger = run.logger.bind(stage="prepare", shop="shop_demo")
        logger.info(
            "workflow=%s batch_size=%s dry_run=%s",
            business["workflow"], settings.integer("BATCH_SIZE"), settings.boolean("DRY_RUN"),
        )
        logger.info("secret=%s is redacted", "example-secret")
    print(f"log written to: {run.log_file}")


if __name__ == "__main__":
    main()

# from ecommerce_automation.logging import RunContext  # 路径按实际包结构
#
# with RunContext("shop_sync", "logs", secrets=["my-secret-token"]) as ctx:
#     ctx.logger.info("开始同步")
#
#     shop_log = ctx.logger.bind(shop="shopA", stage="fetch")
#     shop_log.info("拉取订单完成")
#
#     # 哪怕这里不小心打了密钥，也会变成 [REDACTED]
#     shop_log.info("token=my-secret-token")
#

# Settings的使用
# from ecommerce_automation.config import Settings, ConfigError
#
# try:
#     settings = Settings.load(env_file=".env")
#     config = {
#         "host": settings.require("DB_HOST"),
#         "port": settings.integer("DB_PORT", default=3306, minimum=1),
#         "debug": settings.boolean("DEBUG", default=False),
#     }
#     print(config)
#     # {'host': '127.0.0.1', 'port': 3306, 'debug': True}
# except ConfigError as e:
#     print(f"配置错误: {e}")
