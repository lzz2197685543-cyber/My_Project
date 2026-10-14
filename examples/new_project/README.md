# 新项目模板

把整个 `examples/new_project` 目录复制为自己的新项目，使用安装了基础包的 Python 3.10+ 解释器。

```powershell
python -m pip install -e D:\sd14\ecommerce_automation
python main_01_prepare.py
```

此示例只在本地整理两条商品标题：按普通代码顺序执行采集、整理和保存，结果保存在
`data/prepared.json`，同时产生一份运行日志。没有网络请求，不需要账号或额外依赖。

新项目从这里改：

1. 改 `config/business.json` 的项目名、商品来源与批量参数。
2. 将业务逻辑写在 `services/`，每个函数只做一个清晰动作。
3. 在 `main_*.py` 中按普通 Python 代码顺序调用这些函数。
4. 每个阶段只在验证自己的业务产物之后返回结果。
5. 需要断点恢复和去重时，直接用 `run_tasks(items, handler, db_path=..., key=...)`；只有需要精细控制租约/人工恢复时才用底层 store 和 runner。
6. 阶段之间通过上一步确认的结果传数据；入口各自独立运行。

演示准备成功只表示标题整理完成；真实上架应在业务层检查远端任务结果/商品状态，再返回成功。
若接入 AI、钉钉、HTTP、浏览器或数据库，从基础包对应模块导入客户端并直接调用。需要持久队列时可用 `run_tasks()` 或 `run_tasks_async()`，参见基础包 `docs/USAGE.md`。

交付时可把构建好的 wheel 放进项目 `vendor/`，再执行：

```powershell
python -m pip install --no-index --find-links vendor -r requirements.txt
```

基础包不需要发布到公开 PyPI。采用可选模块时，其第三方依赖也需预先安装或放进 vendor。
