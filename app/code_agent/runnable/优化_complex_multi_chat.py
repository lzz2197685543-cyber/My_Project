import os
import uuid
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_community.chat_message_histories import FileChatMessageHistory

# ==================== 配置 ====================
load_dotenv()
DATA_DIR = "/data/conversations"

# ===== 第一步：构建提示词模板 ======
# 系统角色设定 + 历史消息占位符 + 用户问题
prompt = ChatPromptTemplate.from_messages([
    ('system', '你是一位优秀的技术专家，擅长解决各种开发中的技术问题'),
    MessagesPlaceholder(variable_name='chat_history'),  # 关键：历史消息注入点
    ('human', '{question}')
])

# ===== 第二步：创建大模型实例 ======
llm = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://ws-kcaoxz5olbi6r3qa.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    streaming=True,  # 启用流式输出
    temperature=0.7,  # 控制随机性
)

# ===== 第三步：构建 LCEL 链 ======
# 使用管道符 | 声明式组合：提示词 → 大模型 → 字符串解析器
chain = prompt | llm | StrOutputParser()


# ===== 第四步：配置历史记录存储（文件持久化） ======
def get_session_history(session_id: str):
    """
    获取会话历史记录，使用 LangChain 内置的 FileChatMessageHistory

    优势：
    1. 自动管理消息的保存和加载
    2. 无需手动实现序列化/反序列化
    3. 按用户ID分目录存储，实现数据隔离
    """
    # 按用户ID分目录存储
    user_id = session_id.split("_")[0]
    dir_path = os.path.join(DATA_DIR, user_id)
    os.makedirs(dir_path, exist_ok=True)

    # 文件路径：/data/conversations/{user_id}/{session_id}.txt
    file_path = os.path.join(dir_path, f"{session_id}.txt")
    return FileChatMessageHistory(file_path)


# ===== 第五步：包装为带历史记录的 Runnable ======
chain_with_history = RunnableWithMessageHistory(
    runnable=chain,  # 基础链
    get_session_history=get_session_history,  # 历史记录获取函数
    input_messages_key="question",  # 输入消息的键名
    history_messages_key="chat_history",  # 历史消息的键名（与提示词中的占位符对应）
)


# ===== 第六步：多轮对话主循环 ======
def run_conversation():
    # 生成会话ID：用户ID + UUID（每次生成新会话）
    user_id = "user1"
    session_id = user_id + "_" + str(uuid.uuid4())
    # 或使用已有会话恢复：session_id = user_id + "_" + "82b8d5d4-8ebf-4a55-a892-426542deb8c8"

    print(f"\n[会话开始] 会话 ID: {session_id}")
    print("[提示] 输入 '退出' 或 'exit' 结束对话\n")

    while True:
        # 获取用户输入
        user_input = input("用户: ")
        if user_input.lower() in ["退出", "exit"]:
            break

        # 调用带历史记录的链
        # - 自动从文件加载历史
        # - 将历史注入到提示词的 chat_history 占位符
        # - 调用大模型生成响应
        # - 自动将新消息追加到历史文件
        response = chain_with_history.invoke(
            {"question": user_input},
            config={"configurable": {"session_id": session_id}},
        )

        print(f"助手: {response}")

    print("[会话结束] 历史已保存至文件。")


if __name__ == "__main__":
    run_conversation()