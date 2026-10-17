# ecommerce_automation

面向后续电商自动化项目的公共工具包，版本 `0.5.2`，兼容 Python 3.10+。
安装名称为 `ecommerce-automation`，代码导入名称为 `ecommerce_automation`。
已有业务项目没有迁移到本包。

## 先运行一个完整示例

请使用实际运行新项目的解释器安装。当前机器常用解释器为
`C:\ProgramData\anaconda3\envs\spider310\python.exe`；PATH 中裸 `python` 是 3.8，不能安装本包。

```powershell
& 'C:\ProgramData\anaconda3\envs\spider310\python.exe' -m pip install -e D:\sd14\ecommerce_automation
& 'C:\ProgramData\anaconda3\envs\spider310\python.exe' D:\sd14\ecommerce_automation\examples\new_project\main_01_prepare.py
```

首次运行会按普通 Python 函数处理“采集 → 整理 → 保存”，并写入运行日志。
在 PyCharm 中选择同一个已安装本包的解释器，即可右键运行入口。

新项目直接复制 `examples/new_project`。业务放进它的 `services/`，参数放进它的 `config/`。
包内部不会寻找旧项目配置，不会自动连接数据库、启动浏览器或发送通知。

## 已实现模块

| 模块 | 功能 | 额外依赖 |
| --- | --- | --- |
| `config` | 显式项目路径、JSON、环境配置优先级、类型检查 | `.env` 解析需要 `[config]` |
| `logging` | 一次运行一个文件、run_id、绑定阶段/店铺/任务、指定密钥脱敏、关闭 handler | 无 |
| `tasks` | `run_tasks(items, handler, ...)` 简单调用；需要时还可直接使用 SQLite 持久队列、租约和恢复 | 无 |
| `workflow` | 通用 `TaskOutcome`，保存业务阶段、远端 ID、操作 ID和执行结果 | 无 |
| `storage` | MySQL 独立连接池、事务、DAO；Redis 成功标记 | `[mysql]` / `[redis]` |
| `http` | HTTPX 同步/异步 JSON、超时、限速、有限重试、鉴权回调 | `[http]` |
| `ai` | OpenAI 兼容接口，同步/异步聊天 | `[ai]` |
| `notify` | 日志通知、钉钉加签机器人文本/Markdown 消息 | `[notify]` |
| `dingtalk` | 多维表上传、查询、删除和文档工作表列表 | `[dingtalk]` |
| `dingtalk_work` | 钉钉工作通知、手机号查询 userId/operatorId | `[dingtalk]` |
| `browser` | 异步 Playwright、按平台/账号隔离 profile、人工登录等待、资源关闭 | `[browser]` |

## 各模块速查
| **你想做的事** | **用哪个模块** | **装什么 extra** |
|---|---|---|
| 读配置（`.env` / JSON / 环境变量） | `ProjectPaths` / `Settings` / `load_json` | `[config]` |
| 一次运行一个日志文件、脱敏 | `RunContext` | 无 |
| 任务去重 + 断点续跑（最简单） | `run_tasks(items, handler, db_path=..., key=...)` | 无 |
| 精细控制租约 / 人工恢复 | `SQLiteTaskStore` + `TaskRunner` | 无 |
| 安全 HTTP（重试 / 鉴权 / 幂等） | `HttpClient` / `AsyncHttpClient` | `[http]` |
| AI 改标题 / 总结 | `ask_ai` / `AIClient` | `[ai]` |
| 钉钉群机器人消息 | `DingTalkNotifier` | `[notify]` |
| 钉钉多维表上传 / 查询 / 删除 | `upload_dingtalk_records` 等 | `[dingtalk]` |
| 钉钉工作通知 + 手机号查 ID | `dingtalk_work` | `[dingtalk]` |
| 持久化浏览器登录态 | `BrowserSession` | `[browser]` |
| MySQL 事务 | `MySQLPool` + `BaseDAO` | `[mysql]` |
| Redis 完成标记去重 | `RedisDeduplicator` | `[redis]` |


只需要哪个模块就安装哪个模块：

```powershell
python -m pip install -e 'D:\sd14\ecommerce_automation[config,http,notify]'
python -m pip install -e 'D:\sd14\ecommerce_automation[ai,dingtalk]'
python -m pip install -e 'D:\sd14\ecommerce_automation[mysql,redis]'
python -m pip install -e 'D:\sd14\ecommerce_automation[browser]'
python -m playwright install chromium
```

全部可选功能：`python -m pip install -e 'D:\sd14\ecommerce_automation[all]'`。
浏览器二进制仍需单独安装。

## 项目边界

```text
main_01_xxx.py / main_02_xxx.py
    → services/（平台接口、类目映射、标题规则、发布结果验证）
        → ecommerce_automation.ai / dingtalk / http / storage / tasks
```

采集、订单、财务、库存、选品、编辑和发布都可以使用本包。Temu 的整组店铺发布与 TK 的逐店铺发布继续由业务项目定义。
本包的任务状态只表示“这次任务如何执行”，不代替任何业务状态。
按项目需要导入单个工具即可。AI 服务地址、模型和提示词由调用项目决定；钉钉 app 凭据、表格 ID 和字段映射也由调用项目传入。
包不会自动读取旧项目配置、启动流程或连接真实服务。

## 直接调用工具

```python
from ecommerce_automation.ai import ask_ai
from ecommerce_automation.notify import send_dingtalk_markdown

title = ask_ai(
    "把标题改写成英文",
    api_key=api_key,
    base_url=ai_url,
    model="your-model",
    system_prompt="只返回标题",
)

send_dingtalk_markdown(bot_token, bot_secret, "上新结果", f"已处理 **{len(products)}** 个商品")
```

钉钉多维表的上传、查询、删除和工作通知均可按需直接调用，完整示例见 `docs/USAGE.md`；断点恢复队列可以直接调用 `run_tasks(items, handler, db_path=..., key="sku")`，业务 handler 只接收普通字典。需要复用连接时再使用对应客户端类。
各项可复制示例见 `examples/README.md`。

## 任务语义

```text
pending → processing → succeeded / skipped / failed / need_manual
               ↓
        可安全重试 → pending（耗尽次数后 failed）
```

- `(queue, key)` 是唯一键，重复 enqueue 不覆盖已有 payload，也不重复已完成任务。
- 推荐 key：`工作流:平台:店铺:业务对象:业务版本`；按日期运行的任务包含业务日期。
- `operation_id` 是本地对一次外部副作用的标识；`remote_id` 是平台返回的任务、报表或请求 ID。
- 抛 `RetryableError` 表示整个 handler 可以安全重放；默认延迟 30 秒，下次启动再领取。
- 抛 `PermanentError` 进入 failed；`SkipTask` 进入 skipped。
- 未知异常、`OutcomeUnknown`、`AuthenticationError` 进入 need_manual；鉴权失败同时中止当前批次。
- 超出租约的任务在下次 claim 时进入 need_manual，不会盲目重放；旧 worker 的完成写入会被拒绝。
- 运行很久的 handler 必须在到期前调用 `store.heartbeat(task)`，或显式配置合理的 lease_seconds。
- 同步和异步 runner 均串行执行；多进程可共享同一个本机 SQLite 文件。SQLite 文件不用于网络共享盘。
- 本地状态与远端平台无法构成同一事务：远端提交成功后本地崩溃，仍需查远端确认结果。
  唯一键和租约不能保证外部副作用“恰好一次”。

HTTP GET/HEAD/OPTIONS 默认允许有限重试；POST/PATCH/PUT/DELETE 默认不重放。
只读 POST 或平台明确支持幂等键的操作，才传 `replay_safe=True`。
每个 HTTP client 串行化自己的请求及鉴权刷新；不同 client 的限速互相独立。
HTTP 200 只代表收到 JSON，业务项目仍必须验证商品/任务结果。
写请求应传 `idempotency_key`，并把它保存为 `operation_id`；超时后先查询远端，再决定是否人工解决或重试。

## 安装与发布

开发期间使用 `pip install -e`，修改公共包会立即影响使用该 editable 安装的项目。
稳定运行的新项目建议使用固定版本 wheel：

```powershell
python -m pip wheel --no-deps --wheel-dir dist .
python -m pip install D:\sd14\ecommerce_automation\dist\ecommerce_automation-0.5.2-py3-none-any.whl
```

只在公共包目录构建，不会修改旧项目。wheel 可以保存在私有仓库或共享的制品目录。
发布新行为时增加 `pyproject.toml` 和 `__init__.py` 中的版本号；每个新项目自行升级依赖。
不兼容变更必须给出迁移说明，避免依赖“永远使用最新版”。

## 验证

标准库 unittest，无需 pytest：

```powershell
python -m unittest discover -s tests -v
```

运行前安装本包。测试使用临时 SQLite、HTTP 模拟响应、数据库替身和浏览器替身，
覆盖去重、并发领取、租约、事务回滚、配置隔离、日志脱敏及 HTTP 重放边界。
没有安装可选依赖时相关测试会显示 skipped。

离线测试不代表真实平台、MySQL、Redis 和浏览器登录已验收；新项目接入实际服务时，
需要对自己的连接参数和业务成功条件执行集成验证。

详细用法：`docs/USAGE.md`；工作流设计：`docs/WORKFLOWS.md`；文件说明：`docs/PROJECT_STRUCTURE.md`；
开发约定：`AGENTS.md`；功能示例：`examples/`；新项目模板：`examples/new_project/`。
