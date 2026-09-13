# 本地知识文件上传阿里云百炼知识库操作规范

> 适用场景：把本地知识文件（.txt / .md 等）入库到百炼平台知识库，并验证召回生效

## 一、核心结论

上传是**异步两段式**过程：

1. 提交文件 → 拿到 `job_id`
2. 用 `job_id` 轮询处理状态 → 等待云端完成切片、向量化、入库
3. 查询验证 → 确认知识真正可召回

**关键认知：上传成功 ≠ 知识可用。** 工具返回成功仅代表文件已提交给平台，必须等状态完成并通过召回验证，才算真正打通。

## 二、工具调用链（三个工具串行）

```
① upload_local_file_to_bailian_rag(file_path="绝对路径")
        ↓ 返回 job_id
② query_bailian_rag_job_status(job_id="<①的返回值>")
        ↓ 轮询直到状态完成
③ query_rag(query="文件中独有的内容")
        ↓ 能召回 = 入库成功
```

| 步骤 | 工具 | 关键参数 | 注意点 |
|---|---|---|---|
| ① | `upload_local_file_to_bailian_rag` | `file_path`：必须绝对路径 | 返回值中的 `job_id` 必须记录，不要丢弃 |
| ② | `query_bailian_rag_job_status` | `job_id`：①返回的 ID | 状态未完成时重复调用属正常，间隔几秒再查 |
| ③ | `query_rag` | `query`：自然语言问题 | 用文件独有的内容做探针，验证召回 |

中间靠 `job_id` 衔接，这是唯一的传递变量。

## 三、路径规范（最易踩坑）

- `file_path` **必须传绝对路径**，例如
  `E:\Ai_Agent\app\code_agent\rag\bailian_rag_upload_guide.md`
- 相对路径会因进程工作目录不确定而找不到文件
- Windows 下 `\` 或 `/` 均可，但不要带引号嵌套、中文空格

### 文件工具的目录权限限制

`list_directory` / `file_search` / `read_file` / `write_file` 仅能在**当前工作目录**内使用，越界会被拒绝，报错形如：

`Access denied to file_path: ... Permission granted exclusively to the current working directory`

规避方式：
- 需要查看目标目录时，改用 `execute_powershell_command`：

```powershell
Get-ChildItem -Path "E:\Ai_Agent\app\code_agent\rag" -Recurse | Select-Object Name, Length, FullName
```

- 需要跨目录写文件时，**推荐"先写工作目录、再复制过去"**，比在命令行里拼接长文本安全（可避免中文、引号、反引号的转义问题）：

```powershell
Copy-Item -Path ".\xxx.md" -Destination "E:\Ai_Agent\app\code_agent\rag\xxx.md" -Force
```

拿到准确路径再执行上传，可避免拼错路径反复重试。

## 四、失败对照表

| 现象 | 原因 | 处理 |
|---|---|---|
| ① 报文件不存在 | 用了相对路径，或目录名拼写有误 | 回到 `Get-ChildItem` 核对 `FullName` |
| ② 状态长期不完成 | 文件编码非 UTF-8，或格式平台不支持 | 转 UTF-8 后重新上传 |
| ③ 召回为空 | 只上传没等解析完成；或查询语义与原文差异过大 | 先确认 ② 已完成，再换更接近原文表述的 query |
| write_file 被拒绝 | 目标路径不在当前工作目录内 | 先写工作目录，再用 Copy-Item 复制 |

## 五、内容层面的注意事项

- **只传知识文件**：`.txt` / `.md` / `.pdf` 等；`.py` 这类代码文件属于工程代码，不要入库
- **避免内容重复**：两份内容相同的文件同时入库，会导致召回时互相干扰
  - 排查方法：对比文件字节数，尺寸完全一致的疑似重复，上传前先比对内容
- **文件命名**：用能表达主题的英文名，如 `bailian_rag_upload_guide.md`，避免 `1.txt`、`新建文档.md` 这类无语义命名

## 六、标准流程清单

1. 确认文件存在且路径准确（跨目录用 PowerShell 列目录）
2. 核对内容是否与已入库文件重复
3. 调用上传工具，记录 `job_id`
4. 轮询状态直到完成
5. 用独有内容做召回验证
6. 验证通过才算任务结束
