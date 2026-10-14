# 接入指南

## 0. 按需调用工具

这个包是工具箱。你的业务代码保持普通函数和普通顺序，需要什么就导入什么。

### AI 对话

```python
from ecommerce_automation.ai import ask_ai, AIClient

title = ask_ai(
    "把这个商品标题改写成英文：儿童积木",
    api_key=api_key,
    base_url=ai_base_url,
    model="your-model",
    system_prompt="只返回改写后的标题",
    temperature=0.2,
)

# 同一程序要多次请求时，复用 AIClient 可避免重复创建连接。
with AIClient(api_key=api_key, base_url=ai_base_url, model="your-model") as ai:
    another_title = ai.simple_chat("继续改写下一个商品标题")
```

异步项目可使用 `AsyncAIClient`：

```python
from ecommerce_automation.ai import AsyncAIClient

async with AsyncAIClient(api_key=api_key, base_url=ai_base_url, model="your-model") as ai:
    answer = await ai.simple_chat("总结这段订单备注")
```

安装：`pip install 'ecommerce-automation[ai]'`。客户端不读取 `.env`，由业务项目自行读取并传入密钥、服务地址和模型。

### 钉钉机器人消息

```python
from ecommerce_automation.notify import DingTalkNotifier, send_dingtalk_markdown

send_dingtalk_markdown(bot_token, bot_secret, "库存同步", "已更新 **18** 个 SKU")

# 也可以复用客户端连续发消息：
with DingTalkNotifier(bot_token, bot_secret) as bot:
    bot.send_text("同步完成", at_mobiles=["13800000000"])
```

安装：`pip install 'ecommerce-automation[notify]'`。失败会抛异常，由调用项目决定记录、通知或中止后续逻辑。

### 钉钉多维表

```python
from ecommerce_automation.dingtalk import DingTalkTableClient, DingTalkTokenProvider, upload_dingtalk_records

result = upload_dingtalk_records(
    [{"SKU": "SKU-001", "库存": 18}, {"SKU": "SKU-002", "库存": 6}],
    client_id=client_id,
    client_secret=client_secret,
    base_id=base_id,
    sheet_id=sheet_id,
    operator_id=operator_id,
    batch_size=100,
)
# 默认逐批打印批次进度；返回值仍是每批钉钉原始响应。

# 要复用 access token/连接时，再显式管理客户端生命周期：
with DingTalkTokenProvider(client_id, client_secret) as token:
    with DingTalkTableClient(base_id, sheet_id, operator_id, token) as table:
        result = table.upload_records(
            [{"SKU": "SKU-001", "库存": 18}, {"SKU": "SKU-002", "库存": 6}],
            batch_size=100,
            delay=0.1,
        )
```

安装：`pip install 'ecommerce-automation[dingtalk]'`。记录字段由调用项目准备。上传请求不会自动重试；遇到超时先查询表格，确认未写入后再重新提交。

列出文档下的工作表、查询记录，以及删除记录/工作表：

```python
from ecommerce_automation.dingtalk import (
    delete_dingtalk_records,
    delete_dingtalk_sheet,
    list_dingtalk_sheets,
    query_dingtalk_records,
)

sheets = list_dingtalk_sheets(
    client_id=client_id,
    client_secret=client_secret,
    base_id=base_id,
    operator_id=operator_id,
)
for sheet in sheets:
    print(f"{sheet['name']} -> {sheet['id']}")

page = query_dingtalk_records(
    client_id=client_id,
    client_secret=client_secret,
    base_id=base_id,
    sheet_id=sheet_id,
    operator_id=operator_id,
    max_results=100,
    filter="platform='速卖通' and today_sales>10",
    sort=[{"field": "today_sales", "order": "desc"}],
    field_names=["SKU", "platform", "today_sales"],
)
print(page["records"])
if page.get("nextToken"):
    next_page = query_dingtalk_records(
        client_id=client_id,
        client_secret=client_secret,
        base_id=base_id,
        sheet_id=sheet_id,
        operator_id=operator_id,
        next_token=page["nextToken"],
    )

# 删除操作不可撤销。先从查询结果中选定真实记录 id，再显式启用确认：
record_ids_to_delete = []  # 填入 page["records"] 中确认过的记录 id
confirm_delete_records = False
if confirm_delete_records and record_ids_to_delete:
    delete_dingtalk_records(
        record_ids_to_delete, client_id=client_id, client_secret=client_secret,
        base_id=base_id, sheet_id=sheet_id, operator_id=operator_id,
    )

# 删除整个工作表影响该表全部数据；使用 list_dingtalk_sheets() 返回的真实 id。
sheet_id_to_delete = ""
confirm_delete_sheet = False
if confirm_delete_sheet and sheet_id_to_delete:
    delete_dingtalk_sheet(
        sheet_id_to_delete, client_id=client_id, client_secret=client_secret,
        base_id=base_id, operator_id=operator_id,
    )
```

删除响应若返回 HTTP 错误，或 HTTP 200 但响应中的 `success` 不是 `true`，工具会抛出包含钉钉响应的异常。示例里的 ID 变量必须填入接口返回的真实值。

查询单页后用响应中的 `nextToken` 继续翻页。文档下工作表列表只需要 `base_id`，记录查询和删除还需要对应的 `sheet_id`。

### 钉钉工作通知和用户 ID

工作通知是应用发给用户的私聊/工作消息，与群机器人消息使用不同凭据和接口：

```python
from ecommerce_automation.dingtalk_work import (
    DingTalkWorkNotifier,
    get_dingtalk_operator_id_by_mobile,
    get_dingtalk_union_id_by_user_id,
    get_dingtalk_user_id_by_mobile,
    send_dingtalk_work_text,
)

user_id = get_dingtalk_user_id_by_mobile(
    "13800000000", client_id=client_id, client_secret=client_secret,
)
operator_id = get_dingtalk_operator_id_by_mobile(
    "13800000000", client_id=client_id, client_secret=client_secret,
)
same_operator_id = get_dingtalk_union_id_by_user_id(
    user_id, client_id=client_id, client_secret=client_secret,
)
send_dingtalk_work_text(
    user_id, "库存同步完成", "本次更新 18 个商品",
    client_id=client_id, client_secret=client_secret, agent_id=agent_id,
)

# 连续查询或发送时，复用 notifier 和 access token。
with DingTalkWorkNotifier(client_id, client_secret, agent_id) as work:
    user_id = work.get_user_id_by_mobile("13800000000")
    operator_id = work.get_union_id_by_user_id(user_id)
    work.send_text(user_id, "任务完成", "处理结果已写入多维表")
```

`userId` 用于向具体用户发送工作通知；多维表 `operator_id` 使用 `unionId`。应用需具有对应的通讯录查询、工作通知和多维表权限。接口失败会抛出异常，异常中包含钉钉返回的错误信息。

### 普通函数式任务队列

需要任务去重和中断后续跑时，用便捷函数；handler 只接收普通字典：

```python
from ecommerce_automation.tasks import run_tasks

def publish_one(product):
    # 这里仍然是项目自己的普通业务代码
    return {"sku": product["sku"], "published": True}

summary = run_tasks(
    products,
    publish_one,
    db_path="data/publish_tasks.sqlite3",
    key="sku",
    queue="publish_products",
)
```

同样的数据库、queue 和 key 再次运行时，已完成项目会去重，未完成项目可以继续处理。需要更细的租约或人工恢复控制时，再直接使用 `SQLiteTaskStore` 和 `TaskRunner`。
函数返回本轮统计字典。没有被明确标记为可重试/永久失败的异常会进入 `need_manual`，避免自动重复执行可能已经产生的外部写入。

## 1. 配置属于业务项目

```python
from pathlib import Path
from ecommerce_automation import ProjectPaths, Settings, load_json

paths = ProjectPaths(Path(__file__).resolve().parent)
settings = Settings.load(env_file=paths.config / ".env")
business = load_json(paths.config / "business.json")
database = settings.require("DB_NAME")
port = settings.integer("DB_PORT", 3306, minimum=1)
```

优先级：显式传入的 `environ`（未传时使用系统环境） > 指定 `.env` > defaults。
不改变 `os.environ`，不向父目录搜索 `.env`，不对 `${VAR}` 做隐式插值。
不需要 `.env` 时直接 `Settings.load()`，也无需安装 dotenv。

## 2. 运行日志

```python
from ecommerce_automation import RunContext

with RunContext("temu_project", paths.logs, secrets=[settings.require("API_KEY")]) as run:
    logger = run.logger.bind(stage="publish", shop="shop_01")
    logger.info("prepared_count=%s", 25)
```

日志在项目 `logs/YYYY-MM-DD/project_time_runid.log`。多个相同项目名的 run 各自拥有 handler。
日志时间使用执行机器本地时间；跨机器调度时统一操作系统时区。
自动遮蔽仅针对传入的 secret 原文（包含异常 traceback）；不把整份配置/headers/cookies 打入日志。
任务 payload、result、error 也会持久化到 SQLite，因此这些字段应只存业务字段和必要错误描述。
本包不自动清理历史日志或运行数据，保留策略由项目或运维设定。

## 3. 同步任务与业务状态

```python
from ecommerce_automation import TaskOutcome
from ecommerce_automation.errors import PermanentError
from ecommerce_automation.tasks import SQLiteTaskStore, TaskRunner

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
```

`summary` 是本次领取的任务结果统计，`store.counts(queue)` 是整个队列的状态统计。
重试延迟还没到时 runner 会返回，不会在后台自动运行或长期等待；由后续阶段运行或外部调度再次调用。

`TaskStatus` 是公共执行状态；`business_state`、`operation_id`、`remote_id` 是业务项目保存的扩展字段。
采集可以写 `business_state="collected"`，财务可以写 `business_state="reconciled"`，选品可以写 `business_state="exported"`。
对于真实写操作，只有确认平台最终业务结果才能 return `TaskOutcome.success(...)`。
“接口接受了异步任务”仅表示提交阶段成功；请单独用确认阶段轮询远端 task_id，无法确认时返回 `TaskOutcome.manual(...)`。

```python
return TaskOutcome.manual(
    "库存请求超时，远端结果未知",
    business_state="sync_pending_confirmation",
    operation_id=f"stock:{task.key}",
)
```

## 4. 异步任务与 HTTP

```python
import asyncio
from ecommerce_automation.http import AsyncHttpClient
from ecommerce_automation.tasks import AsyncTaskRunner
from ecommerce_automation.errors import PermanentError

async def main():
    async with AsyncHttpClient("https://your-platform.example") as client:
        async def handle(task):
            result = await client.request_json("GET", "/api/product", params={"id": task.payload["sku"]})
            if result.get("code") != 200:
                raise PermanentError("查询商品业务失败")
            return TaskOutcome.success(result["data"], business_state="fetched")
        with RunContext("query", paths.logs) as run:
            await AsyncTaskRunner(store, logger=run.logger).run("query_v1", handle)

asyncio.run(main())
```

示例域名和成功码只是占位，需要用新项目的真实接口契约替换。
同步版本为 `HttpClient` + `with`，两者方法都叫 `request_json`。

每次请求可以注入鉴权，而业务失效码由项目决定。写请求若平台支持幂等键：

```python
def is_auth_invalid(response, payload):
    return isinstance(payload, dict) and payload.get("code") == "SESSION_EXPIRED"

with HttpClient(
    "https://your-platform.example",
    auth_headers=session_manager.get_headers,
    is_auth_invalid=is_auth_invalid,
    refresh_auth=session_manager.refresh,
) as client:
    data = client.request_json(
        "POST", "/api/inventory/sync", json={"sku": "sku1", "quantity": 18},
        replay_safe=True, idempotency_key="stock:shop1:sku1:v1",
    )
```

`session_manager` 是业务项目自己的对象。refresh 必须返回布尔 True，刷新后下次请求重新取 headers。
HTTP 401 默认判为鉴权失败，403 默认是 HTTP 错误；平台若有额外失效码，通过回调精确判断。
异步 client 的 get_headers/refresh 必须为 async，is_auth_invalid 仍是普通函数。
所有网络尝试共用 max_attempts，鉴权只刷新一次；不自动跟随重定向。
retry-after 超过等待预算时抛 RetryableError，由上层延迟调度。

## 5. 浏览器与人工登录

```python
from ecommerce_automation.browser import BrowserSession

async with BrowserSession(
    paths.data / "profiles", platform="jst", account="shop_01", headless=False,
) as browser:
    await browser.page.goto("https://your-platform.example", wait_until="domcontentloaded")
    async def logged_in(page):
        return await page.get_by_text("退出登录", exact=True).is_visible()
    await browser.wait_for_login(logged_in, timeout=120, logger=logger)
    response = await browser.request.get("https://your-platform.example/api/items")
```

登录判断必须替换成对应平台的可靠信号。等待期间不跳转页面，不打断用户处理验证码。
profile 在 `data/profiles/<platform>/<account>/`；名称使用 ASCII 字母、数字、下划线、连字符。
同一个 profile 同时只供一个浏览器实例使用。本包不实现任何平台专有的登录或验证码绕过。
BrowserSession 是独立异步组件，APIRequestContext 不经过 HttpClient 的重试策略。

## 6. MySQL 事务

```python
from ecommerce_automation.storage import MySQLConfig, MySQLPool, BaseDAO

config = MySQLConfig(
    host=settings.require("DB_HOST"), port=settings.integer("DB_PORT", 3306),
    user=settings.require("DB_USER"), password=settings.require("DB_PASSWORD"),
    database=settings.require("DB_NAME"),
)
with MySQLPool(config) as pool:
    dao = BaseDAO(pool)
    with dao.transaction() as cursor:
        cursor.execute("UPDATE my_products SET title=%s WHERE sku=%s", ("标题", "sku1"))
        cursor.execute("INSERT INTO my_audit (sku) VALUES (%s)", ("sku1",))
```

两条 SQL 共用一事务，全部完成才提交；异常回滚并归还连接。
表名和 SQL 属于业务项目，本包不创建或修改现有 MySQL 表。
MySQL/Redis 接口是同步接口；async 项目使用 `asyncio.to_thread` 调用完整的数据库操作。

## 7. Redis 去重与通知

```python
from ecommerce_automation.storage import RedisDeduplicator

with RedisDeduplicator.from_url(settings.require("REDIS_URL"), namespace="shop_01") as dedup:
    fresh = dedup.filter_new(["sku1", "sku2"])
    # 在业务结果已经持久化成功后，才写入完成标记：
    dedup.mark_done("sku1", ttl_seconds=86400)
```

Redis 标记不是任务锁；先检查再执行不能阻止并发重复。
本机工作分配使用 SQLite 原子 claim，跨机器业务去重仍需数据库唯一约束或远端幂等机制。

```python
from ecommerce_automation.notify import DingTalkNotifier

with DingTalkNotifier(
    settings.require("DINGTALK_ACCESS_TOKEN"), settings.require("DINGTALK_SECRET"),
) as notifier:
    notifier.send_text("批次完成：成功 20，需人工检查 1")
```

机器人须启用加签。HTTP 200 且 errcode 为整数 0 才算通知成功；发送超时不自动重复发送。
不要在商品 handler 成功后紧接通知并将通知错误误判为商品失败；建议整批结束后独立通知。

## 8. 人工核对和恢复

```python
from ecommerce_automation import TaskStatus

task = store.get("inventory_sync_v1", "inventory:shop1:sku1:v1")
# 先根据 task.payload 查询远端；确认没有重复副作用、且故障已处理后：
store.resolve_manual(
    task.id, TaskStatus.SUCCEEDED,
    result={"confirmed_quantity": 18}, business_state="synced", remote_id="stock-001",
)
```

`resolve_manual` 只接受 `need_manual`，用于人工查询远端后记录最终结果；不会重新执行外部副作用。
`requeue` 只接受 failed/need_manual，不覆盖 succeeded，不允许抢占活跃 processing。
耗尽次数必须显式 `reset_attempts=True` 才能重置。恢复前先停止仍可能执行的旧进程；
租约 token 只保护本地状态写入，不能取消已发出的远端请求。

## 9. 功能示例索引

完整可复制示例在 `examples/`：

- `01_config_logging.py`：路径、`.env`、JSON、日志绑定和脱敏。
- `02_collection_workflow.py`：数据采集结果写入 `collected`。
- `03_finance_reconciliation.py`：财务下载、匹配、异常对账。
- `04_inventory_sync.py`：库存同步、幂等操作和远端 ID。
- `05_product_selection.py`：选品过滤、结果文件交付。
- `06_http_idempotency.py`：HTTP mock、鉴权重试和幂等键。
- `07_browser_login.py`：持久化浏览器 Profile 和人工登录等待。
- `08_external_integrations.py`：MySQL、Redis、钉钉接入模板。
- `09_manual_reconcile.py`：超时后的人工远端核对。
