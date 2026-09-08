import os
from dotenv import load_dotenv
import alibabacloud_bailian20231229.client as bailian_20231229_client
from  alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_util import models as tea_util_models

from mcp.server.fastmcp import FastMCP
from typing import Annotated, List
from pydantic import Field

mcp = FastMCP()

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")
access_key_id =os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
workspace_id=os.getenv("WORKSPACE_ID")
index_id='i3o22as2gt'


# 1. 初始化客户端
def create_client()->bailian_20231229_client.Client:
    config=open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
    )

    config.endpoint = 'bailian.cn-beijing.aliyuncs.com'
    return bailian_20231229_client.Client(config)

def retrieve_index(client,workspace_id,index_id,query):
    retrieve_request=bailian_20231229_models.RetrieveRequest(
        index_id=index_id,
        query=query,
    )
    runtime = tea_util_models.RuntimeOptions()
    return client.retrieve_with_options(
        workspace_id,
        retrieve_request,
        {},
        runtime,
    )

@mcp.tool(name="query_rag",description='从百炼平台查询知识库信息')
def query_rag_from_bailian(query:Annotated[
    str, Field(description="访问知识库查询的内容", examples="终端的操作规范")]):
    bailian_client=create_client()
    rag=retrieve_index(bailian_client,workspace_id,index_id,query)

    result=''

    for i in rag.body.data.nodes:
        result+=f"""{i.text}"""

    return result

if __name__ == '__main__':
    mcp.run(transport='stdio')
    # print(query_rag_from_bailian('终端操作规范'))