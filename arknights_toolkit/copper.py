from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pathlib import Path
import json
import random


dir_ = Path(__file__).parent / "resource" / "copper"
resource_path = str(dir_.resolve())
with (dir_ / "copper_table.json").open("r", encoding="utf-8") as f:
    copper_data = json.load(f)


def create_gradient_image(width, height, color_points, direction=1):
    """创建渐变图像
    direction: 0=水平, 1=垂直
    """
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)

    # 对颜色点按位置排序
    sorted_points = sorted(color_points, key=lambda x: x[1])

    for x in range(width):
        for y in range(height):
            if direction == 0:  # 水平渐变
                pos = x / (width - 1) if width > 1 else 0
            else:  # 垂直渐变
                pos = y / (height - 1) if height > 1 else 0

            # 找到相邻的颜色点
            color = None
            for i in range(len(sorted_points) - 1):
                if sorted_points[i][1] <= pos <= sorted_points[i + 1][1]:
                    start_color, start_pos = sorted_points[i]
                    end_color, end_pos = sorted_points[i + 1]

                    # 计算插值比例
                    if start_pos == end_pos:
                        ratio = 0
                    else:
                        ratio = (pos - start_pos) / (end_pos - start_pos)

                    # 线性插值
                    r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                    g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                    b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)

                    color = (r, g, b)
                    break

            if color is None:
                # 使用第一个或最后一个颜色
                if pos <= sorted_points[0][1]:
                    color = sorted_points[0][0]
                else:
                    color = sorted_points[-1][0]

            draw.point((x, y), fill=color)

    return image


def get_random_coppers(copper_data, count=3):
    """随机选择指定数量的铜币"""
    if not copper_data:
        return []

    copper_names = list(copper_data.keys())
    selected_names = random.sample(copper_names, min(count, len(copper_names)))

    selected_coppers = []
    for name in selected_names:
        copper_info = copper_data[name].copy()
        copper_info['name'] = name
        selected_coppers.append(copper_info)

    return selected_coppers


def determine_mode_from_coppers(coppers):
    """根据铜币类型确定图片模式"""
    if not coppers:
        return 'normal'

    types = [copper.get('type', 'mid') for copper in coppers]

    # 如果全是 high，返回 nice
    if all(t == 'high' for t in types):
        return 'nice'
    # 如果全是 low，返回 bad
    elif all(t == 'low' for t in types):
        return 'bad'
    else:
        return 'normal'


def wrap_text(text, font, max_width):
    """文字换行处理"""
    if not text:
        return []

    lines = []
    words = list(text)  # 中文逐字处理
    current_line = ""

    for char in words:
        test_line = current_line + char
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char

    if current_line:
        lines.append(current_line)

    return lines


def load_font_safe(font_path, size):
    """安全加载字体"""
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()


def draw_copper_detail(background: Image.Image, copper_data, copper_detail_back, x_pos, y_pos):
    """在指定位置绘制单个铜币的详细信息"""

    # 加载字体
    font_path = str(dir_.parent / "HarmonyOS_Sans_SC_Medium.ttf")
    title_font = load_font_safe(font_path, 24)
    desc_font = load_font_safe(font_path, 18)
    notes_font = load_font_safe(font_path, 18)

    # 计算区域
    detail_height = copper_detail_back.height

    # === 上1/3部分：铜币图标 ===
    top_y = y_pos
    top_center_x = x_pos + copper_detail_back.width // 2
    top_center_y = top_y + 120

    # 1. 绘制 copper_frame_<type>.png
    copper_type = copper_data.get('type', 'mid')
    copper_frame = Image.open(f"{resource_path}/copper_frame_{copper_type}.png").convert("RGBA")
    frame_x = top_center_x - copper_frame.width // 2
    frame_y = top_center_y - copper_frame.height // 2
    background.paste(copper_frame, (frame_x, frame_y), copper_frame)

    # 2. 绘制 detail_selecting_frame.png
    selecting_frame = Image.open(f"{resource_path}/detail_selecting_frame.png").convert("RGBA")
    frame_x = top_center_x - selecting_frame.width // 2
    frame_y = top_center_y - selecting_frame.height // 2
    background.paste(selecting_frame, (frame_x, frame_y), selecting_frame)

    # 3. 绘制铜币图标
    copper_name = copper_data.get('name', '')
    coin_icon = Image.open(f"{resource_path}/icon/{copper_name}.png").convert("RGBA")
    coin_icon = coin_icon.resize((120, 120), Image.Resampling.LANCZOS)
    icon_x = top_center_x - coin_icon.width // 2
    icon_y = top_center_y - coin_icon.height // 2
    background.paste(coin_icon, (icon_x, icon_y), coin_icon)

    # 4. 绘制装饰云朵
    cloud_up = Image.open(f"{resource_path}/copper_dec_cloud_up.png").convert("RGBA")
    cloud_x = frame_x + selecting_frame.width - cloud_up.width + 40
    cloud_y = frame_y - cloud_up.height + 25
    background.paste(cloud_up, (cloud_x, cloud_y), cloud_up)

    cloud_down = Image.open(f"{resource_path}/copper_dec_cloud_down.png").convert("RGBA")
    cloud_x = frame_x - 40
    cloud_y = frame_y + selecting_frame.height - 50
    background.paste(cloud_down, (cloud_x, cloud_y), cloud_down)

    # === 中1/3部分：文字信息 ===
    mid_y = y_pos + 240
    mid_center_x = x_pos + copper_detail_back.width // 2

    # 第一行：类型图标 + 类别-名称
    line1_y = mid_y + 20

    # 类型图标
    type_icon = Image.open(f"{resource_path}/icon_copper_type_{copper_type}.png").convert("RGBA")
    # 准备文字
    category = copper_data.get('category', '')
    name = copper_data.get('name', '')
    text = f"{category[:1]}-{name}" if category and name else name

    # 计算总宽度
    bbox = title_font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    total_width = type_icon.width + 10 + text_width

    # 居中绘制
    start_x = mid_center_x - total_width // 2

    # 绘制图标
    icon_y = line1_y - type_icon.height // 2
    background.paste(type_icon, (start_x, icon_y), type_icon)

    # 绘制文字
    draw = ImageDraw.Draw(background)
    text_x = start_x + type_icon.width + 10
    text_y = line1_y - (bbox[3] - bbox[1]) // 2
    draw.text((text_x, text_y), text, font=title_font, fill=(48, 48, 48))

    # 第二行：已投出状态
    line2_y = mid_y + 60

    # 绘制状态背景
    state_back_color = Image.open(f"{resource_path}/copper_draw_state_back_color.png").convert("RGBA")
    state_back_mask = Image.open(f"{resource_path}/copper_draw_state_back_mask.png").convert("L")

    # 绘制状态背景（使用蒙版）
    state_x = mid_center_x - state_back_color.width // 2
    state_y = line2_y - state_back_color.height // 2
    background.paste(state_back_color, (state_x, state_y), state_back_mask)
    # background.paste(state_back_mask, (state_x, state_y), state_back_mask)
    # 绘制"已投出"文字
    draw = ImageDraw.Draw(background)
    text = "已投出"
    bbox = desc_font.getbbox(text)
    text_x = state_x + (state_back_color.width - (bbox[2] - bbox[0])) // 2
    text_y = state_y + (state_back_color.height - (bbox[3] - bbox[1])) // 2
    draw.text((text_x, text_y), text, font=desc_font, fill=(48, 48, 48))

    # 第三行：描述（左对齐）
    line3_y = mid_y + 80

    draw = ImageDraw.Draw(background)
    description = copper_data["description"]
    max_width = copper_detail_back.width - 100  # 留边距
    lines = wrap_text(description, desc_font, max_width)
    for line in lines:
        draw.text((x_pos + 50, line3_y), line, font=desc_font, fill=(84, 84, 84))
        line3_y += desc_font.getbbox(line)[3] - desc_font.getbbox(line)[1] + 5  # 行高+间距

    # === 下1/3部分：注释 ===
    bottom_y = y_pos + (detail_height - 195)

    draw = ImageDraw.Draw(background)
    notes = copper_data["notes"].split(" ")
    current_y = bottom_y + 95
    draw.text((x_pos + 60, current_y), notes[0], font=notes_font, fill=(96, 96, 96))
    draw.text((x_pos + 190, current_y), notes[1], font=notes_font, fill=(96, 96, 96))
    current_y += 30
    draw.text((x_pos + 60, current_y), notes[2], font=notes_font, fill=(96, 96, 96))
    draw.text((x_pos + 190, current_y), notes[3], font=notes_font, fill=(96, 96, 96))


def create_composite_image(mode: str, coppers: list[dict]):
    """创建复合图像
    mode: 'normal', 'bad', 'nice'
    coppers: 铜币数据列表
    """

    # 定义渐变色
    gradients = {
        'normal': [((67, 162, 140), 0.0), ((175, 228, 219), 0.25), ((215, 254, 251), 0.5), ((169, 224, 214), 0.75),
                   ((67, 162, 140), 1.0)],
        'bad': [((8, 34, 25), 0.0), ((142, 62, 73), 0.25), ((193, 67, 93), 0.5), ((139, 65, 78), 0.75),
                ((8, 39, 40), 1.0)],
        'nice': [((248, 182, 200), 0.0), ((228, 232, 240), 0.25), ((216, 249, 255), 0.5), ((227, 232, 241), 0.75),
                 ((248, 182, 200), 1.0)]
    }

    # 创建1440x720的背景渐变
    background = create_gradient_image(1440, 720, gradients[mode], direction=1)

    # 计算左右分割点 (3:1)
    left_width = 1440 * 3 // 4  # 1125
    right_start = left_width
    right_width = 1440 - left_width  # 375

    # === 右半部分 ===

    # 1. bg_<模式>_mountain_right.png - 垂直居中，中线在右半部分左四分之一，向上移动60像素
    mountain = Image.open(f"{resource_path}/bg_{mode}_mountain_right.png").convert("RGBA")
    mountain_x = right_start
    mountain_y = 0
    # 中线在右半部分的左四分之一位置
    center_x = right_start + right_width // 4
    mountain_x = center_x - mountain.width // 2
    mountain_y = (720 - mountain.height) // 2 - 60  # 向上移动60像素
    background.paste(mountain, (mountain_x, mountain_y), mountain)

    # 2. back_tree_left.png - 在mountain正下方，中线与mountain对齐，也向上移动60像素
    back_tree_left = Image.open(f"{resource_path}/back_tree_left.png").convert("RGBA")
    # 中线与mountain对齐
    tree_x = mountain_x + mountain.width // 2 - back_tree_left.width // 2
    tree_y = mountain_y + mountain.height - 40  # mountain已经向上移动了60像素
    background.paste(back_tree_left, (tree_x, tree_y), back_tree_left)

    # 3. result_<模式>_copper_back.png - 右半部分中间偏上水平居中
    result_copper = Image.open(f"{resource_path}/result_{mode}_copper_back.png").convert("RGBA")
    x_pos = right_start + (right_width - result_copper.width) // 2
    y_pos = 720 // 3  # 中间偏上
    background.paste(result_copper, (x_pos, y_pos), result_copper)

    # 3. 将3枚铜钱呈三角形叠放 - 右半部分中间偏上水平居中
    # 定义铜币图标大小和位置
    coin_size = (120, 120)
    center_x = right_start + right_width // 2
    center_y = 720 // 3 + 60  # 原中间偏上位置微调

    # 计算三个铜币的位置（三角形排列）
    # 顶层铜币 (coppers[2])
    top_coin_pos = (center_x - 50, center_y - 130)
    # 左下铜币 (coppers[0])
    left_coin_pos = (center_x - 100, center_y - 65)
    # 右下铜币 (coppers[1])
    right_coin_pos = (center_x - 30, center_y - 45)

    # 按照 coppers[0], coppers[1], coppers[2] 的顺序绘制，让顶层铜币在最上面
    coin_positions = [right_coin_pos, top_coin_pos, left_coin_pos]
    for i in range(3):
        copper_name = coppers[i]["name"]
        try:
            coin_icon = Image.open(f"{resource_path}/icon/{copper_name}.png").convert("RGBA")
            coin_icon = coin_icon.resize(coin_size, Image.Resampling.LANCZOS)
            background.paste(coin_icon, coin_positions[i], coin_icon)
        except FileNotFoundError:
            print(f"警告: 找不到铜币图标文件 {resource_path}/icon/{copper_name}.png")

    # 4. front_tree_right_blur.png - 高斯模糊，水平4倍垂直2倍拉伸，截取左上角1/2放置右下角
    front_tree_right_blur = Image.open(f"{resource_path}/front_tree_right_blur.png").convert("RGBA")
    # 应用高斯模糊
    blurred = front_tree_right_blur.filter(ImageFilter.GaussianBlur(radius=3))

    # 水平4倍，垂直2倍拉伸
    scaled_width = blurred.width * 4
    scaled_height = blurred.height * 2
    scaled_tree = blurred.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    # 截取左上角1/2部分
    crop_width = scaled_width // 2
    crop_height = scaled_height // 2
    cropped_tree = scaled_tree.crop((0, 0, crop_width, crop_height))

    # 放置在右下角
    x_pos = 1440 - cropped_tree.width
    y_pos = 720 - cropped_tree.height
    background.paste(cropped_tree, (x_pos, y_pos), cropped_tree)

    # 5. front_tree_left.png - 截取左上角3/4部分，放置右下角
    front_tree_left = Image.open(f"{resource_path}/front_tree_left.png").convert("RGBA")
    crop_width = 0
    crop_height = 0
    # 截取左上角3/4部分
    crop_width = front_tree_left.width * 3 // 4
    crop_height = front_tree_left.height * 3 // 4
    cropped_tree = front_tree_left.crop((0, 0, crop_width, crop_height))

    # 放置在右下角
    x_pos = 1440 - cropped_tree.width
    y_pos = 720 - cropped_tree.height
    background.paste(cropped_tree, (x_pos, y_pos), cropped_tree)

    # 6. btn_check.png - 在front_tree_left上方，右半部分水平居中
    btn_check = Image.open(f"{resource_path}/btn_check.png").convert("RGBA")
    x_pos = right_start + (right_width - btn_check.width) // 2
    y_pos = 720 - crop_height - btn_check.height + 20  # 在tree上方留20像素间距
    background.paste(btn_check, (x_pos, y_pos), btn_check)

    # === 左半部分 ===

    # 1. front_tree_left_blur.png - 高斯模糊，水平4倍垂直2倍拉伸，截取右上角1/2放置左下角
    front_tree_left_blur = Image.open(f"{resource_path}/front_tree_left_blur.png").convert("RGBA")
    # 应用高斯模糊
    blurred = front_tree_left_blur.filter(ImageFilter.GaussianBlur(radius=3))

    # 水平4倍，垂直2倍拉伸
    scaled_width = blurred.width * 4
    scaled_height = blurred.height * 2
    scaled_tree = blurred.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    # 截取右上角1/2部分
    crop_width = scaled_width // 2
    crop_height = scaled_height // 2
    cropped_tree = scaled_tree.crop((scaled_width - crop_width, 0, scaled_width, crop_height))

    # 放置在左下角
    y_pos = 720 - cropped_tree.height
    background.paste(cropped_tree, (0, y_pos), cropped_tree)

    # 2. 左半部分水平居中放置三个 result_copper_detail_back.png，间距10，并绘制铜币详情
    copper_detail = Image.open(f"{resource_path}/result_copper_detail_back.png").convert("RGBA")
    # 计算总宽度和起始位置
    total_width = copper_detail.width * 3 + 10 * 2
    start_x = (left_width - total_width) // 2

    for i in range(3):
        x_pos = start_x + i * copper_detail.width
        y_pos = (720 - copper_detail.height) // 2  # 垂直居中

        # 绘制背景
        background.paste(copper_detail, (x_pos, y_pos), copper_detail)

        # 绘制铜币详情
        draw_copper_detail(background, coppers[i], copper_detail, x_pos, y_pos)

    # === 分隔线 ===

    # crossline_vertical.png - 分隔左右部分，只垂直拉伸到高度360，水平方向不变
    crossline = Image.open(f"{resource_path}/crossline_vertical.png").convert("RGBA")
    # 只垂直拉伸到高度360，保持原始宽度
    target_height = 360
    scaled_crossline = crossline.resize((crossline.width * 2, target_height), Image.Resampling.LANCZOS)

    # 在分割点处垂直居中放置
    x_pos = left_width - scaled_crossline.width // 2
    y_pos = (720 - target_height) // 2
    background.paste(scaled_crossline, (x_pos, y_pos), scaled_crossline)

    return background


def draw_copper():
    # 随机选择3个铜币
    selected_coppers = get_random_coppers(copper_data, 3)
    # 根据铜币类型确定模式
    auto_mode = determine_mode_from_coppers(selected_coppers)
    return create_composite_image(auto_mode, selected_coppers)
