import requests

# 测试 generate 端点,调用本地下载的模型
response = requests.post(
    "http://127.0.0.1:11434/api/generate",
    json={
        "model": "qwen2.5:7b",
        "prompt": "AI Agent是什么？",
        "stream": False
    }
)

print(f"状态码: {response.status_code}")
if response.status_code == 200:
    print(response.json()["response"])
else:
    print(f"错误: {response.text}")


# from langchain_ollama.chat_models import ChatOllama
#
# llm = ChatOllama(
#     model="qwen2.5:7b",
# )
#
# response = llm.invoke("你好")
# print(response)