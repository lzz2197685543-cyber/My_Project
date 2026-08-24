"""
LangChain 提示词模板（Prompt Template）使用指南
包含四种常用模板：
1. PromptTemplate - 基础文本模板
2. ChatPromptTemplate - 对话消息模板
3. ChatMessagePromptTemplate - 单条消息模板
4. FewShotPromptTemplate - 少样本示例模板
"""

from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    ChatMessagePromptTemplate,
    FewShotPromptTemplate
)
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# ============================================================
# 初始化大模型
# ============================================================
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True
)

print("=" * 60)
print("LangChain 提示词模板示例")
print("=" * 60)

# ============================================================
# 第一种：PromptTemplate（基础文本模板）
# ============================================================
print("\n【第一种】PromptTemplate - 基础文本模板")
print("-" * 40)

# 1.1 创建模板
prompt_template = PromptTemplate.from_template('今天{something}一点也不好')

# 1.2 填充变量生成提示词
prompt = prompt_template.format(something='心情')
print(f"生成的提示词: {prompt}")

# 1.3 调用模型
# resp = llm.stream(prompt)
# for chunk in resp:
#     print(chunk.content, end='')


# ============================================================
# 第二种：ChatPromptTemplate（对话消息模板）
# ============================================================
print("\n【第二种】ChatPromptTemplate - 对话消息模板")
print("-" * 40)

# 2.1 定义系统消息和用户消息模板
system_message = '你是一位{role}专家，擅长回答{domain}领域的问题。'
user_message = '{question}'

# 2.2 创建对话模板
chat_template = ChatPromptTemplate.from_messages([
    ('system', system_message),
    ('user', user_message)
])

# 2.3 填充变量生成提示词
prompt = chat_template.format_messages(
    role='技术',
    domain='web开发',
    question='如何搭建一个基于python的web项目'
)
print(f"生成的提示词: {prompt}")

# 2.4 调用模型
# resp = llm.stream(prompt)
# for chunk in resp:
#     print(chunk.content, end='')


# ============================================================
# 第三种：ChatMessagePromptTemplate（单条消息模板）
# ============================================================
print("\n【第三种】ChatMessagePromptTemplate - 单条消息模板")
print("-" * 40)

# 3.1 分别创建系统消息和用户消息模板
system_message = '你是一位{role}专家，擅长回答{domain}领域的问题。'
user_message = '{question}'

system_template = ChatMessagePromptTemplate.from_template(
    template=system_message,
    role='system',
)

user_template = ChatMessagePromptTemplate.from_template(
    template=user_message,
    role='user',
)

# 3.2 组合成对话模板
chat_prompt = ChatPromptTemplate.from_messages([
    system_template,
    user_template
])

# 3.3 填充变量生成提示词
prompt = chat_prompt.format_messages(
    role='技术',
    domain='web开发',
    question='如何搭建一个基于python的web项目'
)
print(f"生成的提示词: {prompt}")

# 3.4 调用模型
# resp = llm.stream(prompt)
# for chunk in resp:
#     print(chunk.content, end='')


# ============================================================
# 第四种：FewShotPromptTemplate（少样本示例模板）
# ============================================================
print("\n【第四种】FewShotPromptTemplate - 少样本示例模板")
print("-" * 40)

# 4.1 定义示例的格式模板
example_template = '输入：{input}\n输出：{output}'

# 4.2 提供示例数据
examples = [
    {'input': '将Hello翻译成中文', 'output': '你好'},
    {'input': '将tool翻译成中文', 'output': '工具'},
    # 可以添加更多示例
]

# 4.3 创建少样本模板
few_shot_template = FewShotPromptTemplate(
    examples=examples,  # 示例列表
    example_prompt=PromptTemplate.from_template(example_template),  # 示例格式
    prefix='请将以下英文翻译成中文:',  # 前缀说明
    suffix="输入：{text}\n输出:",  # 后缀，包含要处理的新输入
    input_variables=['text']  # 输入变量列表
)

# 4.4 查看完整模板结构
print("完整模板结构:")
print(few_shot_template)

# 4.5 填充变量生成提示词
prompt = few_shot_template.format(text='freedom')
print("\n生成的提示词:")
print(prompt)

# 4.6 调用模型
print("\n模型响应:")
resp = llm.stream(prompt)
for chunk in resp:
    print(chunk.content, end='')


"""

模板类型	适用场景	核心特点	使用方式
PromptTemplate	简单的文本生成	最基础，单一文本模板	format()
ChatPromptTemplate	对话场景	支持多角色消息（system/user/assistant）	format_messages()
ChatMessagePromptTemplate	复杂对话系统	可复用的单条消息模板	结合ChatPromptTemplate使用
FewShotPromptTemplate	少样本学习	在上下文中提供示例	提供examples和模板

"""