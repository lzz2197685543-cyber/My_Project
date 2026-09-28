from langchain_core.prompt_values import StringPromptValue
from langgraph.graph import StateGraph,MessagesState
from langgraph.constants import START, END
from langchain_core.messages import AIMessage
import os
from app.code_agent.model.qwen import qwen_llm
from app.code_agent.mcp.browser import search_in_baidu_with_html

def output_graph_image(graph,filename):
    try:
        png_data=graph.get_graph().draw_mermaid_png()
        output_file_dir=os.path.dirname(__file__)
        output_file_path=os.path.join(output_file_dir,filename+'.png')

        with open(output_file_path,'wb') as f:
            f.write(png_data)

            print(f'文件写入成功：{output_file_path}')

    except Exception as e:
        print(e)


key_extract_query_keyword='key_extract_query_keyword'
key_search_baidu='key_search_baidu'
key_reply_user='key_reply_user'

class BaiduSearchMessagesState(MessagesState):
    search_question:str
    search_keyword:str
    search_results:str


def node_extract_query_keyword(state:BaiduSearchMessagesState):
    last_message=state['messages'][-1]
    content=last_message.content
    state['search_question']=content
    prompt=StringPromptValue(text=f'请从如下信息中提取需要在百度中搜索的关键词，直接返回结果：{content}')
    message=qwen_llm.invoke(input=prompt)
    state['messages'].append(message)
    print(message.content)
    state['search_keyword']=message.content
    return state

def node_search_baidu(state:BaiduSearchMessagesState):
    keyword=state['search_keyword']
    html=search_in_baidu_with_html(keyword)
    state['messages'].append(AIMessage(content=f'百度搜索结果：{html}'))
    state['search_results']=html
    return state

def node_reply_user(state:BaiduSearchMessagesState):
    question=state['search_question']
    baidu_search_result = state['search_results']

    result=qwen_llm.invoke(input=f"""
    # 要求
    请结合百度搜索的结果，回答用户的问题:{question}
    
    # 百度搜索的结果
    {baidu_search_result}
    
""")
    state['messages'].append(result)
    return state

state_graph = StateGraph(BaiduSearchMessagesState)
state_graph.add_node(key_extract_query_keyword,node_extract_query_keyword)
state_graph.add_node(key_search_baidu,node_search_baidu)
state_graph.add_node(key_reply_user,node_reply_user)

state_graph.add_edge(START,key_extract_query_keyword)
state_graph.add_edge(key_extract_query_keyword,key_search_baidu)
state_graph.add_edge(key_search_baidu,key_reply_user)
state_graph.add_edge(key_reply_user,END)

compiled_graph=state_graph.compile()
# output_graph_image(compiled_graph,'langgraph')

results=compiled_graph.stream({
    'messages':[('user','江门今天的天气如何？')]
})

for s in results:
    key=list(s)[0]
    print(s[key]['messages'][-1].content)
    print('-'*60)