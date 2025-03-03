import logging
from app.scripts.BanWords2.BanWordsManager import get_ban_words, get_default_ban_words
from app.api import set_group_ban, send_group_msg, send_private_msg, delete_msg
from app.config import owner_id
from datetime import datetime
import asyncio


async def is_ban_words(websocket, group_id, user_id, raw_message, message_id):
    """检查用户发言权值和是否超过阈值，包含默认违禁词和群组特定违禁词"""
    try:
        all_weight = 0
        # 获取默认违禁词和群组特定违禁词
        default_ban_words = get_default_ban_words()
        group_ban_words = get_ban_words(group_id)

        # 合并违禁词字典，群组特定的违禁词优先级高于默认违禁词
        ban_words = default_ban_words.copy()
        ban_words.update(group_ban_words)

        for word in ban_words:
            try:
                weight_value = int(ban_words[word])
                if word in raw_message:
                    all_weight += weight_value
            except ValueError:
                logging.warning(f"无效的权重值: {word}: {ban_words[word]}")
                continue

        if all_weight > 10:
            await delete_msg(websocket, message_id)
            await set_group_ban(websocket, group_id, user_id, 60 * 10)
            await send_private_msg(
                websocket,
                owner_id[0],
                f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"群号：{group_id}\n"
                f"用户：{user_id}\n"
                f"发送的消息超过了阈值，已自动禁言，原始消息如下",
            )
            await asyncio.sleep(0.5)
            await send_private_msg(websocket, owner_id[0], raw_message)
    except Exception as e:
        logging.error(f"检查违禁词失败: {e}")
        return False
