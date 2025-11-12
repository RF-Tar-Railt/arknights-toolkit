from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pathlib import Path
import json
import datetime
import random
from typing import List, Dict, Tuple, Any, Optional

# --- 资源路径和数据加载 ---
dir_ = Path(__file__).parent / "resource"
copper_dir = dir_ / "copper"
resource_path = str(copper_dir.resolve())
with (copper_dir / "copper_table.json").open("r", encoding="utf-8") as f:
    copper_data: Dict[str, Dict[str, Any]] = json.load(f)

# --- 字体和图片资源预加载 ---


def load_font_safe(font_path: str, size: int):
    """安全加载字体，失败则返回默认字体"""
    try:
        return ImageFont.truetype(font_path, size)
    except IOError:
        return ImageFont.load_default()


def _preload_images() -> Dict[str, Any]:
    """预加载所有静态图片资源以提高性能"""
    assets = {}
    font_path = str(dir_ / "HarmonyOS_Sans_SC_Medium.ttf")
    assets["fonts"] = {
        "title": load_font_safe(font_path, 24),
        "desc": load_font_safe(font_path, 18),
        "notes": load_font_safe(font_path, 18),
    }

    # 通用和详情页资源
    for key in [
        "detail_selecting_frame", "copper_dec_cloud_up", "copper_dec_cloud_down",
        "copper_draw_state_back_color", "copper_draw_state_back_mask",
        "back_tree_left", "btn_check", "result_copper_detail_back",
        "crossline_vertical"
    ]:
        assets[key] = Image.open(f"{resource_path}/{key}.png").convert("RGBA")

    # 按类型/模式分类的资源
    for mode in ["normal", "bad", "nice"]:
        assets[f"bg_{mode}_mountain_right"] = Image.open(f"{resource_path}/bg_{mode}_mountain_right.png").convert("RGBA")
        assets[f"result_{mode}_copper_back"] = Image.open(f"{resource_path}/result_{mode}_copper_back.png").convert("RGBA")

    for type_ in ["high", "mid", "low"]:
        assets[f"copper_frame_{type_}"] = Image.open(f"{resource_path}/copper_frame_{type_}.png").convert("RGBA")
        assets[f"icon_copper_type_{type_}"] = Image.open(f"{resource_path}/icon_copper_type_{type_}.png").convert("RGBA")

    # --- 预处理需要变换的图像 ---
    # front_tree_right_blur
    tree_r_blur = Image.open(f"{resource_path}/front_tree_right_blur.png").convert("RGBA")
    blurred_r = tree_r_blur.filter(ImageFilter.GaussianBlur(radius=3))
    scaled_r = blurred_r.resize((blurred_r.width * 4, blurred_r.height * 2), Image.Resampling.LANCZOS)
    assets["processed_tree_r"] = scaled_r.crop((0, 0, scaled_r.width // 2, scaled_r.height // 2))

    # front_tree_left
    tree_l = Image.open(f"{resource_path}/front_tree_left.png").convert("RGBA")
    assets["processed_tree_l"] = tree_l.crop((0, 0, tree_l.width * 3 // 4, tree_l.height * 3 // 4))

    # front_tree_left_blur
    tree_l_blur = Image.open(f"{resource_path}/front_tree_left_blur.png").convert("RGBA")
    blurred_l = tree_l_blur.filter(ImageFilter.GaussianBlur(radius=3))
    scaled_l = blurred_l.resize((blurred_l.width * 4, blurred_l.height * 2), Image.Resampling.LANCZOS)
    assets["processed_tree_l_blur"] = scaled_l.crop((scaled_l.width // 2, 0, scaled_l.width, scaled_l.height // 2))

    # crossline_vertical
    crossline = assets["crossline_vertical"]
    assets["scaled_crossline"] = crossline.resize((crossline.width * 2, 360), Image.Resampling.LANCZOS)

    return assets


ASSETS = _preload_images()


def create_gradient_image(width: int, height: int, color_points: List[Tuple[Tuple[int, int, int], float]], direction: int = 1) -> Image.Image:
    """创建渐变图像 (性能优化版)
    direction: 0=水平, 1=垂直
    """
    if direction == 0:  # 水平
        gradient = Image.new('RGB', (width, 1))
        draw = ImageDraw.Draw(gradient)
        points = sorted([(int(pos * (width - 1)), color) for color, pos in color_points])
    else:  # 垂直
        gradient = Image.new('RGB', (1, height))
        draw = ImageDraw.Draw(gradient)
        points = sorted([(int(pos * (height - 1)), color) for color, pos in color_points])

    for i in range(len(points) - 1):
        start_pos, start_color = points[i]
        end_pos, end_color = points[i+1]

        if start_pos >= end_pos:
            continue

        for pos in range(start_pos, end_pos):
            ratio = (pos - start_pos) / (end_pos - start_pos)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            if direction == 0:
                draw.point((pos, 0), fill=(r, g, b))
            else:
                draw.point((0, pos), fill=(r, g, b))

    # 填充首尾
    if points:
        if direction == 0:
            draw.point((0, 0), fill=points[0][1])
            draw.point((width - 1, 0), fill=points[-1][1])
        else:
            draw.point((0, 0), fill=points[0][1])
            draw.point((0, height - 1), fill=points[-1][1])

    if direction == 0:
        return gradient.resize((width, height), Image.Resampling.NEAREST)
    else:
        return gradient.resize((width, height), Image.Resampling.NEAREST)


def get_random_coppers(copper_data_map: Dict[str, Dict[str, Any]], session: Optional[str]) -> List[Dict[str, Any]]:
    """随机选择指定数量的铜币"""
    if not copper_data_map:
        return []

    rand = random.Random()
    now = datetime.datetime.now()
    count = sum(ord(char) for char in session) if session else 0
    rand.seed(count + (now.day * now.month) + now.hour + now.minute + now.year)

    copper_names = list(copper_data_map.keys())
    selected_names = random.sample(copper_names, 3)
    selected_coppers = [copper_data_map[name].copy() for name in selected_names]
    return selected_coppers


def determine_mode_from_coppers(coppers: List[Dict[str, Any]]) -> str:
    """根据铜币类型确定图片模式"""
    if not coppers:
        return 'normal'

    types = [copper.get('type', 'mid') for copper in coppers]

    if all(t == 'high' for t in types):
        return 'nice'
    elif all(t == 'low' for t in types):
        return 'bad'
    else:
        return 'normal'


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """文字换行处理"""
    if not text:
        return []

    lines = []
    words = list(text)
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


def draw_copper_detail(background: Image.Image, copper_info: Dict[str, Any], copper_detail_back: Image.Image, x_pos: int, y_pos: int) -> None:
    """在指定位置绘制单个铜币的详细信息"""
    title_font = ASSETS["fonts"]["title"]
    desc_font = ASSETS["fonts"]["desc"]
    notes_font = ASSETS["fonts"]["notes"]

    detail_height = copper_detail_back.height
    top_center_x = x_pos + copper_detail_back.width // 2
    top_center_y = y_pos + 120

    copper_type = copper_info["type"]
    copper_frame = ASSETS[f"copper_frame_{copper_type}"]
    frame_x = top_center_x - copper_frame.width // 2
    frame_y = top_center_y - copper_frame.height // 2
    background.paste(copper_frame, (frame_x, frame_y), copper_frame)

    selecting_frame = ASSETS["detail_selecting_frame"]
    frame_x = top_center_x - selecting_frame.width // 2
    frame_y = top_center_y - selecting_frame.height // 2
    background.paste(selecting_frame, (frame_x, frame_y), selecting_frame)

    copper_icon = copper_info["icon_image"]
    icon_x = top_center_x - copper_icon.width // 2
    icon_y = top_center_y - copper_icon.height // 2
    background.paste(copper_icon, (icon_x, icon_y), copper_icon)

    cloud_up = ASSETS["copper_dec_cloud_up"]
    cloud_x = frame_x + selecting_frame.width - cloud_up.width + 40
    cloud_y = frame_y - cloud_up.height + 25
    background.paste(cloud_up, (cloud_x, cloud_y), cloud_up)

    cloud_down = ASSETS["copper_dec_cloud_down"]
    cloud_x = frame_x - 40
    cloud_y = frame_y + selecting_frame.height - 50
    background.paste(cloud_down, (cloud_x, cloud_y), cloud_down)

    mid_y = y_pos + 240
    mid_center_x = x_pos + copper_detail_back.width // 2
    line1_y = mid_y + 20

    type_icon = ASSETS[f"icon_copper_type_{copper_type}"]
    category = copper_info["category"]
    name = copper_info["name"]
    text = f"{category[:1]}-{name}" if category and name else name

    bbox = title_font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    total_width = type_icon.width + 10 + text_width
    start_x = mid_center_x - total_width // 2

    icon_y = line1_y - type_icon.height // 2
    background.paste(type_icon, (start_x, icon_y), type_icon)

    draw = ImageDraw.Draw(background)
    text_x = start_x + type_icon.width + 10
    text_y = line1_y - (bbox[3] - bbox[1]) // 2
    draw.text((text_x, text_y), text, font=title_font, fill=(48, 48, 48))

    line2_y = mid_y + 60
    state_back_color = ASSETS["copper_draw_state_back_color"]
    state_back_mask = ASSETS["copper_draw_state_back_mask"].convert("L")
    state_x = mid_center_x - state_back_color.width // 2
    state_y = line2_y - state_back_color.height // 2
    background.paste(state_back_color, (state_x, state_y), state_back_mask)

    text = "已投出"
    bbox = desc_font.getbbox(text)
    text_x = state_x + (state_back_color.width - (bbox[2] - bbox[0])) // 2
    text_y = state_y + (state_back_color.height - (bbox[3] - bbox[1])) // 2
    draw.text((text_x, text_y), text, font=desc_font, fill=(48, 48, 48))

    line3_y = mid_y + 80
    description = copper_info["description"]
    max_width = copper_detail_back.width - 100
    lines = wrap_text(description, desc_font, max_width)
    for line in lines:
        draw.text((x_pos + 50, line3_y), line, font=desc_font, fill=(84, 84, 84))
        line3_y += desc_font.getbbox(line)[3] - desc_font.getbbox(line)[1] + 5

    bottom_y = y_pos + (detail_height - 195)
    notes = copper_info["notes"].split(" ")
    current_y = bottom_y + 95
    draw.text((x_pos + 60, current_y), notes[0], font=notes_font, fill=(96, 96, 96))
    draw.text((x_pos + 190, current_y), notes[1], font=notes_font, fill=(96, 96, 96))
    current_y += 30
    draw.text((x_pos + 60, current_y), notes[2], font=notes_font, fill=(96, 96, 96))
    draw.text((x_pos + 190, current_y), notes[3], font=notes_font, fill=(96, 96, 96))


def create_composite_image(mode: str, coppers: List[Dict[str, Any]]) -> Image.Image:
    """创建复合图像"""
    gradients = {
        'normal': [((67, 162, 140), 0.0), ((175, 228, 219), 0.25), ((215, 254, 251), 0.5), ((169, 224, 214), 0.75), ((67, 162, 140), 1.0)],
        'bad': [((8, 34, 25), 0.0), ((142, 62, 73), 0.25), ((193, 67, 93), 0.5), ((139, 65, 78), 0.75), ((8, 39, 40), 1.0)],
        'nice': [((248, 182, 200), 0.0), ((228, 232, 240), 0.25), ((216, 249, 255), 0.5), ((227, 232, 241), 0.75), ((248, 182, 200), 1.0)]
    }
    background = create_gradient_image(1440, 720, gradients[mode], direction=1)

    left_width = 1080  # 1440 * 3 // 4
    right_start = left_width
    right_width = 360  # 1440 - left_width

    # === 右半部分 ===
    mountain = ASSETS[f"bg_{mode}_mountain_right"]
    center_x = right_start + right_width // 4
    mountain_x = center_x - mountain.width // 2
    mountain_y = (720 - mountain.height) // 2 - 60
    background.paste(mountain, (mountain_x, mountain_y), mountain)

    back_tree_left = ASSETS["back_tree_left"]
    tree_x = mountain_x + mountain.width // 2 - back_tree_left.width // 2
    tree_y = mountain_y + mountain.height - 40
    background.paste(back_tree_left, (tree_x, tree_y), back_tree_left)

    result_copper = ASSETS[f"result_{mode}_copper_back"]
    x_pos = right_start + (right_width - result_copper.width) // 2
    y_pos = 720 // 3
    background.paste(result_copper, (x_pos, y_pos), result_copper)

    center_x = right_start + right_width // 2
    center_y = 720 // 3 + 60
    coin_positions = [
        (center_x - 100, center_y - 65),  # coppers[0]
        (center_x - 30, center_y - 45),   # coppers[1]
        (center_x - 50, center_y - 130)   # coppers[2]
    ]
    # 调整绘制顺序以确保正确的堆叠
    draw_order = [0, 1, 2]
    for i in draw_order:
        copper_icon = coppers[i]["icon_image"]
        background.paste(copper_icon, coin_positions[i], copper_icon)

    cropped_tree_r = ASSETS["processed_tree_r"]
    x_pos = 1440 - cropped_tree_r.width
    y_pos = 720 - cropped_tree_r.height
    background.paste(cropped_tree_r, (x_pos, y_pos), cropped_tree_r)

    cropped_tree_l = ASSETS["processed_tree_l"]
    x_pos = 1440 - cropped_tree_l.width
    y_pos = 720 - cropped_tree_l.height
    background.paste(cropped_tree_l, (x_pos, y_pos), cropped_tree_l)

    btn_check = ASSETS["btn_check"]
    x_pos = right_start + (right_width - btn_check.width) // 2
    y_pos = 720 - cropped_tree_l.height - btn_check.height + 20
    background.paste(btn_check, (x_pos, y_pos), btn_check)

    # === 左半部分 ===
    cropped_tree_l_blur = ASSETS["processed_tree_l_blur"]
    y_pos = 720 - cropped_tree_l_blur.height
    background.paste(cropped_tree_l_blur, (0, y_pos), cropped_tree_l_blur)

    copper_detail_back = ASSETS["result_copper_detail_back"]
    total_width = copper_detail_back.width * 3 + 10 * 2
    start_x = (left_width - total_width) // 2

    for i in range(3):
        x_pos = start_x + i * (copper_detail_back.width + 10) # 加上间距
        y_pos = (720 - copper_detail_back.height) // 2
        background.paste(copper_detail_back, (x_pos, y_pos), copper_detail_back)
        draw_copper_detail(background, coppers[i], copper_detail_back, x_pos, y_pos)

    # === 分隔线 ===
    scaled_crossline = ASSETS["scaled_crossline"]
    x_pos = left_width - scaled_crossline.width // 2
    y_pos = (720 - scaled_crossline.height) // 2
    background.paste(scaled_crossline, (x_pos, y_pos), scaled_crossline)

    return background


def draw_copper(session: Optional[str] = None) -> Image.Image:
    """主函数：生成最终的铜币图片"""
    selected_coppers = get_random_coppers(copper_data, session)
    for copper in selected_coppers:
        coin_icon = Image.open(f"{resource_path}/icon/{copper['name']}.png").convert("RGBA")
        coin_icon = coin_icon.resize((120, 120), Image.Resampling.LANCZOS)
        copper["icon_image"] = coin_icon
    auto_mode = determine_mode_from_coppers(selected_coppers)
    return create_composite_image(auto_mode, selected_coppers)
