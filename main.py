# script/BanWords2/main.py

import logging
import os
import sys

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import owner_id
from app.api import *
from app.switch import load_switch, save_switch

# 数据存储路径，实际开发时，请将BanWords2替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "BanWords2",
)


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "BanWords2")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "BanWords2", status)


# 初始化
def init_BanWords2():
    os.makedirs(DATA_DIR, exist_ok=True)
    init_group_BanWords2_json(owner_id)
    init_default_BanWords2_json()


# 初始化分群违禁词JSON文件
def init_group_BanWords2_json(group_id):
    json_file = os.path.join(DATA_DIR, f"{group_id}.json")
    if not os.path.exists(json_file):
        with open(json_file, "w") as f:
            f.write("{}")
            logging.info(f"初始化分群违禁词JSON文件: {json_file}")


# 初始化默认违禁词JSON文件
def init_default_BanWords2_json():
    json_file = os.path.join(DATA_DIR, "default.json")
    if not os.path.exists(json_file):
        with open(json_file, "w") as f:
            f.write("{}")
            logging.info(f"初始化默认违禁词JSON文件: {json_file}")


# 群消息处理函数
async def handle_BanWords2_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))

    except Exception as e:
        logging.error(f"处理BanWords2群消息失败: {e}")
        await send_group_msg(group_id, "处理BanWords2群消息失败，错误信息：" + str(e))
        return
