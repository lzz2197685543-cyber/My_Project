from mcp.server.fastmcp import FastMCP
from app.code_agent.rag.rag import retrieve_index, create_client, workspace_id, upload_rag_file_to_bailian, \
    add_document_to_index, get_index_job_status
from typing import Annotated, List
from pydantic import Field

mcp = FastMCP()


@mcp.tool(name="query_rag", description='从百炼平台查询知识库信息')
def query_rag_from_bailian(query: Annotated[
    str, Field(description="访问知识库查询的内容", examples="终端的操作规范")]):
    bailian_client = create_client()

    index_id = 'vez3oeatuq'  # 知识库id
    rag = retrieve_index(bailian_client, workspace_id, index_id, query)

    result = ''

    for i in rag.body.data.nodes:
        result += f"""{i.text}"""

    return result


@mcp.tool(name="upload_local_file_to_bailian_rag", description='将本地的知识文件上传到百炼知识库')
def upload_rag_to_bailian(file_path:
Annotated[str, Field(description="本地知识文件的路径，需要传入绝对路径",
                     examples="D:\\sd14\\ai-agent\\app\\code_agent\\rag\\rag_test.txt")]):
    client = create_client()
    category_id = 'cate_786ad3bd6814418bb68a69cf244b3e73_17993206'
    index_id = 'vez3oeatuq'  # 知识库id
    file_id = upload_rag_file_to_bailian(client, category_id, workspace_id, file_path)

    return add_document_to_index(client, workspace_id, index_id, file_id)

@mcp.tool(name="query_bailian_rag_job_status", description='查询上传到百炼知识库中的知识文件的处理状态')
def query_bailian_rag_job_status(job_id:str):
    client = create_client()
    index_id = 'vez3oeatuq'  # 知识库id
    job_status=get_index_job_status(client,workspace_id,index_id,job_id)
    return job_status.body.data


if __name__ == '__main__':
    mcp.run(transport='stdio')
    # file_path='D:\\sd14\\ai-agent\\app\\code_agent\\rag\\terminal.txt'
    # res=upload_rag_to_bailian(file_path)
    # print(res)

    # job_id='cb0ce04e1b974e798843b86298e9731f'
    # res=query_bailian_rag_job_status(job_id)
    # print(res)