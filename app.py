import io
from pathlib import Path

import streamlit as st
from streamlit_cropper import st_cropper
from PIL import Image, ImageDraw, ImageFont, ImageOps


# =========================
# 기본 설정
# =========================
PAGE_W = 860
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)


ASPECT_OPTIONS = {
    "자유 비율": None,
    "상세페이지 세로형 860:980": (860, 980),
    "정사각형 1:1": (1, 1),
    "세로형 4:5": (4, 5),
    "세로형 3:4": (3, 4),
    "가로형 16:9": (16, 9),
}


# =========================
# 폰트
# =========================
def get_font(size: int, bold: bool = False):
    if bold:
        candidates = [
            "C:/Windows/Fonts/malgunbd.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/Library/Fonts/AppleGothic.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/malgun.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/Library/Fonts/AppleGothic.ttf",
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


def fit_width(img: Image.Image, width: int = PAGE_W) -> Image.Image:
    """
    자동 crop 없이, 사용자가 crop한 이미지를 상세페이지 폭에 맞게만 리사이즈.
    """
    img = img.convert("RGB")
    w, h = img.size

    if w == 0 or h == 0:
        raise ValueError("Invalid image size")

    new_h = int(h * width / w)
    return img.resize((width, new_h), Image.LANCZOS)


def stack_blocks(blocks: list[Image.Image]) -> Image.Image:
    total_h = sum(block.height for block in blocks)
    canvas = Image.new("RGB", (PAGE_W, total_h), WHITE)

    y = 0
    for block in blocks:
        canvas.paste(block, (0, y))
        y += block.height

    return canvas


# =========================
# 텍스트 블록
# =========================
def text_width(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    if not text:
        return []

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


def build_description_block(
    product_name: str,
    item_text: str,
    material_text: str,
    size_text: str,
    thickness_text: str,
    weight_text: str,
    extra_text: str,
) -> Image.Image:
    title_font = get_font(31, bold=True)
    body_font = get_font(25, bold=False)

    raw_lines = []

    if item_text.strip():
        raw_lines.append(f"Item: {item_text.strip()}")

    if material_text.strip():
        raw_lines.append(f"Material: {material_text.strip()}")

    if size_text.strip():
        raw_lines.append(f"Size: {size_text.strip()}")

    if thickness_text.strip():
        raw_lines.append(f"Thickness: {thickness_text.strip()}")

    if weight_text.strip():
        raw_lines.append(f"Weight: {weight_text.strip()}")

    if extra_text.strip():
        raw_lines.append("")
        raw_lines.extend(extra_text.strip().splitlines())

    temp = Image.new("RGB", (PAGE_W, 100), WHITE)
    draw = ImageDraw.Draw(temp)

    left_margin = 42
    max_text_w = PAGE_W - left_margin * 2

    wrapped_lines = []
    for line in raw_lines:
        if line == "":
            wrapped_lines.append("")
        else:
            wrapped_lines.extend(wrap_text(draw, line, body_font, max_text_w))

    title_top = 82
    body_top = 175
    line_h = 39
    bottom_pad = 90

    height = body_top + len(wrapped_lines) * line_h + bottom_pad
    height = max(height, 430)

    img = Image.new("RGB", (PAGE_W, height), WHITE)
    draw = ImageDraw.Draw(img)

    draw.text(
        (left_margin, title_top),
        product_name.strip() or "Product Name",
        font=title_font,
        fill=BLACK,
    )

    y = body_top
    for line in wrapped_lines:
        draw.text(
            (left_margin, y),
            line,
            font=body_font,
            fill=BLACK,
        )
        y += line_h

    return img


# =========================
# Crop UI
# =========================
def crop_single_image(
    uploaded_file,
    key_prefix: str,
    aspect_ratio,
    expanded: bool = True,
) -> Image.Image:
    original = load_image(uploaded_file)

    with st.expander(f"Crop: {uploaded_file.name}", expanded=expanded):
        st.caption(f"원본 크기: {original.width} × {original.height}")
        st.caption("crop 박스를 조정한 뒤 더블클릭하면 crop 결과가 적용됩니다.")

        cropped = st_cropper(
            img_file=original,
            realtime_update=False,
            box_color="#111111",
            aspect_ratio=aspect_ratio,
            return_type="image",
            key=f"cropper_{key_prefix}_{uploaded_file.name}",
            stroke_width=2,
        )

        cropped = cropped.convert("RGB")

        st.image(
            cropped,
            caption=f"적용될 crop 결과: {cropped.width} × {cropped.height}",
            use_container_width=True,
        )

        return cropped


def crop_multiple_images(
    uploaded_files,
    group_name: str,
    aspect_ratio,
) -> list[Image.Image]:
    cropped_images = []

    for index, file in enumerate(uploaded_files):
        cropped = crop_single_image(
            uploaded_file=file,
            key_prefix=f"{group_name}_{index}",
            aspect_ratio=aspect_ratio,
            expanded=(index == 0),
        )
        cropped_images.append(cropped)

    return cropped_images


# =========================
# 상세페이지 생성
# =========================
def build_detail_page(
    main_img: Image.Image,
    product_name: str,
    item_text: str,
    material_text: str,
    size_text: str,
    thickness_text: str,
    weight_text: str,
    extra_text: str,
    model_imgs: list[Image.Image],
    product_imgs: list[Image.Image],
) -> Image.Image:
    blocks = []

    # 1. Main 사진
    blocks.append(fit_width(main_img, PAGE_W))

    # 2. 제품 설명
    blocks.append(
        build_description_block(
            product_name=product_name,
            item_text=item_text,
            material_text=material_text,
            size_text=size_text,
            thickness_text=thickness_text,
            weight_text=weight_text,
            extra_text=extra_text,
        )
    )

    # 3. 모델컷 사진들
    for img in model_imgs:
        blocks.append(fit_width(img, PAGE_W))

    # 4. 제품컷 사진들
    for img in product_imgs:
        blocks.append(fit_width(img, PAGE_W))

    return stack_blocks(blocks)


# =========================
# Streamlit UI
# =========================
st.set_page_config(
    page_title="Jewelry Detail Page Maker",
    layout="centered",
)

st.title("Jewelry Detail Page Maker")

st.info(
    "이 버전은 자동 crop을 하지 않습니다. "
    "각 사진을 직접 crop한 뒤, crop 결과를 상세페이지 폭에 맞게만 리사이즈합니다."
)

sort_by_name = st.checkbox("여러 장 업로드 시 파일명 기준으로 정렬", value=True)

st.markdown("---")

# =========================
# 1. Main 사진
# =========================
st.markdown("## 1. Main 사진 1장 업로드")

main_file = st.file_uploader(
    "Main 사진을 1장 업로드하세요.",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=False,
    key="main_file",
)

main_aspect_label = st.selectbox(
    "Main 사진 crop 비율",
    list(ASPECT_OPTIONS.keys()),
    index=1,
    key="main_aspect",
)

main_cropped = None

if main_file is not None:
    main_cropped = crop_single_image(
        uploaded_file=main_file,
        key_prefix="main",
        aspect_ratio=ASPECT_OPTIONS[main_aspect_label],
        expanded=True,
    )

st.markdown("---")

# =========================
# 2. 제품 설명
# =========================
st.markdown("## 2. 제품 설명 입력")

product_name = st.text_input("제품명", value="Wood Street_N")
item_text = st.text_input("Item", value="Necklace")
material_text = st.text_input("Material", value="S925, Mother of pearl, Wood, Hematite")
size_text = st.text_input("Size", value="38~43cm, 48~53cm")
thickness_text = st.text_input("Thickness", value="4mm")
weight_text = st.text_input("Weight", value="7.20g")

extra_text = st.text_area(
    "추가 설명",
    value="",
    height=120,
    placeholder="추가 안내 문구가 있으면 입력하세요.",
)

with st.expander("제품 설명 미리보기", expanded=False):
    desc_preview = build_description_block(
        product_name=product_name,
        item_text=item_text,
        material_text=material_text,
        size_text=size_text,
        thickness_text=thickness_text,
        weight_text=weight_text,
        extra_text=extra_text,
    )
    st.image(desc_preview, use_container_width=True)

st.markdown("---")

# =========================
# 3. 모델컷 사진들
# =========================
st.markdown("## 3. 모델컷 사진들 업로드")

model_files = st.file_uploader(
    "모델컷 사진을 여러 장 업로드하세요.",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    key="model_files",
)

model_aspect_label = st.selectbox(
    "모델컷 crop 비율",
    list(ASPECT_OPTIONS.keys()),
    index=1,
    key="model_aspect",
)

model_cropped_images = []

if model_files:
    if sort_by_name:
        model_files = sorted(model_files, key=lambda f: f.name)

    st.write(f"모델컷 업로드 수: {len(model_files)}")

    model_cropped_images = crop_multiple_images(
        uploaded_files=model_files,
        group_name="model",
        aspect_ratio=ASPECT_OPTIONS[model_aspect_label],
    )

st.markdown("---")

# =========================
# 4. 제품컷 사진들
# =========================
st.markdown("## 4. 제품컷 사진들 업로드")

product_files = st.file_uploader(
    "제품컷 사진을 여러 장 업로드하세요.",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    key="product_files",
)

product_aspect_label = st.selectbox(
    "제품컷 crop 비율",
    list(ASPECT_OPTIONS.keys()),
    index=0,
    key="product_aspect",
)

product_cropped_images = []

if product_files:
    if sort_by_name:
        product_files = sorted(product_files, key=lambda f: f.name)

    st.write(f"제품컷 업로드 수: {len(product_files)}")

    product_cropped_images = crop_multiple_images(
        uploaded_files=product_files,
        group_name="product",
        aspect_ratio=ASPECT_OPTIONS[product_aspect_label],
    )

st.markdown("---")

# =========================
# 생성 / 다운로드
# =========================
st.markdown("## 상세페이지 생성")

if st.button("상세페이지 생성"):
    if main_cropped is None:
        st.error("Main 사진 1장은 반드시 업로드해야 합니다.")
    else:
        result = build_detail_page(
            main_img=main_cropped,
            product_name=product_name,
            item_text=item_text,
            material_text=material_text,
            size_text=size_text,
            thickness_text=thickness_text,
            weight_text=weight_text,
            extra_text=extra_text,
            model_imgs=model_cropped_images,
            product_imgs=product_cropped_images,
        )

        st.success("상세페이지 생성 완료")
        st.image(result, caption="생성 결과", use_container_width=True)

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
