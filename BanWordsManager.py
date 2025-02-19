import os
import json
import logging
from app.api import send_group_msg

# 数据存储路径，实际开发时，请将BanWords2替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "BanWords2",
)


def get_ban_words(group_id):
    """
    获取违禁词列表
    :param group_id: 群号
    :return: 违禁词列表
    """
    try:
        with open(
            os.path.join(DATA_DIR, f"{group_id}.json"), "r", encoding="utf-8"
        ) as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果文件不存在,返回空列表
        return []
    except json.JSONDecodeError:
        # JSON解析错误,返回空列表
        return []
    except Exception as e:
        # 其他异常,记录日志并返回空列表
        logging.error(f"获取违禁词列表失败: {e}")
        return []


async def add_ban_word(websocket, group_id, message_id, authorized, word, weight):
    """
    添加违禁词

    group_id: 群号
    message_id: 消息ID
    authorized: 是否授权
    word: 违禁词
    weight: 违禁词权重
    """
    try:
        if not authorized:
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]❌❌❌你没有权限对BanWords2功能进行操作,请联系管理员。",
            )
            return
        # 获取违禁词列表
        ban_words = get_ban_words(group_id)
        # 添加违禁词到字典
        ban_words[word] = weight
        # 保存违禁词列表
        with open(
            os.path.join(DATA_DIR, f"{group_id}.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(ban_words, f, ensure_ascii=False, indent=4)

        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]✅✅✅违禁词【{word}权值{weight}】已添加。",
        )
    except Exception as e:
        logging.error(f"添加违禁词失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]❌❌❌添加违禁词失败: {str(e)}",
        )


async def remove_ban_word(websocket, group_id, message_id, authorized, word):
    """
    删除违禁词
    group_id: 群号
    word: 违禁词
    """
    try:
        if not authorized:
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]❌❌❌你没有权限对BanWords2功能进行操作,请联系管理员。",
            )
            return
        # 获取违禁词列表
        ban_words = get_ban_words(group_id)
        # 删除违禁词
        if word in ban_words:
            del ban_words[word]
        # 保存违禁词列表
        with open(
            os.path.join(DATA_DIR, f"{group_id}.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(ban_words, f, ensure_ascii=False, indent=4)

        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]✅✅✅违禁词【{word}】已删除。",
        )
    except Exception as e:
        logging.error(f"删除违禁词失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]❌❌❌删除违禁词失败: {str(e)}",
        )
