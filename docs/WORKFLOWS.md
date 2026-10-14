# 电商工作流设计

公共包现在按工具箱使用：AI、钉钉、HTTP、浏览器、数据库、日志和任务队列彼此独立。普通流程按原来的 Python 函数写法组织，需要哪项能力就调用对应工具。下面的任务约定只在选择持久队列工具时适用。

| 业务方向 | 常见阶段 | `business_state` 示例 | 典型外部副作用 |
| --- | --- | --- | --- |
| 商品/订单采集 | 请求、解析、清洗、保存 | `fetched`、`parsed`、`collected` | 读取平台接口、写数据库 |
| 商品编辑/上架 | 搬家、编辑、提交、确认 | `moved`、`edited`、`submitted`、`published` | 修改平台数据、提交发布 |
| 库存同步 | 读取、标准化、提交、确认 | `read`、`normalized`、`sync_pending_confirmation`、`synced` | 更新平台库存 |
| 财务对账 | 下载、解析、匹配、审核 | `downloaded`、`parsed`、`matched`、`reconciled` | 下载报表、写财务表 |
| 选品 | 抓取、过滤、评分、导出 | `crawled`、`filtered`、`scored`、`exported` | 抓取页面、写 Excel/表格 |
| 售后/物流 | 下载、关联、更新、关闭 | `downloaded`、`linked`、`updated`、`closed` | 更新订单/物流记录 |

## 两层状态

公共包只定义：

```text
pending       等待领取
processing    当前 worker 正在处理
succeeded     本地 handler 已确认成功
failed        已确认失败，通常不应自动重试
skipped       根据业务规则跳过
need_manual   结果不明确或需要人工处理
```

调用项目自己定义业务状态，并写入 `business_state`：

```python
return TaskOutcome.success(
    {"matched": 1280, "unmatched": 3},
    business_state="reconciled_with_exceptions",
    remote_id="report-2026-10-shop1",
)
```

这条任务的公共状态是 `succeeded`，业务状态是 `reconciled_with_exceptions`。两者同时有意义。

## 一条任务的最小契约

```python
store.enqueue(
    queue="finance_reconcile_v1",
    key="temu:shop1:2026-10",
    payload={"platform": "temu", "shop": "shop1", "month": "2026-10"},
    business_state="downloaded",
    operation_id="report-download:temu:shop1:2026-10",
)
```

- `queue`：一个可独立运行的工作流阶段。
- `key`：该阶段的幂等业务键，不建议只写 SKU。
- `payload`：重跑所需的最小业务输入，不放 token、密码和完整 cookies。
- `business_state`：进入队列时已有的业务状态。
- `operation_id`：一次外部操作的本地标识，可用于日志和平台幂等键。
- `remote_id`：平台返回的任务、请求、报表或导出文件 ID。

推荐 key：

```text
采集：collect:1688:shop1:2026-10-13:page-01
财务：finance:temu:shop1:2026-10
库存：inventory:temu:shop1:SKU-001:v2
选品：selection:sellersprite:2026-10-13:batch-01
物流：parcel:shein:shop1:2026-10:tracking-001
```

## 结果返回规则

```python
# 远端结果已明确成功
return TaskOutcome.success(
    {"remote_status": "accepted"},
    business_state="synced", operation_id=operation_id, remote_id=remote_id,
)

# 数据本身无效，不要继续消耗重试次数
return TaskOutcome.failed("缺少订单号", business_state="invalid")

# 业务规则明确跳过
return TaskOutcome.skipped({"reason": "店铺未启用"}, business_state="skipped_by_rule")

# 网络暂时失败，而且整个操作可安全重放
return TaskOutcome.retry("平台限流", delay=60, business_state="ready")

# 已经发出写请求但无法确定远端结果
return TaskOutcome.manual(
    "请求超时，先按 operation_id 查询远端",
    business_state="sync_pending_confirmation", operation_id=operation_id,
)
```

不确定时不要返回普通字典。普通字典会被 runner 当作成功结果；要使用 `TaskOutcome.manual` 或抛出 `OutcomeUnknown`。

## 远端副作用的四步模式

适用于库存、价格、商品提交、订单状态更新等写操作：

```text
1. 生成稳定 operation_id
2. 以 operation_id 作为平台支持的 Idempotency-Key
3. 发出请求
4. 用远端查询接口确认最终状态
```

如果第 3 步超时，不要直接重发：进入 `need_manual`，通过 `operation_id` 或 `remote_id` 查询平台，再调用 `resolve_manual`。

公共包的租约只能防止两个本地 worker 覆盖状态，不能撤回已经发出的网络请求。

## 按你现有项目的落地方式

普通业务流程保持熟悉的结构：

```python
products = collect_products()
products = clean_products(products)
ai_titles = rewrite_titles(products, ai_client)
upload_records = make_dingtalk_records(ai_titles)
dingtalk_table.upload_records(upload_records)
```

平台登录、字段转换、类目规则和上传后验证仍由项目服务函数实现；AI、钉钉表、钉钉机器人等通用连接器直接从公共包导入。

### 采集类项目

适用于 `ToySaas`、1688/Temu/平台数据采集：

```text
入口：建立 RunContext、入队日期/页码批次
services/collector.py：页面或接口采集、解析、去重
storage：落库后返回 business_state="collected"
交付：Excel/钉钉/数据库写成功后再返回 succeeded
```

### 财务类项目

适用于 `SMT`、`Shopee`、`Shein`、`TK`、`Temu` 月报：

```text
download → parse → normalize → match → reconcile → export
```

每个阶段独立 queue；不要把下载、匹配、上传钉钉写成一个无法恢复的大函数。

### 库存/价格同步

适用于销售日报、库存回写、低库存补货：

```text
read_source → normalize → submit → confirm
```

`submit` 采用幂等键，`confirm` 查询平台最终状态；提交超时进入 `need_manual`。

### 选品项目

适用于 `ToySaas`、`SellerSprite` 等：

```text
crawl → filter → score → export → notify
```

评分函数尽量写成纯函数，任务结果只保存统计和交付文件路径，不把原始大 payload 全塞进 SQLite。

## 公共包边界

放入公共包：配置、日志、任务租约、幂等执行、HTTP 传输、浏览器会话、数据库事务、通知适配。

留在业务项目：平台 URL、登录选择器、业务字段、类目映射、SKU 规则、财务匹配规则、库存语义、远端成功判断、AI prompt。
