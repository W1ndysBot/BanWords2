# script/BanWords2/main.py

import logging
import os
import sys
import json
import re

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
def init_BanWords2(group_id=None):
    os.makedirs(DATA_DIR, exist_ok=True)
    init_group_BanWords2_json(group_id)
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


# 添加违禁词词库，传入违禁词和权值和群号
def add_banword(word: str, weight: int, group_id: str = None) -> bool:
    """
    添加违禁词到词库

    Args:
        word (str): 要添加的违禁词
        weight (int): 违禁词的权值
        group_id (str, optional): 群号。若指定则添加到对应群的词库，否则添加到默认词库

    Returns:
        bool: 添加是否成功
    """
    try:
        # 根据是否传入group_id决定使用哪个json文件
        json_file = os.path.join(
            DATA_DIR, f"{group_id}.json" if group_id else "default.json"
        )

        # 确保目标文件存在
        if group_id:
            init_group_BanWords2_json(group_id)

        with open(json_file, "r") as f:
            ban_words = json.load(f)

        ban_words[word] = weight

        with open(json_file, "w") as f:
            json.dump(ban_words, f, ensure_ascii=False, indent=4)

        logging.info(
            f"添加{'群组' if group_id else '默认'}违禁词成功: {word}, 权值: {weight}"
            + (f", 群号: {group_id}" if group_id else "")
        )
        return True
    except Exception as e:
        logging.error(f"添加{'群组' if group_id else '默认'}违禁词失败: {e}")
        return False


# 从词库中删除违禁词
def del_banword(word: str, group_id: str = None) -> bool:
    """
    从词库中删除违禁词

    Args:
        word (str): 要删除的违禁词
        group_id (str, optional): 群号。若指定则从对应群的词库删除，否则从默认词库删除

    Returns:
        bool: 删除是否成功
    """
    try:
        json_file = os.path.join(
            DATA_DIR, f"{group_id}.json" if group_id else "default.json"
        )

        with open(json_file, "r") as f:
            ban_words = json.load(f)

        if word in ban_words:
            del ban_words[word]

            with open(json_file, "w") as f:
                json.dump(ban_words, f, ensure_ascii=False, indent=4)

            logging.info(
                f"删除{'群组' if group_id else '默认'}违禁词成功: {word}"
                + (f", 群号: {group_id}" if group_id else "")
            )
            return True
        return False

    except Exception as e:
        logging.error(f"删除{'群组' if group_id else '默认'}违禁词失败: {e}")
        return False


# 管理员命令函数
async def manager_command(websocket, raw_message, group_id):
    try:
        match = re.match("bw2add(.*) (\d+)", raw_message)
        if match:
            word = match.group(1)
            weight = int(match.group(2))
            if add_banword(word, weight, group_id):
                await send_group_msg(
                    websocket,
                    group_id,
                    f"群【{group_id}】添加违禁词成功: {word}, 权值: {weight}",
                )
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"群【{group_id}】添加违禁词失败: {word}, 权值: {weight}",
                )

        match = re.match("bw2del(.*)", raw_message)
        if match:
            word = match.group(1)
            if del_banword(word, group_id):
                await send_group_msg(
                    websocket,
                    group_id,
                    f"群【{group_id}】删除违禁词成功: {word}",
                )
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"群【{group_id}】删除违禁词失败: {word}",
                )

        match = re.match("bw2defaultadd(.*) (\d+)", raw_message)
        if match:
            word = match.group(1)
            weight = int(match.group(2))
            if add_banword(word, weight):
                await send_group_msg(
                    websocket,
                    group_id,
                    f"默认违禁词添加成功: {word}, 权值: {weight}",
                )
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"默认违禁词添加失败: {word}, 权值: {weight}",
                )

    except Exception as e:
        logging.error(f"处理BanWords2管理员命令失败: {e}")
        await send_group_msg(
            websocket, group_id, "处理BanWords2管理员命令失败，错误信息：" + str(e)
        )
        return


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

        # 初始化
        init_BanWords2()

        # 鉴权
        authorized = is_authorized(role, user_id)

        if authorized:
            # 管理员命令
            await manager_command(websocket, raw_message, group_id)

    except Exception as e:
        logging.error(f"处理BanWords2群消息失败: {e}")
        await send_group_msg(group_id, "处理BanWords2群消息失败，错误信息：" + str(e))
        return
