import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain.schema import HumanMessage, AIMessage

# ==================== 配置 ====================
load_dotenv()
DATA_DIR = "/data/conversations"

# ===== 第一步：构建提示词模板 ======
# 系统角色设定 + 历史消息占位符 + 用户问题
prompt = ChatPromptTemplate.from_messages([
    ('system', '你是一位优秀的技术专家，擅长解决各种开发中的技术问题'),
    MessagesPlaceholder(variable_name='chat_history'),  # 关键：使用 MessagesPlaceholder
    ('human', '{question}')
])

# ===== 第二步：创建大模型实例 ======
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    temperature=0.7,
)

# ===== 第三步：构建链式调用 ======
# 提示词模板 | 大模型 | 字符串输出解析器
chain = prompt | llm | StrOutputParser()


# ===== 第四步：定义文件操作函数（历史记录持久化） ======
def get_file_path(session_id):
    """根据会话ID生成JSON文件的存储路径"""
    user_id = session_id.split("_")[0]
    dir_path = os.path.join(DATA_DIR, user_id)
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, f"{session_id}.json")


def save_conversation_history(session_id, messages):
    """将对话历史保存到JSON文件"""
    file_path = get_file_path(session_id)
    data = [
        {
            "session_id": session_id,
            "sender": "user" if isinstance(msg, HumanMessage) else "assistant",
            "content": msg.content,
            "timestamp": datetime.now().isoformat(),
        }
        for msg in messages
    ]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_conversation_history(session_id):
    """从JSON文件加载对话历史"""
    file_path = get_file_path(session_id)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [
            HumanMessage(content=item["content"]) if item["sender"] == "user"
            else AIMessage(content=item["content"])
            for item in raw
        ]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# ===== 第五步：构建基于历史消息的Runnable实例 ======
def get_session_history(session_id):
    """获取会话历史（从文件加载）"""
    history = load_conversation_history(session_id)
    return InMemoryChatMessageHistory(messages=history)


chain_with_history = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history",
)


# ===== 第六步：构建多轮对话主循环 ======
def run_conversation():
    # 生成会话ID：用户ID + UUID（每次生成新会话）
    user_id = "user1"
    session_id = user_id + "_" + str(uuid.uuid4())
    # 或使用已有会话：session_id = user_id + "_" + "82b8d5d4-8ebf-4a55-a892-426542deb8c8"

    print(f"\n[会话开始] 会话 ID: {session_id}")

    while True:
        user_input = input("用户: ")
        if user_input.lower() in ["退出", "exit"]:
            break

        # 调用带历史记录的链
        response = chain_with_history.invoke(
            {"question": user_input},
            config={"configurable": {"session_id": session_id}},
        )

        # 手动保存历史到文件
        history = load_conversation_history(session_id)
        history.append(HumanMessage(content=user_input))
        history.append(AIMessage(content=response))
        save_conversation_history(session_id, history)

        print(f"助手: {response}")

    print("[会话结束] 历史已保存至文件。")


if __name__ == "__main__":
    run_conversation()