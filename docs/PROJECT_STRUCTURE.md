# ecommerce_automation 项目结构

本项目是后续电商自动化项目共用的基础包。它负责通用技术能力，不负责任何具体平台的商品字段、类目规则、店铺配置或发布流程。

## 1. 总体结构

```text
ecommerce_automation/
├── pyproject.toml
├── README.md
├── AGENTS.md
├── CHANGELOG.md
├── .gitignore
│
├── src/
│   └── ecommerce_automation/
│       ├── __init__.py
│       ├── py.typed
│       ├── _optional.py
│       ├── errors.py
│       ├── config.py
│       ├── logging.py
│       ├── http.py
│       ├── ai.py
│       ├── dingtalk.py
│       ├── dingtalk_work.py
│       ├── notify.py
│       ├── browser.py
│       ├── status.py
│       ├── workflow.py
│       │
│       ├── tasks/
│       │   ├── __init__.py
│       │   ├── store.py
│       │   ├── runner.py
│       │   └── simple.py
│       │
│       └── storage/
│           ├── __init__.py
│           ├── mysql.py
│           └── redis_client.py
│
├── tests/
│   ├── test_core.py
│   ├── test_tasks.py
│   ├── test_adapters.py
│   ├── test_browser.py
│   ├── test_isolation.py
│   └── test_utilities.py
│
├── docs/
│   ├── USAGE.md
│   ├── PROJECT_STRUCTURE.md
│   └── VALIDATION.md
│
└── examples/
    ├── 01_config_logging.py
    ├── 02_collection_workflow.py
    ├── 03_finance_reconciliation.py
    ├── 04_inventory_sync.py
    ├── 05_product_selection.py
    ├── 06_http_idempotency.py
    ├── 07_browser_login.py
    ├── 08_external_integrations.py
    ├── 09_manual_reconcile.py
    ├── 10_ai_chat.py
    ├── 11_dingtalk_bot.py
    ├── 12_dingtalk_table_upload.py
    ├── 13_task_queue_function.py
    ├── README.md
    └── new_project/
        ├── main_01_prepare.py
        ├── README.md
        ├── requirements.txt
        ├── config/
        │   ├── business.json
        │   └── .env.example
        └── services/
            ├── __init__.py
            └── prepare.py
```

`build/`、`dist/`、`*.egg-info/`、`.venv/` 属于构建或本地环境产物，不属于源码结构，也不应该手工修改或提交。

## 2. 根目录文件

### `pyproject.toml`

Python 包的构建和安装配置，定义：

- 包名：`ecommerce-automation`
- 导入名：`ecommerce_automation`
- 当前版本：`0.5.2`
- Python 版本：`3.10+`
- `src/` 源码布局
- 可选依赖组：`config`、`http`、`notify`、`ai`、`dingtalk`、`mysql`、`redis`、`browser`、`all`

### `README.md`

项目总说明，包含安装方式、模块列表、任务状态语义、HTTP 重试原则、发布 wheel 的方式和基础边界。

### `AGENTS.md`

给 Agent 和维护者的开发约定，例如：

- import 不能产生外部副作用
- 平台逻辑不能放进公共包
- 可选依赖只能在使用时加载
- 写请求默认不能自动重放
- 修改公共能力必须补行为测试

### `CHANGELOG.md`

记录公共包版本变化。以后新增或修改公开 API 时，必须更新这里。

### `.gitignore`

忽略虚拟环境、构建产物、运行日志、本地数据、凭据和 IDE 文件。

## 3. 核心源码目录

源码放在 `src/ecommerce_automation/`，这是标准的 `src-layout`，可以避免从项目根目录误导入未安装的源码。

### `__init__.py`

公共包入口导出常用的配置、路径、日志和结果类型。AI、钉钉、HTTP、存储和队列工具从各自模块单独导入。

import 这个文件不会读取配置、创建目录、连接数据库或启动浏览器。

### `py.typed`

声明这个包提供类型标注，方便 Pyright、mypy 等工具检查调用项目。

### `_optional.py`

可选依赖加载器。调用 HTTP、AI、钉钉、MySQL、Redis、Playwright 或 dotenv 功能时，才加载对应第三方包；缺少依赖时给出明确安装命令。

### `errors.py`

定义跨项目统一的异常语义：

| 异常 | 用途 |
| --- | --- |
| `ConfigError` | 配置缺失或格式错误 |
| `RetryableError` | 当前操作可以安全重试 |
| `PermanentError` | 数据或业务错误，不应继续重试 |
| `NeedsManual` | 需要人工处理 |
| `AuthenticationError` | 登录态失效或登录失败 |
| `OutcomeUnknown` | 远端结果未知，重试前必须查询确认 |
| `SkipTask` | 当前任务主动跳过 |
| `LeaseLostError` | 当前 worker 已经失去任务所有权 |
| `MissingDependencyError` | 没有安装对应可选依赖 |

### `config.py`

提供配置和路径管理：

- `ProjectPaths`：统一得到新项目的 `config/`、`data/`、`logs/` 路径
- `load_json()`：读取并验证 JSON 对象
- `Settings`：读取环境变量和 `.env`，支持字符串、整数、布尔值和必填项检查

配置属于调用项目，公共包不保存账号、密码、token 或店铺信息。

### `logging.py`

提供一次运行一个日志文件的日志上下文：

- 自动生成 `run_id`
- 支持绑定 `stage`、`shop`、`task_id`
- 同时写文件和控制台
- 对指定 secret 做脱敏
- 上下文退出时关闭 handler

调用项目通过 `RunContext` 获取 logger，不要继续复制自己的基础日志实现。

### `http.py`

提供同步和异步 HTTP JSON 客户端：

- 请求超时
- 最小请求间隔
- `Retry-After` 处理
- GET 等只读请求的有限重试
- 登录失效回调和刷新回调
- 不自动跟随重定向
- 写请求默认禁止重放

平台的登录失效码、请求 URL 和业务成功条件由调用项目传入。

### `ai.py`

提供 `ask_ai()` / `ask_ai_async()` 单次调用函数，以及 `AIClient` / `AsyncAIClient` 复用连接的客户端。调用项目传入 API key、服务地址和模型；提示词、业务字段解析和模型选择策略留在业务代码中。安装 `[ai]` extra 后使用。

### `dingtalk.py`

提供 `upload_dingtalk_records()`、`list_dingtalk_sheets()`、`query_dingtalk_records()`、`delete_dingtalk_records()` 和 `delete_dingtalk_sheet()` 按需调用函数，以及 `DingTalkTokenProvider` 和 `DingTalkTableClient` 复用客户端。上传逐批输出进度、失败时报告批次；写请求不自动重放。应用凭据、base/sheet/operator ID 和记录字段均由调用项目提供。

### `dingtalk_work.py`

提供 `send_dingtalk_work_text()` 工作通知、手机号查询 `userId`、通过 `userId` 查询 `unionId`，以及手机号直查多维表 `operatorId` 的函数。`DingTalkWorkNotifier` 支持复用 token 和 HTTP 连接。工作通知的 `agent_id`、应用凭据及接收用户由调用项目传入。

### `notify.py`

提供通知接口：

- `Notifier`：通知协议
- `LogNotifier`：把通知写入日志，适合本地测试
- `send_dingtalk_text()` / `send_dingtalk_markdown()` 单次调用函数
- `DingTalkNotifier`：复用连接发送钉钉加签机器人文本和 Markdown 消息

钉钉通知只有在 HTTP 成功且返回 `errcode == 0` 时才算成功。

### `browser.py`

提供异步 Playwright 持久化浏览器会话：

- 按平台和账号隔离 Profile
- 复用登录态
- 等待人工登录或验证码
- 统一关闭 browser context 和 Playwright runtime

这里不放任何具体平台的登录流程，也不实现验证码绕过。

### `status.py`

定义公共包唯一负责的执行状态：`pending`、`processing`、`succeeded`、`failed`、`skipped` 和 `need_manual`。
平台业务阶段不放进这里；例如 `collected`、`reconciled`、`synced`、`exported` 应通过任务的 `business_state` 保存。

### `workflow.py`

定义 `TaskOutcome`，让 handler 明确返回已确认的执行结果。除了执行状态外，它还可以携带：

- `result`：业务结果摘要或远端响应的必要字段
- `business_state`：调用项目定义的业务阶段
- `operation_id`：本地生成的幂等操作标识
- `remote_id`：平台返回的任务、报表或请求 ID
- `retry_delay`：明确允许重试时的延迟

写请求结果不明确时使用 `TaskOutcome.manual(...)` 或抛出 `OutcomeUnknown`，不要直接返回普通字典让 runner 把未知结果当成成功。

## 4. `tasks/` 任务模块

任务模块负责本地任务队列和状态流转，不负责具体的商品业务。

### `tasks/store.py`

`SQLiteTaskStore` 提供：

- `(queue, task_key)` 唯一去重
- 原子领取任务
- `processing` 租约
- worker 心跳
- 失败次数和最大尝试次数
- 结果与错误落盘
- `business_state`、`operation_id`、`remote_id` 与执行状态分开保存
- 过期任务转入 `need_manual`
- 人工确认后重新排队

状态流转：

```text
pending → processing → succeeded
                    ├→ skipped
                    ├→ failed
                    └→ need_manual
```

### `tasks/runner.py`

提供任务执行器：

- `TaskRunner`：同步 handler
- `AsyncTaskRunner`：异步 handler
- `RunSummary`：本轮领取和结果统计

handler 的返回值必须代表已经确认的业务结果。未知异常会进入 `need_manual`，不会自动猜测成功或盲目重试。

### `tasks/__init__.py`

统一导出任务模块的公共 API，调用项目可以从 `ecommerce_automation.tasks` 导入。

### `tasks/simple.py`

提供 `run_tasks(items, handler, db_path=..., key=...)` 和异步版本。handler 只接收普通字典，调用端不必操作 `Task` 对象或 runner；需要自定义租约、人工恢复等行为时再使用底层类。

## 5. `storage/` 存储模块

### `storage/mysql.py`

提供：

- `MySQLConfig`：数据库连接配置
- `MySQLPool`：独立连接池
- `BaseDAO`：事务、单条执行、批量执行、单条查询、多条查询

事务必须显式开始；成功后提交，异常后回滚并释放连接。表结构和业务 SQL 由调用项目维护。

### `storage/redis_client.py`

提供 `RedisDeduplicator`：

- 按 namespace 隔离标记
- 批量筛选未处理 key
- 成功后写入完成标记
- 支持 TTL

Redis 标记只用于完成记录，不是任务锁。并发任务分配使用 SQLite 或业务数据库的原子机制。

### `storage/__init__.py`

统一导出 MySQL 和 Redis 公共类。

## 6. 测试目录

### `tests/test_core.py`

测试配置、JSON、路径、日志隔离、secret 脱敏和 handler 清理。

### `tests/test_tasks.py`

测试任务去重、并发领取、租约过期、heartbeat、重试、人工状态、同步 runner 和异步 runner。

### `tests/test_adapters.py`

测试 HTTP 重试边界、写请求不可盲目重放、鉴权刷新、钉钉签名、MySQL 事务和 Redis 去重。

### `tests/test_browser.py`

使用 Playwright 替身测试 Profile 路径、登录等待、启动失败清理和关闭失败清理。

### `tests/test_isolation.py`

验证基础模块在没有第三方依赖时仍能导入，import 不会自动创建文件或连接外部服务。

运行：

```powershell
python -m unittest discover -s tests -v
```

## 7. 新项目模板

`examples/new_project/` 是以后新项目的起点：

### `main_01_prepare.py`

阶段入口示例，演示普通函数串联的“采集 → 整理 → 保存”流程、路径初始化、配置读取和日志。

### `services/prepare.py`

业务函数示例。实际项目应在 `services/` 中放平台采集、编辑、发布和结果确认逻辑，函数不需要接收任务对象。

### `config/business.json`

演示业务配置。真实项目可放批量大小、任务版本、店铺映射和业务开关。

### `config/.env.example`

环境变量模板，不放真实凭据。

### `requirements.txt`

声明调用项目依赖的公共包版本。平台特有依赖由项目自行添加。

### `README.md`

说明如何复制模板、安装公共包、启动阶段和设计任务 key。

## 8. 功能示例

`examples/01_*.py` 到 `examples/13_*.py` 是按工具和业务场景拆开的最小用法：

- `01_config_logging.py`：配置、路径、日志和脱敏
- `02_collection_workflow.py`：商品、订单和接口采集
- `03_finance_reconciliation.py`：财务下载、匹配和对账
- `04_inventory_sync.py`：库存写入、幂等操作和远端 ID
- `05_product_selection.py`：选品过滤和结果导出
- `06_http_idempotency.py`：HTTP 重试边界和幂等键
- `07_browser_login.py`：持久化浏览器会话和人工登录
- `08_external_integrations.py`：MySQL、Redis 和钉钉接入
- `09_manual_reconcile.py`：远端结果未知后的人工核对
- `10_ai_chat.py`：OpenAI 兼容聊天
- `11_dingtalk_bot.py`：钉钉机器人 Markdown 消息
- `12_dingtalk_table_upload.py`：钉钉多维表分批上传
- `14_dingtalk_table_and_work.py`：多维表查询/删除、工作通知和用户 ID 查询
- `13_task_queue_function.py`：普通字典 handler 的持久队列调用

其中 `01` 到 `06`、`09`、`13` 可离线运行；`07`、`08`、`10`、`11`、`12` 在未配置环境变量时只提示并退出。

## 9. 调用项目的依赖方向

```text
main_01_xxx.py
    ↓
services/
    ↓
ecommerce_automation
    ├── config
    ├── logging
    ├── tasks
    ├── ai
    ├── dingtalk
    ├── http
    ├── browser
    ├── storage
    └── notify
```

公共包不应该反向 import 任何调用项目。

调用项目负责：

- 平台 URL 和 API 字段
- 平台登录和鉴权刷新实现
- 商品模型和字段转换
- 类目、标题、SKU、图片规则
- 采集、编辑、发布、确认流程
- 业务数据库表和 SQL
- 远端业务状态判断

公共包负责：

- 通用配置读取
- 日志和运行标识
- 可选任务去重、租约、重试和人工恢复
- 可复用的 AI 聊天、钉钉机器人及多维表上传工具
- 通用 HTTP、浏览器会话和数据库事务能力
- 通知基础能力

以后新增平台时，复制 `examples/new_project/`，在业务项目中实现平台逻辑，不修改公共包来适配单个平台。
