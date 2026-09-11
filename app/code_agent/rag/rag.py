import os
from dotenv import load_dotenv
import alibabacloud_bailian20231229.client as bailian_20231229_client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_tea_util import models as tea_util_models


import hashlib
import requests

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")
access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
workspace_id = os.getenv("WORKSPACE_ID")
index_id = 'vez3oeatuq' # 知识库id

category_id = 'cate_786ad3bd6814418bb68a69cf244b3e73_17993206' # 文件类目id


# 1. 初始化客户端
def create_client() -> bailian_20231229_client.Client:
    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
    )

    config.endpoint = 'bailian.cn-beijing.aliyuncs.com'
    return bailian_20231229_client.Client(config)


def retrieve_index(client, workspace_id, index_id, query):
    retrieve_request = bailian_20231229_models.RetrieveRequest(
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





# =========================== 一、百炼知识库创建 =================================


# ========== 1.获得上传凭证============
def apply_lease(client, category_id, file_name, file_md5, file_size, workspace_id):
    headers = {}
    runtime = tea_util_models.RuntimeOptions()

    request = bailian_20231229_models.ApplyFileUploadLeaseRequest(
        file_name=file_name,
        md_5=file_md5,
        size_in_bytes=file_size
    )

    return client.apply_file_upload_lease_with_options(
        category_id,
        workspace_id,
        request,
        headers,
        runtime
    )


def calculate_md5(file_path: str) -> str:
    """
    计算文件的 MD5 哈希值。

    参数:
        file_path (str): 文件路径。

    返回:
        str: 文件的 MD5 哈希值。
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_info(file_path):
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_md5 = calculate_md5(file_path)
    return file_name, file_md5, file_size

def apply_lease_by_file_path(client, category_id, workspace_id,file_path):
    file_name, file_md5, file_size = get_file_info(file_path)
    res=apply_lease(client, category_id, file_name, file_md5, file_size,workspace_id)
    lease_id = res.body.data.file_upload_lease_id
    headers = res.body.data.param.headers
    upload_url = res.body.data.param.url
    return lease_id, upload_url, headers


# ========== 2.上传文件============

# 2.1 将文件上传至阿里云百炼
def upload_file_to_bailian(upload_url,headers,file_path):
    with open(file_path, "rb") as f:
        file_content=f.read()

    upload_headers = {
        'Content-Type': headers['Content-Type'],
        "X-bailian-extra": headers["X-bailian-extra"],
    }
    response = requests.put(upload_url, data=file_content, headers=upload_headers)
    print(response.status_code)
    response.raise_for_status()

# 2.2 将文件添加到指定类目
def add_file_to_bailian_category(client,lease_id:str,parser:str,category_id:str,workspace_id:str):
    """
        将文件添加到阿里云百炼指定类目。

        参数:
            client: 阿里云百炼客户端。
            lease_id (str): 租约 ID。
            parser (str): 用于文件的解析器。
            category_id (str): 类别 ID。
            workspace_id (str): 业务空间 ID。

        返回:
            阿里云百炼服务的响应。
        """
    headers = {}
    request = bailian_20231229_models.AddFileRequest(
        lease_id=lease_id,
        parser=parser,
        category_id=category_id,
    )
    runtime = tea_util_models.RuntimeOptions()
    return client.add_file_with_options(workspace_id, request, headers, runtime)

# 2.3 查询上传状态
def describe_file(client, workspace_id, file_id):
    """
    获取文档的基本信息。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        file_id (str): 文档ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    runtime = tea_util_models.RuntimeOptions()
    return client.describe_file_with_options(workspace_id, file_id, headers, runtime)


# ========== 3.创建知识库============
def create_index(client,workspace_id,file_id,name,structure_type="unstructured",source_type="DATA_CENTER_FILE",sink_type="BUILT_IN"):
    headers={}
    runtime = tea_util_models.RuntimeOptions()
    request=bailian_20231229_models.CreateIndexRequest(
        structure_type=structure_type,
        source_type=source_type,
        sink_type=sink_type,
        name=name,
        document_ids=[file_id]
    )
    return client.create_index_with_options(workspace_id, request, headers, runtime)

# ========== 4.知识文件向量化============
def submit_index(client,workspace_id,index_id):
    headers = {}
    runtime = tea_util_models.RuntimeOptions()
    submit_index_job_request = bailian_20231229_models.SubmitIndexJobRequest(
        index_id=index_id
    )
    return client.submit_index_job_with_options(workspace_id, submit_index_job_request, headers, runtime)

# 查询向量化任务状态
def get_index_job_status(client, workspace_id, index_id, job_id):
    """
    查询索引任务状态。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。
        job_id (str): 任务ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    get_index_job_status_request = bailian_20231229_models.GetIndexJobStatusRequest(
        index_id=index_id,
        job_id=job_id
    )
    runtime = tea_util_models.RuntimeOptions()
    return client.get_index_job_status_with_options(workspace_id, get_index_job_status_request, headers, runtime)


# ========== 5.查询知识库============
def list_indices(client, workspace_id):
    """
    获取指定业务空间下一个或多个知识库的详细信息。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    list_indices_request = bailian_20231229_models.ListIndicesRequest()
    runtime = tea_util_models.RuntimeOptions()

    return client.list_indices_with_options(workspace_id, list_indices_request, headers, runtime)


# ===========================二、百炼知识库更新=================================
# 追加文件到知识库
def submit_index_add_documents_job(client, workspace_id, index_id, file_id, source_type="DATA_CENTER_FILE"):
    """
    向一个非结构化知识库追加导入已解析的文档。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。
        file_id (str): 文档ID。
        source_type(str): 数据类型。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    submit_index_add_documents_job_request = bailian_20231229_models.SubmitIndexAddDocumentsJobRequest(
        index_id=index_id,
        document_ids=[file_id],
        source_type=source_type
    )
    runtime = tea_util_models.RuntimeOptions()
    return client.submit_index_add_documents_job_with_options(workspace_id, submit_index_add_documents_job_request, headers, runtime)


# ===========================三、百炼知识库删除=================================
# 删除知识库下的指定文件
def delete_index_document(client, workspace_id, index_id, file_id):
    """
    从指定的非结构化知识库中永久删除一个或多个文档。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。
        file_id (str): 文档ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    delete_index_document_request = bailian_20231229_models.DeleteIndexDocumentRequest(
        index_id=index_id,
        document_ids=[file_id]
    )
    runtime = tea_util_models.RuntimeOptions()
    return client.delete_index_document_with_options(workspace_id, delete_index_document_request, headers, runtime)

# 删除知识库
def delete_index(client, workspace_id, index_id):
    """
    永久性删除指定的知识库。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    delete_index_request = bailian_20231229_models.DeleteIndexRequest(
        index_id=index_id
    )
    runtime = tea_util_models.RuntimeOptions()
    return client.delete_index_with_options(workspace_id, delete_index_request, headers, runtime)




def upload_rag_file_to_bailian(client,category_id,workspace_id,file_path):
    """
    上传文件到百炼数据中心，并添加到指定分类
    参数：
        client:百炼客户端
        workspace_id:业务空间ID
        category_id:分类id
        file_path:文件路径
    return:
        文件的上传状态
    """
    # 1.申请文件租约
    lease_id, upload_url, headers = apply_lease_by_file_path(client, category_id, workspace_id, file_path)
    print('-'*60)
    print('文件租约申请成功')
    print('lease_id:',lease_id)
    print('upload_url:',upload_url)
    print('headers:',headers)
    print('-'*60)
    print()

    # 2.上传文件到百炼数据中心
    upload_file_to_bailian(upload_url, headers, file_path)
    print('-' * 60)
    print('上传文件到百炼数据中心成功')
    print('-' * 60)
    print()

    # 3.将文件添加到指定分类
    add_file_response = add_file_to_bailian_category(client, lease_id, "DASHSCOPE_DOCMIND", category_id, workspace_id)
    file_id = add_file_response.body.data.file_id
    print('-' * 60)
    print('将文件添加到指定分类成功')
    print('file_id:',file_id)
    print('-' * 60)

    # 4.查看文件状态
    describe_file_res = describe_file(client, workspace_id, file_id=file_id)

    return file_id


def add_document_to_index(client,workspace_id,index_id,file_id):
    job_res=submit_index_add_documents_job(client,workspace_id,index_id,file_id)
    job_id=job_res.body.data.id
    job_status=get_index_job_status(client,workspace_id,index_id,job_id)
    return job_status.body.data



if __name__ == '__main__':
#     mcp.run(transport='stdio')
    # print(query_rag_from_bailian('终端操作规范'))
    # file_path = 'D:\\sd14\\ai-agent\\app\\code_agent\\rag\\rag_test.txt'
    client=create_client()

    job_id = 'cb0ce04e1b974e798843b86298e9731f'
    res = get_index_job_status(client, workspace_id, index_id, job_id)
    print(res)
