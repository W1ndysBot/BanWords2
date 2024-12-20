from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO


# 画图，传入的文案画出白底黑字图片，边界自适应
def draw_text(text: str, font_size: int = 20, font_path: str = None) -> str:
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
        # 使用指定字体文件或默认字体
        font = (
            ImageFont.truetype(font_path, font_size)
            if font_path
            else ImageFont.load_default()
        )

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

        print("生成文本图片成功")
        return img_base64
    except Exception as e:
        print(f"生成文本图片失败: {e}")
        return ""


# 测试函数
def test_draw_text():
    text = "Hello, World!"
    font_size = 20
    font_path = None  # 使用默认字体

    # 调用函数生成图片
    img_base64 = draw_text(text, font_size, font_path)
    print("生成的base64字符串:", img_base64)
    # 拼接完整路径
    img_base64 = f"data:image/png;base64,{img_base64}"
    print(img_base64)

    # 尝试解码base64字符串并加载为图片
    try:
        img_data = base64.b64decode(img_base64)
        img = Image.open(BytesIO(img_data))
        img.verify()  # 验证图片是否完整
        print("测试通过: 图片生成成功且有效")
    except Exception as e:
        assert False, f"测试失败: 无法解码或验证图片 - {e}"


# 运行测试函数
test_draw_text()
