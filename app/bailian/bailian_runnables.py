# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.runnables import RunnableParallel
#
# import os
#
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
#
#
# load_dotenv()
#
#
# # 检查是否成功加载
# api_key = os.getenv("DASHSCOPE_API_KEY")
#
#
# # 初始化 LLM
# llm = ChatOpenAI(
#     model="qwen-plus",
#     api_key=api_key,
#     base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
#     streaming=True,
#     temperature=0.7,
# )
#
# joke_chain = ChatPromptTemplate.from_template("tell me a joke about {topic}") | llm
# poem_chain = ChatPromptTemplate.from_template("write a 2-line poem about {topic}") | llm
#
# parallel_chain = RunnableParallel(joke=joke_chain, poem=poem_chain)
#
# result = parallel_chain.invoke({"topic": "AI"})
# print(result)


# 函数RunnableLambda
# from langchain_core.runnables import RunnableLambda
#
# uppercase_lambda = RunnableLambda(lambda x: x.upper())
# result = uppercase_lambda.invoke("hello world")  # 输出 "HELLO WORLD"
#
# print(result)


# 透传 RunnablePassthrough
from langchain_core.runnables import (
RunnableLambda,
RunnableParallel,
RunnablePassthrough,
)

runnable = RunnableParallel(
    origin=RunnablePassthrough(),
    modified=lambda x: x+1
)

print(runnable.invoke(1)) # {'origin': 1, 'modified': 2}


def fake_llm(prompt: str) -> str: # Fake LLM for the example
    return "completion"

chain = RunnableLambda(fake_llm) | {
    'original': RunnablePassthrough(), # Original LLM output
    'parsed': lambda text: text[::-1] # Parsing logic
}

print(chain.invoke('hello')) # {'original': 'completion', 'parsed': 'noitelpmoc'}