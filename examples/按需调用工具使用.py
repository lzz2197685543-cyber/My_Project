# 一、AI 对话
# from ecommerce_automation.ai import ask_ai, AIClient
#
#
# title = ask_ai(
#     "把这个商品标题改写成英文：儿童积木",
#     api_key="sk-00000",# 填写正确的api_key
#     base_url='https://codex666ai.com/v1',
#     model="deepseek-v4.1-flash",
#     system_prompt="只返回改写后的标题",
#     temperature=0.2,
# )
# print(title)

# # 同一程序要多次请求时，复用 AIClient 可避免重复创建连接。
# with AIClient(api_key=api_key, base_url=ai_base_url, model="your-model") as ai:
#     another_title = ai.simple_chat("继续改写下一个商品标题")


# 二、钉钉机器人消息(群聊)
# from ecommerce_automation.notify import DingTalkNotifier, send_dingtalk_markdown
# bot_token = os.getenv("DINGTALK_BOT_TOKEN")
# bot_secret = os.getenv("DINGTALK_BOT_SECRET")
#
# send_dingtalk_markdown(bot_token, bot_secret, "库存同步", "已更新 **18** 个 SKU")
#
# # 也可以复用客户端连续发消息：
# with DingTalkNotifier(bot_token, bot_secret) as bot:
#     bot.send_text("同步完成", at_mobiles=["18078418293"])

# 三、钉钉多维表上传
# import os
# from dotenv import load_dotenv
# load_dotenv()
#
# from ecommerce_automation.dingtalk import (
#     delete_dingtalk_records,
#     list_dingtalk_sheets,
#     query_dingtalk_records,
#     delete_dingtalk_sheet
# )
#
# client_id = os.getenv("DINGTALK_CLIENT_ID")
# client_secret = os.getenv("DINGTALK_CLIENT_SECRET")
# base_id = os.getenv("DINGTALK_BASE_ID")
# sheet_id = os.getenv("DINGTALK_SHEET_ID")
# operator_id = os.getenv("DINGTALK_OPERATOR_ID")
# agent_id = os.getenv("DINGTALK_AGENT_ID")
# result = upload_dingtalk_records(
#     [{"SKU": "SKU-001", "库存": 18}, {"SKU": "SKU-002", "库存": 6}],
#     client_id=client_id,
#     client_secret=client_secret,
#     base_id=base_id,
#     sheet_id=sheet_id,
#     operator_id=operator_id,
#     batch_size=100,
# )

# 要复用 access token/连接时，再显式管理客户端生命周期：
# with DingTalkTokenProvider(client_id, client_secret) as token:
#     with DingTalkTableClient(base_id, sheet_id, operator_id, token) as table:
#         result = table.upload_records(
#             [{"SKU": "SKU-001", "库存": 18}, {"SKU": "SKU-002", "库存": 6}],
#             batch_size=100,
#             delay=0.1,
#         )


# sheets = list_dingtalk_sheets(
#     client_id=client_id,
#     client_secret=client_secret,
#     base_id=base_id,
#     operator_id=operator_id,
# )
# for sheet in sheets:
#     print(f"{sheet['name']} -> {sheet['id']}")
#
# if sheet_id:
#     page = query_dingtalk_records(
#         client_id=client_id,
#         client_secret=client_secret,
#         base_id=base_id,
#         sheet_id=sheet_id,
#         operator_id=operator_id,
#         max_results=100,
#     )
#
#     for record in page.get("records", []):
#         print("record id:", record.get("id"))
#         print("record fields:", record.get("fields"))

# 删除操作不可撤销。先从查询结果中选定真实记录 id，再显式启用确认：
# record_ids_to_delete = ['T1Rhs2Geiy']  # 填入 page["records"] 中确认过的记录 id
# confirm_delete_records = True
# if confirm_delete_records and record_ids_to_delete:
#     delete_dingtalk_records(
#         record_ids_to_delete, client_id=client_id, client_secret=client_secret,
#         base_id=base_id, sheet_id=sheet_id, operator_id=operator_id,
#     )

# 删除整个工作表影响该表全部数据；使用 list_dingtalk_sheets() 返回的真实 id。
# sheet_id_to_delete = sheet_id
# confirm_delete_sheet = True
# if confirm_delete_sheet and sheet_id_to_delete:
#     delete_dingtalk_sheet(
#         sheet_id_to_delete, client_id=client_id, client_secret=client_secret,
#         base_id=base_id, operator_id=operator_id,
#     )


# 四、钉钉工作通知和用户 ID
# from ecommerce_automation.dingtalk_work import (
#     DingTalkWorkNotifier,
#     get_dingtalk_operator_id_by_mobile,
#     get_dingtalk_union_id_by_user_id,
#     get_dingtalk_user_id_by_mobile,
#     send_dingtalk_work_text,
# )
#
# user_id = get_dingtalk_user_id_by_mobile(
#     "1807841", client_id=client_id, client_secret=client_secret,
# )
# print(user_id)
# s_operator_id = get_dingtalk_operator_id_by_mobile(
#     "18078", client_id=client_id, client_secret=client_secret,
# )
# print(s_operator_id)
# same_operator_id = get_dingtalk_union_id_by_user_id(
#     user_id, client_id=client_id, client_secret=client_secret,
# )
# print(same_operator_id)
# send_dingtalk_work_text(
#     user_id, "库存同步完成", "本次更新 18 个商品",
#     client_id=client_id, client_secret=client_secret, agent_id=agent_id,
# )
#
# # 连续查询或发送时，复用 notifier 和 access token。
# with DingTalkWorkNotifier(client_id, client_secret, agent_id) as work:
#     user_id = work.get_user_id_by_mobile("13800000000")
#     s_operator_id = work.get_union_id_by_user_id(user_id)
#     work.send_text(user_id, "任务完成", "处理结果已写入多维表")


# 五、普通函数式任务队列
from ecommerce_automation.tasks import run_tasks

def publish_one(product):
    # 这里仍然是项目自己的普通业务代码
    return {"sku": product["sku"], "published": True}

summary = run_tasks(
    products,
    publish_one,
    db_path="data/publish_tasks.sqlite3",
    key="sku",
    queue="publish_products",
)
