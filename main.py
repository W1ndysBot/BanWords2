# script/BanWords2/main.py

import logging
import os
import sys
import re

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import *
from app.api import *
from app.switch import load_switch, save_switch
from app.scripts.BanWords2.BanWordsManager import (
    add_ban_word,
    remove_ban_word,
    get_ban_words,
)
from app.scripts.BanWords2.isBanWords import is_ban_words
from app.api import set_group_ban, set_group_kick

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


# 处理元事件，用于启动时确保数据目录存在
async def handle_meta_event(websocket, msg):
    """处理元事件"""
    os.makedirs(DATA_DIR, exist_ok=True)


# 处理开关状态
async def toggle_function_status(websocket, group_id, message_id, authorized):
    if not authorized:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]❌❌❌你没有权限对BanWords2功能进行操作,请联系管理员。",
        )
        return

    if load_function_status(group_id):
        save_function_status(group_id, False)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]🚫🚫🚫BanWords2功能已关闭",
        )
    else:
        save_function_status(group_id, True)
        await send_group_msg(
            websocket, group_id, f"[CQ:reply,id={message_id}]✅✅✅BanWords2功能已开启"
        )


# 群消息处理函数
async def handle_group_message(websocket, msg):
    """处理群消息"""
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        message_id = str(msg.get("message_id"))
        authorized = user_id in owner_id

        # 处理开关命令
        if raw_message == "bw2":
            await toggle_function_status(websocket, group_id, message_id, authorized)
            return
        # 检查功能是否开启
        if load_function_status(group_id):
            # 其他群消息处理逻辑
            add_ban_words_match = re.search(r"bw2add(\S+) (\d+)", raw_message)
            remove_ban_words_match = re.search(r"bw2rm(\S+)", raw_message)

            # 添加查看违禁词列表命令处理
            if raw_message == "bw2list":
                await list_ban_words(
                    websocket, group_id, user_id, message_id, authorized
                )
            elif add_ban_words_match:
                await add_ban_word(
                    websocket,
                    group_id,
                    message_id,
                    authorized,
                    add_ban_words_match.group(1),
                    add_ban_words_match.group(2),
                )
            elif remove_ban_words_match:
                await remove_ban_word(
                    websocket,
                    group_id,
                    message_id,
                    authorized,
                    remove_ban_words_match.group(1),
                )
            else:
                # 检查用户发言权值和是否超过阈值
                await is_ban_words(
                    websocket, group_id, user_id, raw_message, message_id
                )
    except Exception as e:
        logging.error(f"处理BanWords2群消息失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理BanWords2群消息失败，错误信息：" + str(e),
        )
        return


# 私聊消息处理函数
async def handle_private_message(websocket, msg):
    """处理私聊消息"""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        raw_message = str(msg.get("raw_message"))

        # 检查是否是管理员
        authorized = user_id in owner_id
        if not authorized:
            return

        # 处理解禁命令: unban群号 用户ID
        unban_match = re.search(r"unban(\d+) (\d+)", raw_message)
        if unban_match:
            group_id = unban_match.group(1)
            target_user_id = unban_match.group(2)
            await handle_unban(websocket, group_id, target_user_id, user_id)
            return

        # 处理踢出命令: t群号 用户ID
        kick_match = re.search(r"t(\d+) (\d+)", raw_message)
        if kick_match:
            group_id = kick_match.group(1)
            target_user_id = kick_match.group(2)
            await handle_kick(
                websocket, group_id, target_user_id, user_id, reject_add_request=False
            )
            return

        # 处理踢出并拉黑命令: tl群号 用户ID
        kick_blacklist_match = re.search(r"tl(\d+) (\d+)", raw_message)
        if kick_blacklist_match:
            group_id = kick_blacklist_match.group(1)
            target_user_id = kick_blacklist_match.group(2)
            await handle_kick(
                websocket, group_id, target_user_id, user_id, reject_add_request=True
            )
            return
    except Exception as e:
        logging.error(f"处理BanWords2私聊消息失败: {e}")
        await send_private_msg(
            websocket,
            msg.get("user_id"),
            "处理BanWords2私聊消息失败，错误信息：" + str(e),
        )
        return


# 处理解禁命令
async def handle_unban(websocket, group_id, target_user_id, operator_id):
    """处理解禁命令"""
    try:
        # 调用解禁API（设置禁言时间为0表示解除禁言）
        await set_group_ban(websocket, group_id, target_user_id, 0)
        # 通知操作者解禁成功
        await send_private_msg(
            websocket,
            operator_id,
            f"✅✅✅已解除群 {group_id} 中用户 {target_user_id} 的禁言。",
        )
    except Exception as e:
        logging.error(f"处理解禁命令失败: {e}")
        await send_private_msg(
            websocket, operator_id, f"❌❌❌解除禁言失败，错误信息：{str(e)}"
        )


# 处理踢出命令
async def handle_kick(
    websocket, group_id, target_user_id, operator_id, reject_add_request=False
):
    """处理踢出命令，可选择是否拉黑"""
    try:
        # 调用踢出API
        await set_group_kick(websocket, group_id, target_user_id, reject_add_request)

        # 构建操作结果消息
        operation_type = "踢出并拉黑" if reject_add_request else "踢出"
        await send_private_msg(
            websocket,
            operator_id,
            f"✅✅✅已{operation_type}群 {group_id} 中的用户 {target_user_id}。",
        )
    except Exception as e:
        logging.error(f"处理踢出命令失败: {e}")
        # 构建错误消息
        operation_type = "踢出并拉黑" if reject_add_request else "踢出"
        await send_private_msg(
            websocket,
            operator_id,
            f"❌❌❌{operation_type}操作失败，错误信息：{str(e)}",
        )


# 群通知处理函数
async def handle_group_notice(websocket, msg):
    """处理群通知"""
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))

    except Exception as e:
        logging.error(f"处理BanWords2群通知失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            "处理BanWords2群通知失败，错误信息：" + str(e),
        )
        return


# 处理群历史消息
async def process_group_msg_history(websocket, msg):
    """处理群历史消息"""
    echo = msg.get("echo")
    if echo and echo.startswith("get_group_msg_history_"):
        # 解析群号，用户ID，备注
        parts = echo.replace("get_group_msg_history_", "").split("_")
        if len(parts) >= 3:
            group_id = parts[0]
            user_id = parts[1]
            note = parts[2]
            if note == "isBanWords":
                # 获取历史消息列表
                message_list = msg.get("data", {}).get("messages", [])
                if not message_list:
                    logging.warning(f"未找到群 {group_id} 的历史消息")
                    return

                # 遍历消息列表，查找指定用户ID的消息并撤回
                for message in message_list:
                    if str(message.get("user_id")) == user_id:
                        # 获取消息ID
                        message_id = message.get("message_id")
                        if message_id:
                            try:
                                # 撤回消息
                                await delete_msg(websocket, message_id)
                                logging.info(
                                    f"[扫描历史消息]已撤回用户 {user_id} 在群 {group_id} 的消息: {message_id}"
                                )
                            except Exception as e:
                                logging.error(f"撤回消息失败: {e}")


# 回应事件处理函数
async def handle_response(websocket, msg):
    """处理回调事件"""
    echo = msg.get("echo")
    if echo and echo.startswith("get_group_msg_history_"):
        # 回调处理逻辑
        await process_group_msg_history(websocket, msg)


# 添加查看违禁词列表功能
async def list_ban_words(websocket, group_id, user_id, message_id, authorized):
    """查看违禁词列表"""
    if not authorized:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]❌❌❌你没有权限查看违禁词列表,请联系管理员。",
        )
        return

    try:
        # 获取违禁词列表
        ban_words = get_ban_words(group_id)

        if not ban_words:
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]当前群组没有设置违禁词。",
            )
            return

        # 在群里回复已发送私聊消息
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]✅✅✅违禁词列表已通过私聊发送给您，请查收。",
        )

        # 构建违禁词列表消息
        message = f"群 {group_id} 的违禁词列表：\n"
        message += "====================\n"
        message += "违禁词 | 权重\n"
        message += "--------------------\n"

        for word, weight in ban_words.items():
            message += f"{word} | {weight}\n"

        message += "====================\n"
        message += "共 {0} 个违禁词".format(len(ban_words))

        # 通过私聊发送违禁词列表
        await send_private_msg(websocket, user_id, message)

    except Exception as e:
        logging.error(f"查看违禁词列表失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]❌❌❌查看违禁词列表失败: {str(e)}",
        )


# 统一事件处理入口
async def handle_events(websocket, msg):
    """统一事件处理入口"""
    post_type = msg.get("post_type", "response")  # 添加默认值
    try:
        # 处理回调事件
        if msg.get("status") == "ok":
            await handle_response(websocket, msg)
            return

        post_type = msg.get("post_type")

        # 处理元事件
        if post_type == "meta_event":
            await handle_meta_event(websocket, msg)

        # 处理消息事件
        elif post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await handle_group_message(websocket, msg)
            elif message_type == "private":
                await handle_private_message(websocket, msg)

        # 处理通知事件
        elif post_type == "notice":
            if msg.get("notice_type") == "group":
                await handle_group_notice(websocket, msg)

    except Exception as e:
        error_type = {
            "message": "消息",
            "notice": "通知",
            "request": "请求",
            "meta_event": "元事件",
        }.get(post_type, "未知")

        logging.error(f"处理BanWords2{error_type}事件失败: {e}")

        # 发送错误提示
        if post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await send_group_msg(
                    websocket,
                    msg.get("group_id"),
                    f"处理BanWords2{error_type}事件失败，错误信息：{str(e)}",
                )
            elif message_type == "private":
                await send_private_msg(
                    websocket,
                    msg.get("user_id"),
                    f"处理BanWords2{error_type}事件失败，错误信息：{str(e)}",
                )
