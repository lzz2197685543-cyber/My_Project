"""
基础解析器处理最简单的数据格式转换：
    StrOutputParser:直接提取模型返回的原始文本，不做任何结构化处理
    CommaSeparatedListOutputParser:将逗号分隔的文本转换为Python列表。例如，将“apples,bananas,oranges”解析为['apples','bananas','oranges']
    BooleanOutputParser:解析文本为布尔值（True/False）。模型输出必须是"yes"或"no"(不区分大小写),解析器会统一转为大写后判断。
    SimpleJsonOutputParser:将文本简单处理后转换为JSON格式，通常用于模型已经正确输出JSON的情况。
"""

from langchain_core.output_parsers import StrOutputParser,CommaSeparatedListOutputParser
from langchain_core.prompts import ChatPromptTemplate

from commong import llm



system_message = '你是一位{role}专家，擅长回答{domain}领域的问题。'
user_message = '{question}'

chat_template = ChatPromptTemplate.from_messages([
    ('system', system_message),
    ('user', user_message)
])

parser=StrOutputParser()

chain=chat_template | llm | parser


# 正确方式：直接传入一个字典，包含模板中需要的所有变量
input_dict = {
    'role': '计算',
    'domain': '使用工具进行数据计算',
    'question': '请阅读下面的问题，并返回一个严格的JSON对象，不要使用MarkDown代码块包裹！，问题：12+17=？'
}

# 链会自动将字典中的值填充到模板中，然后调用LLM，最后用解析器处理输出
response = chain.invoke(input_dict)
print(response)
