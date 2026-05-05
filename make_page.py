import io
import math
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps


PAGE_W = 860
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
LIGHT_BG = (246, 246, 246)
DARK_BG = (18, 18, 18)


def get_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def load_image(file) -> Image.Image:
    file.seek(0)
    img = Image.open(file)
    img = ImageOps.exif_transpose(img)
    return img.convert("RGB")


def resize_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)

    resized = img.resize((nw, nh), Image.LANCZOS)

    left = (nw - w) // 2
    top = (nh - h) // 2

    return resized.crop((left, top, left + w, top + h))


def resize_contain(
    img: Image.Image,
    w: int,
    h: int,
    bg=(255, 255, 255),
) -> Image.Image:
    iw, ih = img.size
    scale = min(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)

    resized = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), bg)

    x = (w - nw) // 2
    y = (h - nh) // 2
    canvas.paste(resized, (x, y))

    return canvas


def text_width(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    lines = []

    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue

        buffer = ""

        for ch in paragraph:
            candidate = buffer + ch

            if text_width(draw, candidate, font) <= max_width:
                buffer = candidate
            else:
                if buffer:
                    lines.append(buffer)
                buffer = ch

        if buffer:
            lines.append(buffer)

    return lines


def text_block(
    title: str,
    body: str,
    bg=WHITE,
    title_color=BLACK,
    body_color=(70, 70, 70),
) -> Image.Image:
    title_font = get_font(28)
    body_font = get_font(17)

    temp = Image.new("RGB", (PAGE_W, 10), bg)
    draw = ImageDraw.Draw(temp)

    max_text_w = int(PAGE_W * 0.76)
    lines = wrap_text(draw, body, body_font, max_text_w)

    line_h = 30
    height = 90 + 45 + len(lines) * line_h + 70

    img = Image.new("RGB", (PAGE_W, height), bg)
    draw = ImageDraw.Draw(img)

    draw.text(
        (PAGE_W // 2, 75),
        title,
        font=title_font,
        fill=title_color,
        anchor="mm",
    )

    y = 130
    for line in lines:
        draw.text(
            (PAGE_W // 2, y),
            line,
            font=body_font,
            fill=body_color,
            anchor="mm",
        )
        y += line_h

    return img


def spacer(height: int, bg=WHITE) -> Image.Image:
    return Image.new("RGB", (PAGE_W, height), bg)


def grid_block(images: list[Image.Image]) -> Image.Image:
    margin = 58
    gap = 24
    cols = 2

    cell_w = (PAGE_W - margin * 2 - gap) // cols
    cell_h = cell_w

    rows = math.ceil(len(images) / cols)
    height = margin * 2 + rows * cell_h + (rows - 1) * gap

    canvas = Image.new("RGB", (PAGE_W, height), LIGHT_BG)

    for idx, img in enumerate(images):
        row = idx // cols
        col = idx % cols

        x = margin + col * (cell_w + gap)
        y = margin + row * (cell_h + gap)

        item = resize_contain(img, cell_w, cell_h, DARK_BG)
        canvas.paste(item, (x, y))

    return canvas


def stack_blocks(blocks: list[Image.Image]) -> Image.Image:
    total_h = sum(block.height for block in blocks)
    output = Image.new("RGB", (PAGE_W, total_h), WHITE)

    y = 0
    for block in blocks:
        output.paste(block, (0, y))
        y += block.height

    return output


def make_detail_page(
    files,
    product_name: str,
    subtitle: str,
    material: str,
) -> Image.Image:
    images = [load_image(file) for file in files]

    blocks = [
        resize_cover(images[0], PAGE_W, 980),
        resize_cover(images[1], PAGE_W, 980),

        text_block(
            product_name,
            f"{subtitle}\n\nMaterial : {material}\nSize : Free\nColor : Black",
        ),

        resize_cover(images[2], PAGE_W, 1060),
        resize_cover(images[3], PAGE_W, 980),
        resize_cover(images[4], PAGE_W, 980),
        resize_cover(images[5], PAGE_W, 980),

        grid_block(images[6:9]),

        resize_contain(images[9], PAGE_W, 760, LIGHT_BG),

        text_block(
            "GO GREEN PACKAGE",
            "제품은 기본 패키지에 안전하게 포장되어 발송됩니다.\n"
            "패키지 구성은 생산 시점에 따라 일부 변경될 수 있습니다.",
        ),

        text_block(
            "SHIPPING / EXCHANGE / RETURN",
            "주문 확인 후 순차적으로 발송됩니다.\n"
            "단순 변심으로 인한 교환 및 반품은 상품 수령 후 지정 기간 내 접수해 주세요.\n"
            "착용 흔적, 오염, 훼손이 있는 상품은 교환 및 반품이 제한될 수 있습니다.",
        ),

        text_block(
            "ATTENTION",
            "주얼리 제품은 물, 땀, 향수, 화장품에 장시간 노출될 경우 변색될 수 있습니다.\n"
            "착용 후에는 부드러운 천으로 닦아 밀폐 보관하는 것을 권장합니다.",
        ),
    ]

    return stack_blocks(blocks)


st.set_page_config(page_title="Jewelry Detail Page Maker", layout="centered")

st.title("Jewelry Detail Page Maker")

product_name = st.text_input("제품명", "Round Black B.")
subtitle = st.text_input("한 줄 설명", "Minimal black bracelet")
material = st.text_input("소재", "Surgical steel / Black coating")

uploaded_files = st.file_uploader(
    "사진 10장을 선택하세요. 파일명은 01, 02, 03 순서로 맞추는 것을 권장합니다.",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
)

if uploaded_files:
    uploaded_files = sorted(uploaded_files, key=lambda f: f.name)

    st.write(f"선택된 사진 수: {len(uploaded_files)}")

    if len(uploaded_files) != 10:
        st.error("정확히 10장의 사진이 필요합니다.")
    else:
        if st.button("상세페이지 생성"):
            result = make_detail_page(
                uploaded_files,
                product_name,
                subtitle,
                material,
            )

            st.image(result, use_container_width=True)

            buffer = io.BytesIO()
            result.save(
                buffer,
                format="JPEG",
                quality=92,
                optimize=True,
                progressive=True,
            )

            st.download_button(
                label="상세페이지 JPG 다운로드",
                data=buffer.getvalue(),
                file_name="jewelry_detail_page.jpg",
                mime="image/jpeg",
            )
