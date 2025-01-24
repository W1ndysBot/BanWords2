# script/BanWords2/main.py

import logging
import os
import sys
import json
import re
import asyncio
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import *
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
def init_BanWords2(group_id):
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


# 画图，传入的文案画出白底黑字图片，边界自适应
def draw_text(text: str, font_size: int = 30, font_path: str = None) -> str:
    """
    根据传入的文本生成白底黑字的图片，并返回base64编码的图片数据

    Args:
        text (str): 要绘制的文本

        font_size (int, optional): 字体大小，默认为20
        font_path (str, optional): 字体文件路径，默认为None使用默认字体

    Returns:
        str: base64编码的图片数据
    """
    try:
        # 使用指定字体文件或尝试使用Arial字体，若失败则使用默认字体
        try:
            font = (
                ImageFont.truetype(font_path, font_size)
                if font_path
                else ImageFont.truetype("msyh.ttc", font_size)
            )
        except IOError:
            font = ImageFont.load_default()

        # 计算文本尺寸
        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # 创建白底图片
        img = Image.new("RGB", (text_width + 20, text_height + 20), color="white")
        draw = ImageDraw.Draw(img)

        # 绘制黑字
        draw.text((10, 10), text, font=font, fill="black")

        # 将图片保存到内存中
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        logging.info("生成文本图片成功")
        return img_base64
    except Exception as e:
        logging.error(f"生成文本图片失败: {e}")
        return ""


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

        with open(json_file, "r", encoding="utf-8") as f:
            ban_words = json.load(f)

        ban_words[word] = weight

        with open(json_file, "w", encoding="utf-8") as f:
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

        with open(json_file, "r", encoding="utf-8") as f:
            ban_words = json.load(f)

        if word in ban_words:
            del ban_words[word]

            with open(json_file, "w", encoding="utf-8") as f:
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
async def manager_command(websocket, raw_message, group_id, message_id):
    try:
        # 添加违禁词
        match = re.match(r"bw2add(.*) (\d+)", raw_message)
        if match:
            word = match.group(1)
            weight = int(match.group(2))
            if add_banword(word, weight, group_id):
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]群【{group_id}】添加违禁词成功: {word}, 权值: {weight}",
                )
                return
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]群【{group_id}】添加违禁词失败: {word}, 权值: {weight}",
                )
                return
        # 删除违禁词
        match = re.match("bw2del(.*)", raw_message)
        if match:
            word = match.group(1)
            if del_banword(word, group_id):
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]群【{group_id}】删除违禁词成功: {word}",
                )
                return
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]群【{group_id}】删除违禁词失败: {word}",
                )
                return
        # 添加默认违禁词
        match = re.match(r"bw2defaultadd(.*) (\d+)", raw_message)
        if match:
            word = match.group(1)
            weight = int(match.group(2))
            if add_banword(word, weight):
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]默认违禁词添加成功: {word}, 权值: {weight}",
                )
                return
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]默认违禁词添加失败: {word}, 权值: {weight}",
                )
                return
        # 删除默认违禁词
        match = re.match("bw2defaultdel(.*)", raw_message)
        if match:
            word = match.group(1)
            if del_banword(word):
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]默认违禁词删除成功: {word}",
                )
                return

        # 查看默认违禁词列表
        match = re.match("bw2defaultlist", raw_message)
        if match:
            default_ban_words = get_banword_list()
            default_ban_words_list = "\n".join(
                [f"{word}: {weight}" for word, weight in default_ban_words.items()]
            )
            base64_default_ban_words_list = draw_text(default_ban_words_list)
            if base64_default_ban_words_list:
                # 拼接完整base64图片
                base64_default_ban_words_list = (
                    f"[CQ:image,file=base64://{base64_default_ban_words_list}]"
                )
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]"
                    + f"默认违禁词列表:\n{base64_default_ban_words_list}",
                )
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]"
                    + f"默认违禁词列表:\n{default_ban_words_list}",
                )
            return

        # 查看分群违禁词列表
        match = re.match("bw2list", raw_message)
        if match:
            ban_words = get_banword_list(group_id)
            ban_words_list = "\n".join(
                [f"{word}: {weight}" for word, weight in ban_words.items()]
            )
            base64_ban_words_list = draw_text(ban_words_list)
            if base64_ban_words_list:
                # 拼接完整base64图片
                base64_ban_words_list = (
                    f"[CQ:image,file=base64://{base64_ban_words_list}]"
                )
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]"
                    + f"分群违禁词列表:\n{base64_ban_words_list}",
                )
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]"
                    + f"分群违禁词列表:\n{ban_words_list}",
                )
            return

        # 未识别命令错误提示
        match = re.match("bw2(.*)", raw_message)
        if match:
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]未识别命令: {raw_message}"
                + f"\n\nbw2add违禁词 权值\nbw2del违禁词\nbw2defaultadd违禁词 权值\nbw2defaultdel违禁词\nbw2list\nbw2defaultlist",
            )
            return

    except Exception as e:
        logging.error(f"处理BanWords2管理员命令失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]处理BanWords2管理员命令失败，错误信息：{e}",
        )
        return


# 获取违禁词列表
def get_banword_list(group_id: str = None) -> dict:
    """
    获取指定群组或默认的违禁词列表

    Args:
        group_id (str, optional): 群号。若指定则获取对应群的违禁词列表，否则获取默认违禁词列表

    Returns:
        dict: 违禁词及其权值的字典
    """
    try:
        json_file = os.path.join(
            DATA_DIR, f"{group_id}.json" if group_id else "default.json"
        )
        with open(json_file, "r", encoding="utf-8") as f:
            ban_words = json.load(f)
        return ban_words
    except Exception as e:
        logging.error(f"获取{'群组' if group_id else '默认'}违禁词列表失败: {e}")
        return {}


# 计算消息总权值
def calculate_message_weight(message: str, group_id: str = None) -> int:
    """
    计算消息中违禁词的总权值

    Args:
        message (str): 要检测的消息
        group_id (str, optional): 群号。若指定则使用对应群的违禁词列表，否则使用默认违禁词列表

    Returns:
        int: 消息中违禁词的总权值
    """
    ban_words = get_banword_list(group_id)
    default_ban_words = get_banword_list() if group_id else {}
    total_weight = 0
    for word, weight in {**default_ban_words, **ban_words}.items():
        if word in message:
            total_weight += weight
    return total_weight


# 对群消息进行违禁词检测
async def check_banword(websocket, raw_message, group_id, message_id, user_id):
    """
    检测消息中的违禁词并发送警告

    Args:
        websocket: WebSocket连接对象
        raw_message (str): 要检测的消息
        group_id (str): 群号
        message_id (str): 消息ID
        user_id (str): 用户ID
    """
    total_weight = calculate_message_weight(raw_message, group_id)
    # 若权值大于10则发送警告
    if total_weight > 10:
        # 禁言30天
        await set_group_ban(websocket, group_id, user_id, 60 * 60 * 24 * 30)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]用户【{user_id}】发送的消息包含违禁词，总权值: {total_weight}超过阈值",
        )

        report_message = f"群号【{group_id}】 用户【{user_id}】发送的消息包含违禁词，总权值: {total_weight}超过阈值\n"
        report_message += f"原消息详情下条消息"

        # 上报到上报群
        for group_id in report_group_ids:
            await send_group_msg(websocket, group_id, report_message)
            await asyncio.sleep(0.1)
            await send_group_msg(websocket, group_id, raw_message)


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
        init_BanWords2(group_id)

        # 鉴权
        authorized = is_authorized(role, user_id)

        if authorized:
            # 管理员命令
            await manager_command(websocket, raw_message, group_id, message_id)
        else:
            # 对群消息进行违禁词检测
            await check_banword(websocket, raw_message, group_id, message_id, user_id)
    except Exception as e:
        logging.error(f"处理BanWords2群消息失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]处理BanWords2群消息失败，错误信息：{e}",
        )
        return
