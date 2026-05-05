import io
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps
from streamlit_cropper import st_cropper


PAGE_W = 860
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
DESC_BG = (245, 245, 245)
PHOTO_GAP = 32
PRODUCT_CUT_H = 980
POST_BOX_PATH = Path("assets/postfix_box.jpg")
KOREAN_FONT_NOTICE = "한글이 깨지지 않도록 Pretendard 또는 Noto Sans CJK/Nanum 계열 폰트를 설치하거나 ./fonts 폴더에 Pretendard-Regular.otf, Pretendard-Bold.otf를 넣어주세요."


def get_font_candidates(bold: bool = False) -> list[Path]:
    pretendard_name = "Pretendard-Bold" if bold else "Pretendard-Regular"
    return [
        Path(f"{pretendard_name}.otf"),
        Path(f"{pretendard_name}.ttf"),
        Path("fonts") / f"{pretendard_name}.otf",
        Path("fonts") / f"{pretendard_name}.ttf",
        Path("/usr/share/fonts/truetype/pretendard") / f"{pretendard_name}.ttf",
        Path("/usr/share/fonts/opentype/pretendard") / f"{pretendard_name}.otf",
        Path("C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf"),
        Path("/System/Library/Fonts/AppleSDGothicNeoB.ttc" if bold else "/System/Library/Fonts/AppleSDGothicNeo.ttc"),
        Path("/Library/Fonts/AppleGothic.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJKkr-Bold.otf" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf"),
        Path("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    ]


def get_font_path(bold: bool = False) -> Path | None:
    for path in get_font_candidates(bold):
        if path.exists():
            return path
    return None


def get_font(size: int, bold: bool = False):
    font_path = get_font_path(bold) or get_font_path(False)
    if font_path is None:
        raise FileNotFoundError(KOREAN_FONT_NOTICE)
    return ImageFont.truetype(str(font_path), size)


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


def spacer(height: int, bg=WHITE) -> Image.Image:
    return Image.new("RGB", (PAGE_W, height), bg)


def crop_with_ui(img: Image.Image, key: str, label: str, aspect_ratio: tuple[int, int]) -> Image.Image:
    st.markdown(f"**{label} 크롭**")
    st.caption("crop 박스를 조정한뒤 더블클릭하면 crop 결과가 적용됩니다")
    cropped = st_cropper(
        img,
        realtime_update=True,
        box_color="#4CAF50",
        aspect_ratio=aspect_ratio,
        return_type="image",
        key=key,
    )
    return cropped.convert("RGB") if isinstance(cropped, Image.Image) else img


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
    title_font = get_font(46, bold=True)
    body_font = get_font(28, bold=False)

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

    max_text_w = int(PAGE_W * 0.83)

    wrapped_lines = []
    for raw in lines_raw:
        if raw == "":
            wrapped_lines.append("")
        else:
            wrapped_lines.extend(wrap_text(draw, raw, body_font, max_text_w))

    line_h = 44
    top_pad = 82
    title_gap = 76
    bottom_pad = 78

    height = top_pad + title_gap + len(wrapped_lines) * line_h + bottom_pad
    if height < 430:
        height = 430

    img = Image.new("RGB", (PAGE_W, height), DESC_BG)
    draw = ImageDraw.Draw(img)

    draw.text(
        (40, 82),
        product_name if product_name.strip() else "Product Name",
        font=title_font,
        fill=BLACK,
        anchor="la",
    )

    y = 182
    for line in wrapped_lines:
        draw.text((40, y), line, font=body_font, fill=BLACK, anchor="la")
        y += line_h

    return img


def build_postfix_text_block() -> Image.Image:
    title_font = get_font(56, bold=True)
    body_font = get_font(26, bold=False)

    text = [
        ("GO GREEN PACKAGE", [
            " ",
            "더파트오브는 지구의 환경 보호를 위해 노력합니다.",
            "패키지는 모두 재활용이 가능한 종이와 면으로 제작되었습니다.",
            "면 파우치는 주얼리 외에도 작은 물건을 담아 보관하는 용도로 재사용하실 수 있습니다. 제품의 보관을 위한 폴리백과 더파트오브 정품 보증서를 함께 보내드립니다. 배송 1건당 한 개의 패키지가 제공되나 상품별 별도 포장이 필요하실 경우 추가 개별 포장을 요청 바랍니다.",
        ]),
        ("Creating a Green Future Together"),
        ("ORDER", [
            " ",
            "[일반 상품] 주문 확인 후 1~3일 내로 배송됩니다.",
            "[주문 제작 상품] 사이즈/이니셜 선택이 필요한 제품은 핸드메이드 주문 제작으로 영업일 기준 7일-14일 제작 기간이 소요될 수 있습니다.",
            "급한 주문건은 카카오톡 채널 @thepartof로 문의 바랍니다.",
            "상품 제작은 주문 확인 후 시작되며 검수 후 출고됩니다.",
        ]),
        ("EXCHANGE / RETURN", [
            " ",
            "모든 교환 및 환불 문의는 카카오톡 채널 @thepartof 또는 홈페이지 Q&A 게시판을 통해 접수해 주시기 바랍니다.",
            "더파트오브의 모든 제품은 엄격하고 꼼꼼한 검수 과정을 거쳐 출고됩니다.",
            "혹시라도 제품에 결함이 있는 경우에는 수령 후 24시간 이내에 카카오톡 상담이나 게시판을 통해 사진과 함께 접수 부탁드립니다.",
            "원활한 처리를 위해 접수 완료 시점으로부터 7일 이내에 배송된 택배사를 통한 제품 회수가 이루어져야 합니다.",
            "확인된 초기 상품 불량의 경우에는 동일한 새 제품으로 교환해 드립니다.",
            "제품 착용 이후에 발생하는 결함이나 문제는 A/S 상담을 통해 안내받으실 수 있으며 수리 내용에 따라 비용이 발생할 수 있습니다."
        ]),
        ("AFTER SERVICE", [
            " ",
            "품질 보증 기간은 보증서 기준이며, 제품별로 수리 가능 여부가 다를 수 있습니다. 제품을 보내시기 전에 A/S 가능 여부를 카카오톡 채널을 통해 확인 바랍니다.",
            "A/S 문의 : 카카오톡 채널 @thepartof",
        ]),
        ("ATTENTION", [
            " ",
            "착용 흔적/오염/훼손이 있는 경우 교환 및 반품이 제한될 수 있습니다.",
            "제작 과정상의 미세한 스크래치, 기포, 천연석의 컬러, 톤, 크기 등은 상품/교환 환불 사유에 해당 되지 않습니다.",
            "사용자의 환경이나 해상도 설정에 따라 실제 제품의 색상과 다소 차이가 있을 수 있습니다.",
            "금속 알레르기 반응이 있는 고객님께서는 소재를 충분히 확인하신 후 신중한 구매를 부탁드립니다.",
            "구매 전 미리 공지해 드린 유의 사항을 숙지하지 않아 발생하는 문제에 대해서는 처리가 어려울 수 있습니다.",
            "기타 제품 불량은 소비자 분쟁 해결 기준에 따라 공정하게 보상해 드립니다."
        ]),
    ]

    temp = Image.new("RGB", (PAGE_W, 100), DESC_BG)
    d = ImageDraw.Draw(temp)
    max_w = int(PAGE_W * 0.86)

    lines = []
    for header, body_lines in text:
        lines.append(("header", header))
        for bl in body_lines:
            for wrapped in wrap_text(d, bl, body_font, max_w):
                lines.append(("body", wrapped))
        lines.append(("space", ""))

    h = 120
    for kind, _ in lines:
        h += 72 if kind == "header" else 46 if kind == "body" else 30
    h += 60

    img = Image.new("RGB", (PAGE_W, h), DESC_BG)
    d = ImageDraw.Draw(img)
    y = 80
    cx = PAGE_W // 2

    for kind, txt in lines:
        if kind == "header":
            d.text((cx, y), txt, font=title_font, fill=BLACK, anchor="ma")
            y += 72
        elif kind == "body":
            d.text((40, y), txt, font=body_font, fill=BLACK, anchor="la")
            y += 46
        else:
            y += 30

    return img


def stack_blocks(blocks):
    total_h = sum(block.height for block in blocks)
    canvas = Image.new("RGB", (PAGE_W, total_h), WHITE)

    y = 0
    for block in blocks:
        canvas.paste(block, (0, y))
        y += block.height

    return canvas


def build_detail_page(
    main_img,
    product_name,
    item_text,
    material_text,
    size_text,
    thickness_text,
    weight_text,
    extra_text,
    model_imgs,
    product_imgs,
):
    blocks = []

    blocks.append(resize_cover(main_img, PAGE_W, 980))
    blocks.append(spacer(PHOTO_GAP))

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
    blocks.append(spacer(PHOTO_GAP))

    for img in model_imgs:
        blocks.append(resize_cover(img, PAGE_W, 980))
        blocks.append(spacer(PHOTO_GAP))

    for img in product_imgs:
        blocks.append(resize_contain(img, PAGE_W, PRODUCT_CUT_H, bg=WHITE))
        blocks.append(spacer(PHOTO_GAP))

    if POST_BOX_PATH.exists():
        post_box = Image.open(POST_BOX_PATH)
        post_box = ImageOps.exif_transpose(post_box).convert("RGB")
        blocks.append(resize_cover(post_box, PAGE_W, PRODUCT_CUT_H))
        blocks.append(spacer(PHOTO_GAP))

    blocks.append(build_postfix_text_block())

    return stack_blocks(blocks)


st.set_page_config(page_title="Jewelry Detail Page Maker", layout="centered")
st.title("Jewelry Detail Page Maker")

st.markdown("### 1. Main 사진 1장 업로드")
main_file = st.file_uploader(
    "Main 사진 1장을 업로드하세요",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=False,
    key="main_file",
)

main_img = None
if main_file:
    main_img = load_image(main_file)
    main_img = crop_with_ui(main_img, key="main_crop", label="Main 사진", aspect_ratio=(43, 49))
    st.image(main_img, caption="Main 사진(크롭 적용)", use_container_width=True)

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

model_imgs = []
if model_files:
    st.write(f"모델컷 업로드 수: {len(model_files)}")
    for i, file in enumerate(model_files):
        src = load_image(file)
        cropped = crop_with_ui(src, key=f"model_crop_{i}", label=f"모델컷 {i + 1}", aspect_ratio=(43, 49))
        model_imgs.append(cropped)

    cols = st.columns(3)
    for i, img in enumerate(model_imgs):
        with cols[i % 3]:
            st.image(img, use_container_width=True)

st.markdown("---")

st.markdown("### 4. 제품컷 사진들 업로드")
product_files = st.file_uploader(
    "제품컷 사진을 여러 장 업로드하세요",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    key="product_files",
)

product_imgs = []
if product_files:
    st.write(f"제품컷 업로드 수: {len(product_files)}")
    for i, file in enumerate(product_files):
        src = load_image(file)
        cropped = crop_with_ui(src, key=f"product_crop_{i}", label=f"제품컷 {i + 1}", aspect_ratio=(43, 45))
        product_imgs.append(cropped)

    cols = st.columns(3)
    for i, img in enumerate(product_imgs):
        with cols[i % 3]:
            st.image(img, use_container_width=True)

st.markdown("---")

korean_font_ready = get_font_path(False) is not None or get_font_path(True) is not None
if not korean_font_ready:
    st.error(KOREAN_FONT_NOTICE)
    st.stop()

if not POST_BOX_PATH.exists():
    st.warning("고정 박스 사진 파일이 없습니다: assets/postfix_box.jpg")


if st.button("상세페이지 생성"):
    if main_img is None:
        st.error("Main 사진 1장은 반드시 필요합니다.")
    else:
        result = build_detail_page(
            main_img=main_img,
            product_name=product_name,
            item_text=item_text,
            material_text=material_text,
            size_text=size_text,
            thickness_text=thickness_text,
            weight_text=weight_text,
            extra_text=extra_text,
            model_imgs=model_imgs,
            product_imgs=product_imgs,
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
