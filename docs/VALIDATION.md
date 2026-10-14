# 本次验证记录

日期：2026-10-14，版本：0.5.2。

- Python 3.10.19：54 项 unittest 全部通过，包含多维表上传批次输出、工作表列表、记录查询/删除、删除业务失败响应和工作通知/userId/operatorId 查询 mock。
- 无 site-packages 的子进程可导入所有公共模块，不创建运行目录；调用缺失的可选功能会给出安装提示。
- 离线 wheel 构建成功：`dist/ecommerce_automation-0.5.2-py3-none-any.whl`。
- wheel 已在独立目录安装并验证导入。
- AI 同步/异步客户端使用替身测试；钉钉 token 获取、缓存刷新、机器人消息、多维表上传/查询/删除及工作通知均使用 HTTP mock。
- `run_tasks()` 使用普通 dict handler 测试去重和重复运行行为。
- 示例模板按普通函数完成 `collect → prepare → save`；带外部写入的示例在未配置凭据时只打印提示。

可直接运行已安装的示例：

```powershell
& C:\ProgramData\anaconda3\envs\spider310\python.exe D:\sd14\ecommerce_automation\examples\new_project\main_01_prepare.py
```

测试使用 HTTP MockTransport、MySQL/Redis/Playwright 替身，不连接真实店铺、不发通知。
并发领取测试使用 8 个线程、40 次领取、30 条真实 SQLite 任务，验证没有重复领取。
SQLite 租约保护测试覆盖过期、恢复、旧 worker 更新被拒绝、heartbeat 和完成后禁止覆盖。

真实 MySQL/Redis 网络连接、浏览器二进制启动、平台业务成功条件仍由后续项目进行集成验收。
当前 `.venv` 只用于展示零依赖安装，不包含 pip 或可选功能；日常开发请使用自己的 Python 3.10+ 项目环境。
