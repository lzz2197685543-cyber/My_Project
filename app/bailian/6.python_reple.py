from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.agents import initialize_agent, AgentType

import os
from dotenv import load_dotenv

load_dotenv()

# 定义工具
tools = [PythonREPLTool()]

tool_names = ['PythonREPLTool']

# 初始化大模型
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True
)

# 创建智能体
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,  # 打印详细执行过程
)

# 创建提示词模板
prompt_template = PromptTemplate.from_template(template="""
你是一个专业的AI助手，擅长使用Python完成文件操作和网页生成任务。

## 可用工具
{tool_names}

## 任务执行流程
思考 → 行动 → 观察 → (重复) → 最终答案

每个步骤的说明：
- **思考**：分析当前状态，决定下一步行动
- **行动**：选择 [{tool_names}] 中的一个工具
- **行动输入**：提供具体输入（Python代码要纯净，无代码块标记）
- **观察**：记录执行结果
- **最终答案**：完整的任务完成报告

## 关键规则
1. PythonREPLTool只接受纯净的Python代码，不要添加 ```python 或 ``` 标记
2. 文件操作前确保目录存在：os.makedirs(path, exist_ok=True)
3. 使用UTF-8编码处理文本文件
4. 生成的HTML要专业、美观、完整

## 企业官网HTML要求
- 包含完整的HTML5文档结构
- 导航菜单：首页、关于、产品/服务、联系我们
- 主视觉区（Hero Section）：公司标语和CTA按钮
- 核心优势/产品服务展示（至少3项）
- 团队介绍或客户评价（可选）
- 页脚：版权信息、联系方式
- 使用现代CSS（Flexbox/Grid），响应式设计
- 配色方案专业（建议使用2-3种主色）
- 所有样式内嵌在HTML中

## 当前任务
{input}

开始执行，请在最终答案中提供详细执行报告。
""")

# 生成提示词
prompt = prompt_template.format(
    tool_names=' '.join(tool_names),
    input="""
    请创建一个企业官网的HTML文件，具体要求如下：

    ## 文件信息
    - 文件路径：D:/sd14/ai-code_agent/temp/index.html
    - 文件编码：UTF-8

    ## 网站内容要求
    1. **企业名称**：智创未来科技有限公司 (可以虚构)
    2. **企业定位**：专注于AI人工智能解决方案的科技公司
    3. **页面结构**：
       - 顶部导航栏：首页 | 关于我们 | 产品服务 | 新闻动态 | 联系我们
       - 主视觉区：企业标语 + 行动按钮
       - 核心业务展示区：至少展示3项核心业务（如：AI咨询、大模型部署、数据标注）
       - 企业优势：4个左右的优势卡片（技术领先、专业团队等）
       - 底部：版权信息、联系方式、地址

    ## 设计要求
    - 使用现代化设计风格（渐变、阴影、圆角等）
    - 主色调：蓝色系 (#2563eb, #3b82f6) + 白色
    - 响应式设计，适配不同屏幕
    - 所有样式写在HTML内部（不用外部资源）
    - 包含字体图标（使用Font Awesome CDN）

    ## 执行步骤
    1. 先检查 D:/sd14/ai-code_agent/temp 目录是否存在，不存在则创建
    2. 编写完整的HTML代码
    3. 写入文件并确认成功
    4. 返回文件路径和页面功能说明
    """
)

resp = agent.invoke(prompt)
print(resp)
print(resp['output'])
