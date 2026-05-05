import io
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps


# =========================
# 기본 설정
# =========================
PAGE_W = 860
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
TEXT_GRAY = (70, 70, 70)
DESC_BG = (245, 245, 245)


# =========================
# 폰트
# =========================
def get_font(size: int, bold: bool = False):
    candidates = []

    if bold:
        candidates += [
            "C:/Windows/Fonts/malgunbd.ttf",
            "/System/Library/Fonts/AppleSDGothicNeoB.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        ]
    else:
        candidates += [
            "C:/Windows/Fonts/malgun.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


# =========================
# 이미지 처리
# =========================
def load_image(uploaded_file) -> Image.Image:
    uploaded_file.seek(0)
    img = Image.open(uploaded_file)
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


def resize_contain(img: Image.Image, w: int, h: int, bg=WHITE) -> Image.Image:
    iw, ih = img.size
    scale = min(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    resized = img.resize((nw, nh), Image.LANCZOS)

    canvas = Image.new("RGB", (w, h), bg)
    x = (w - nw) // 2
    y = (h - nh) // 2
    canvas.paste(resized, (x, y))
    return canvas


# =========================
# 텍스트 블록
# =========================
def text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap_text(draw, text: str, font, max_width: int):
    if not text:
        return []

    lines = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue

        buf = ""
        for ch in paragraph:
            candidate = buf + ch
            if text_width(draw, candidate, font) <= max_width:
                buf = candidate
            else:
                if buf:
                    lines.append(buf)
                buf = ch
        if buf:
            lines.append(buf)

    return lines


def build_description_block(
    product_name: str,
    item_text: str,
    material_text: str,
    size_text: str,
    thickness_text: str,
    weight_text: str,
    extra_text: str = "",
) -> Image.Image:
    title_font = get_font(28, bold=True)
    body_font = get_font(17, bold=False)

    lines_raw = []
    if item_text.strip():
        lines_raw.append(f"Item: {item_text}")
    if material_text.strip():
        lines_raw.append(f"Material: {material_text}")
    if size_text.strip():
        lines_raw.append(f"Size: {size_text}")
    if thickness_text.strip():
        lines_raw.append(f"Thickness: {thickness_text}")
    if weight_text.strip():
        lines_raw.append(f"Weight: {weight_text}")
    if extra_text.strip():
        lines_raw.append("")
        lines_raw.extend(extra_text.splitlines())

    temp = Image.new("RGB", (PAGE_W, 100), DESC_BG)
    draw = ImageDraw.Draw(temp)

    max_text_w = int(PAGE_W * 0.80)

    wrapped_lines = []
    for raw in lines_raw:
        if raw == "":
            wrapped_lines.append("")
        else:
            wrapped_lines.extend(wrap_text(draw, raw, body_font, max_text_w))

    line_h = 26
    top_pad = 70
    title_gap = 55
    bottom_pad = 65

    height = top_pad + title_gap + len(wrapped_lines) * line_h + bottom_pad
    if height < 280:
        height = 280

    img = Image.new("RGB", (PAGE_W, height), DESC_BG)
    draw = ImageDraw.Draw(img)

    draw.text(
        (40, 70),
        product_name if product_name.strip() else "Product Name",
        font=title_font,
        fill=BLACK,
        anchor="la",
    )

    y = 140
    for line in wrapped_lines:
        draw.text((40, y), line, font=body_font, fill=BLACK, anchor="la")
        y += line_h

    return img


# =========================
# 페이지 합성
# =========================
def spacer(height: int, bg=WHITE):
    return Image.new("RGB", (PAGE_W, height), bg)


def stack_blocks(blocks):
    total_h = sum(block.height for block in blocks)
    canvas = Image.new("RGB", (PAGE_W, total_h), WHITE)

    y = 0
    for block in blocks:
        canvas.paste(block, (0, y))
        y += block.height

    return canvas


def build_detail_page(
    main_file,
    product_name,
    item_text,
    material_text,
    size_text,
    thickness_text,
    weight_text,
    extra_text,
    model_files,
    product_files,
):
    blocks = []

    # 1) Main 사진
    if main_file is not None:
        main_img = load_image(main_file)
        blocks.append(resize_cover(main_img, PAGE_W, 980))

    # 2) 제품 설명
    desc_block = build_description_block(
        product_name=product_name,
        item_text=item_text,
        material_text=material_text,
        size_text=size_text,
        thickness_text=thickness_text,
        weight_text=weight_text,
        extra_text=extra_text,
    )
    blocks.append(desc_block)

    # 3) 모델컷들
    if model_files:
        for file in model_files:
            img = load_image(file)
            blocks.append(resize_cover(img, PAGE_W, 980))

    # 4) 제품컷들
    if product_files:
        for file in product_files:
            img = load_image(file)
            blocks.append(resize_contain(img, PAGE_W, 900, bg=WHITE))

    return stack_blocks(blocks)


# =========================
# Streamlit UI
# =========================
st.set_page_config(page_title="Jewelry Detail Page Maker", layout="centered")
st.title("Jewelry Detail Page Maker")

st.markdown("### 1. Main 사진 1장 업로드")
main_file = st.file_uploader(
    "Main 사진 1장을 업로드하세요",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=False,
    key="main_file",
)

if main_file:
    st.image(main_file, caption="Main 사진", use_container_width=True)

st.markdown("---")

st.markdown("### 2. 제품 설명 입력")
product_name = st.text_input("제품명", value="Wood Street_N")
item_text = st.text_input("Item", value="Necklace")
material_text = st.text_input("Material", value="S925, Mother of pearl, Wood, Hematite")
size_text = st.text_input("Size", value="38~43cm, 48~53cm")
thickness_text = st.text_input("Thickness", value="4mm")
weight_text = st.text_input("Weight", value="7.20g")
extra_text = st.text_area("추가 설명(선택)", value="", height=120)

st.markdown("---")

st.markdown("### 3. 모델컷 사진들 업로드")
model_files = st.file_uploader(
    "모델컷 사진을 여러 장 업로드하세요",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    key="model_files",
)

if model_files:
    st.write(f"모델컷 업로드 수: {len(model_files)}")
    cols = st.columns(3)
    for i, file in enumerate(model_files):
        with cols[i % 3]:
            st.image(file, use_container_width=True)

st.markdown("---")

st.markdown("### 4. 제품컷 사진들 업로드")
product_files = st.file_uploader(
    "제품컷 사진을 여러 장 업로드하세요",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    key="product_files",
)

if product_files:
    st.write(f"제품컷 업로드 수: {len(product_files)}")
    cols = st.columns(3)
    for i, file in enumerate(product_files):
        with cols[i % 3]:
            st.image(file, use_container_width=True)

st.markdown("---")

if st.button("상세페이지 생성"):
    if main_file is None:
        st.error("Main 사진 1장은 반드시 필요합니다.")
    else:
        result = build_detail_page(
            main_file=main_file,
            product_name=product_name,
            item_text=item_text,
            material_text=material_text,
            size_text=size_text,
            thickness_text=thickness_text,
            weight_text=weight_text,
            extra_text=extra_text,
            model_files=model_files,
            product_files=product_files,
        )

        st.success("상세페이지 생성 완료")
        st.image(result, caption="생성 결과", use_container_width=True)

        buf = io.BytesIO()
        result.save(buf, format="JPEG", quality=92)
        st.download_button(
            label="상세페이지 JPG 다운로드",
            data=buf.getvalue(),
            file_name="detail_page.jpg",
            mime="image/jpeg",
        )
