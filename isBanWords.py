import logging
import re
from app.scripts.BanWords2.BanWordsManager import get_ban_words, get_default_ban_words
from app.api import set_group_ban, send_private_msg, delete_msg, get_group_msg_history
from app.config import owner_id
from datetime import datetime
import asyncio
import base64


async def is_ban_words(websocket, group_id, user_id, raw_message, message_id):
    """检查用户发言权值和是否超过阈值，包含默认违禁词和群组特定违禁词"""
    try:

        # 预处理
        raw_message = raw_message.replace(" ", "")
        raw_message = raw_message.replace("\n", "")
        # 删除标点
        raw_message = re.sub(r"[^\w\s]", "", raw_message)

        all_weight = 0
        # 获取默认违禁词和群组特定违禁词
        default_ban_words = get_default_ban_words()
        group_ban_words = get_ban_words(group_id)

        # 合并违禁词字典，群组特定的违禁词优先级高于默认违禁词
        ban_words = default_ban_words.copy()
        ban_words.update(group_ban_words)

        # 记录触发的违禁词列表
        triggered_words = []

        for word, weight in ban_words.items():
            try:
                weight_value = int(weight)
                # 首先尝试正则表达式匹配
                try:
                    if re.search(word, raw_message):
                        all_weight += weight_value
                        triggered_words.append(f"{word}({weight_value})")
                        continue
                except re.error:
                    # 如果正则表达式无效，退回到普通字符串匹配
                    if word in raw_message:
                        all_weight += weight_value
                        triggered_words.append(f"{word}({weight_value})")
            except ValueError:
                logging.warning(f"无效的权重值: {word}: {ban_words[word]}")
                continue

        if all_weight > 10:
            await delete_msg(websocket, message_id)
            await set_group_ban(websocket, group_id, user_id, 60 * 10)
            # 查询十条历史记录
            await get_group_msg_history(
                websocket, group_id, 10, user_id, note="isBanWords"
            )
            await send_private_msg(
                websocket,
                owner_id[0],
                f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"群号：{group_id}\n"
                f"用户：{user_id}\n"
                f"触发的违禁词列表：{', '.join(triggered_words)}\n"
                f"总权重：{all_weight}\n"
                f"发送的消息超过了阈值，已自动禁言，原始消息base64编码如下",
            )
            await asyncio.sleep(0.5)

            encoded_message = base64.b64encode(raw_message.encode("utf-8")).decode(
                "utf-8"
            )
            await send_private_msg(websocket, owner_id[0], encoded_message)
            await asyncio.sleep(0.5)
            await send_private_msg(websocket, owner_id[0], f"unban{group_id} {user_id}")
            await send_private_msg(websocket, owner_id[0], f"t{group_id} {user_id}")
            await send_private_msg(websocket, owner_id[0], f"tl{group_id} {user_id}")
    except Exception as e:
        logging.error(f"检查违禁词失败: {e}")
        return False
