# 功能示例

这些示例按你现有项目中反复出现的工作流整理。它们演示的是公共包的使用方式，平台 URL、字段和成功条件仍由业务项目实现。

| 文件 | 场景 | 是否访问真实服务 |
| --- | --- | --- |
| `01_config_logging.py` | 配置与运行日志 | 否 |
| `02_collection_workflow.py` | 商品/订单/接口数据采集 | 否，使用本地样本 |
| `03_finance_reconciliation.py` | 财务下载、匹配、对账 | 否，使用本地样本 |
| `04_inventory_sync.py` | 库存同步与远端确认 | 否，模拟平台响应 |
| `05_product_selection.py` | 选品过滤与 Excel/JSON 交付 | 否 |
| `06_http_idempotency.py` | HTTP 鉴权、重试、幂等键 | 否，使用 HTTP mock |
| `07_browser_login.py` | Playwright 持久化登录与人工验证码 | 需要浏览器和平台地址 |
| `08_external_integrations.py` | MySQL、Redis、钉钉的接入 | 需要你自己的凭据 |
| `09_manual_reconcile.py` | 远端结果未知后的人工核对 | 否 |
| `10_ai_chat.py` | OpenAI 兼容 AI 聊天 | 需要显式配置 API key 和模型 |
| `11_dingtalk_bot.py` | 钉钉机器人 Markdown 消息 | 需要显式配置机器人凭据 |
| `12_dingtalk_table_upload.py` | 钉钉多维表分批上传 | 需要显式配置应用和表格 ID |
| `13_task_queue_function.py` | 用普通 dict handler 调用持久队列 | 否 |
| `14_dingtalk_table_and_work.py` | 列出文档工作表、查询记录、工作通知及 ID 查询；删除需显式确认环境变量 | 需要显式配置应用权限和凭据 |

离线示例：

```powershell
python 01_config_logging.py
python 02_collection_workflow.py
python 03_finance_reconciliation.py
python 04_inventory_sync.py
python 05_product_selection.py
python 09_manual_reconcile.py
python 13_task_queue_function.py
```

HTTP 示例需要安装：

```powershell
python -m pip install -e "D:\sd14\ecommerce_automation[http]"
python 06_http_idempotency.py
```

浏览器示例需要安装 `[browser]` 并执行 `python -m playwright install chromium`。配置真实平台登录页后再运行：

```powershell
$env:BROWSER_DEMO_URL = "https://your-real-platform.example/login"
$env:BROWSER_HEADLESS = "0"
python 07_browser_login.py
```

未设置 `BROWSER_DEMO_URL` 时示例只打印提示，不会访问占位域名。外部服务示例默认不会在没有环境变量时执行连接。

AI 和钉钉示例分别需要安装：

```powershell
python -m pip install -e "D:\sd14\ecommerce_automation[ai,dingtalk,notify]"
python 10_ai_chat.py
python 11_dingtalk_bot.py
python 12_dingtalk_table_upload.py
python 14_dingtalk_table_and_work.py
```

没有设置所需环境变量时，外部服务示例只打印需要的变量名称并退出。确认变量指向测试机器人/测试表格后再运行会产生外部写入的示例。

## 重要理解

任务队列工具保留两层状态：

```text
执行状态：pending / processing / succeeded / failed / skipped / need_manual
业务状态：由项目定义，例如 collected / reconciled / synced / exported
```

例如：

```python
return TaskOutcome.success(
    {"rows": 1280},
    business_state="reconciled",
    remote_id="finance-report-2026-10",
)
```

不要把 `published`、`matched`、`synced` 加到公共 `TaskStatus` 枚举里。它们是不同项目的业务词，不是通用执行结果。
