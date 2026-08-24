import uuid

from app.agent.prompts.multi_chat_prompts import multi_chat_prompt
from app.agent.model.qwen import qwen_llm

from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_community.agent_toolkits.file_management import FileManagementToolkit
from langchain_core.runnables import RunnableWithMessageHistory, RunnableSequence,RunnableParallel

store = {}


def get_session_history(session_id):
    # if session_id not in store:
    #     store[session_id] = ChatMessageHistory()
    # print(store)
    # return store[session_id]
    return FileChatMessageHistory(f'{session_id}.json')

file_toolkit=FileManagementToolkit(root_dir='D:\sd14\\ai-agent\\temp')

file_tools=file_toolkit.get_tools()

llm_with_tools=qwen_llm.bind_tools(tools=file_tools)

# 串行写法1
# chain = multi_chat_prompt | llm_with_tools | StrOutputParser()

# 串行写法2
# chain=multi_chat_prompt.pipe(llm_with_tools).pipe(StrOutputParser())

# 串行写法3，RunnableSequence 至少需要两步，否则会引发报错：
chain=RunnableSequence(
    first=multi_chat_prompt,
    middle=[llm_with_tools],
    last=StrOutputParser()
)

chain_with_history = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history",
)

chat_session_id = uuid.uuid4()

while True:
    user_input = input('用户:')
    if user_input.lower() == 'q' or user_input.lower() == 'quit':
        break

    response = chain_with_history.stream(
        {'question': user_input},
        config={'configurable': {"session_id": chat_session_id}},
    )
    print("助理:")
    for chunk in response:
        print(chunk,end='')

    print('\n')

