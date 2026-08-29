import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory

load_dotenv()


# 检查是否成功加载
api_key = os.getenv("DASHSCOPE_API_KEY")

# ===== 第一步：构建提示词模板 ======

multi_chat_prompt = ChatPromptTemplate.from_messages([
    ('system', '你是一位优秀的技术专家，擅长解决各种开发中的技术问题'),
    MessagesPlaceholder(variable_name='chat_history'),  # 关键：使用 MessagesPlaceholder
    ('human', '{question}')
])


# ===== 第二步：创建大模型实例 ======
# 初始化 LLM
qwen_llm = ChatOpenAI(
    model="qwen-plus",
    api_key=api_key,
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    temperature=0.7,
)


# ===== 第三步：构建链式调用 ======
chain = multi_chat_prompt | qwen_llm  | StrOutputParser()

# ===== 第四步：构建基于历史消息的Runnable实例 ======
store = {}


def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    print(store)
    return store[session_id]

chain_with_history = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history",
)

# ===== 第五步：构建多轮对话 ======

import uuid

def run_conversation():
    session_id = uuid.uuid4()
    while True:
        user_input = input("用户：")
        if user_input.lower() == "exit" or user_input.lower() == "quit" or user_input.lower() == "q":
            break

        response = chain_with_history.invoke(
            {"question": user_input},
            config={"configurable": {"session_id": session_id}},
        )

        print("助手：")
        for chunk in response:
            print(chunk, end="")
        print("\n")

if __name__ == '__main__':
    run_conversation()