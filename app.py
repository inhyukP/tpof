import base64
import io
import json
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from PIL import Image, ImageDraw, ImageFont, ImageOps
from werkzeug.exceptions import RequestEntityTooLarge


BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
PAGE_W = 860
BLACK = (20, 20, 20)
PAGE_BG = (245, 245, 245)
PHOTO_GAP = 10
PHOTO_BORDER = 20
MODEL_CUT_H = 1056
PRODUCT_CUT_H = 980
POST_BOX_PATH = BASE_DIR / "assets" / "postfix_box_lot.JPG"
CONFIG_VERSION = 1
ITEM_OPTIONS = ["NECKLACE", "EARRING", "RING", "BRACELET", "ANKLET", "직접입력"]
KOREAN_FONT_NOTICE = (
    "한글이 깨지지 않도록 Pretendard 또는 Noto Sans CJK/Nanum 계열 폰트를 "
    "설치하거나 ./fonts 폴더에 Pretendard-Regular.otf, Pretendard-Bold.otf를 넣어주세요."
)


def get_font_candidates(bold: bool = False) -> list[Path]:
    pretendard_name = "Pretendard-Bold" if bold else "Pretendard-Regular"
    return [
        BASE_DIR / f"{pretendard_name}.otf",
        BASE_DIR / f"{pretendard_name}.ttf",
        BASE_DIR / "fonts" / f"{pretendard_name}.otf",
        BASE_DIR / "fonts" / f"{pretendard_name}.ttf",
        Path(f"{pretendard_name}.otf"),
        Path(f"{pretendard_name}.ttf"),
        Path("fonts") / f"{pretendard_name}.otf",
        Path("fonts") / f"{pretendard_name}.ttf",
        Path("/usr/share/fonts/truetype/pretendard") / f"{pretendard_name}.ttf",
        Path("/usr/share/fonts/opentype/pretendard") / f"{pretendard_name}.otf",
        Path("C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf"),
        Path(
            "/System/Library/Fonts/AppleSDGothicNeoB.ttc"
            if bold
            else "/System/Library/Fonts/AppleSDGothicNeo.ttc"
        ),
        Path("/Library/Fonts/AppleGothic.ttf"),
        Path(
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
            if bold
            else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        ),
        Path(
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"
            if bold
            else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
        ),
        Path(
            "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Bold.otf"
            if bold
            else "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf"
        ),
        Path(
            "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"
            if bold
            else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
        ),
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


def load_image_bytes(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
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


def resize_contain(img: Image.Image, w: int, h: int, bg=PAGE_BG) -> Image.Image:
    iw, ih = img.size
    scale = min(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    resized = img.resize((nw, nh), Image.LANCZOS)

    canvas = Image.new("RGB", (w, h), bg)
    x = (w - nw) // 2
    y = (h - nh) // 2
    canvas.paste(resized, (x, y))
    return canvas


def spacer(height: int, bg=PAGE_BG) -> Image.Image:
    return Image.new("RGB", (PAGE_W, height), bg)


def add_bg_border(
    block: Image.Image,
    border: int,
    bg=PAGE_BG,
    fit_mode: str = "cover",
) -> Image.Image:
    if border <= 0:
        return block

    inner_w = max(1, block.width - (border * 2))
    inner_h = max(1, block.height - (border * 2))

    if fit_mode == "contain":
        inner = resize_contain(block, inner_w, inner_h, bg=bg)
    else:
        inner = resize_cover(block, inner_w, inner_h)

    canvas = Image.new("RGB", (block.width, block.height), bg)
    canvas.paste(inner, (border, border))
    return canvas


def build_product_image_block(
    img: Image.Image,
    border: int = PHOTO_BORDER,
    max_h: int = PRODUCT_CUT_H,
    bg=PAGE_BG,
) -> Image.Image:
    inner_w = max(1, PAGE_W - (border * 2))
    inner_max_h = max(1, max_h - (border * 2))
    iw, ih = img.size
    scale = min(inner_w / iw, inner_max_h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    resized = img.resize((nw, nh), Image.LANCZOS)

    block_h = nh + (border * 2)
    canvas = Image.new("RGB", (PAGE_W, block_h), bg)
    x = (PAGE_W - nw) // 2
    canvas.paste(resized, (x, border))
    return canvas


def image_to_data_url(
    img: Image.Image,
    image_format: str = "PNG",
    **save_kwargs,
) -> str:
    buf = io.BytesIO()
    fmt = image_format.upper()
    mime = "jpeg" if fmt == "JPEG" else fmt.lower()
    img.convert("RGB").save(buf, format=fmt, **save_kwargs)
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/{mime};base64,{encoded}"


def image_from_data_url(data_url: str) -> Image.Image:
    if not data_url:
        raise ValueError("이미지 데이터가 비어 있습니다.")
    if "," in data_url:
        _, encoded = data_url.split(",", 1)
    else:
        encoded = data_url
    raw = base64.b64decode(encoded)
    return load_image_bytes(raw)


def images_from_payload(payload: dict, key: str) -> list[Image.Image]:
    values = payload.get(key) or []
    return [image_from_data_url(data_url) for data_url in values if data_url]


def config_to_bytes(config: dict) -> bytes:
    return json.dumps(config, ensure_ascii=False).encode("utf-8")


def normalize_download_filename(
    filename: str,
    default: str = "detail_page_config.json",
    extension: str = ".json",
) -> str:
    cleaned = Path(filename.strip()).name if filename.strip() else default
    if cleaned in {"", ".", ".."}:
        cleaned = default
    if not cleaned.lower().endswith(extension):
        cleaned = f"{cleaned}{extension}"
    return cleaned


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


def get_description_lines(
    item_text: str,
    material_text: str,
    size_text: str,
    pendant_text: str,
    thickness_text: str,
    weight_text: str,
    extra_text: str = "",
) -> list[str]:
    lines = []
    if item_text.strip():
        lines.append(f"Item: {item_text}")
    if material_text.strip():
        lines.append(f"Material: {material_text}")
    if size_text.strip():
        lines.append(f"Size: {size_text}")
    if pendant_text.strip():
        lines.append(f"Pendant: {pendant_text}")
    if thickness_text.strip():
        lines.append(f"Thickness: {thickness_text}")
    if weight_text.strip():
        lines.append(f"Weight: {weight_text}")
    if extra_text.strip():
        lines.extend(extra_text.splitlines())

    return lines


def has_description_content(
    product_name: str,
    item_text: str,
    material_text: str,
    size_text: str,
    pendant_text: str,
    thickness_text: str,
    weight_text: str,
    extra_text: str = "",
) -> bool:
    return bool(
        product_name.strip()
        or item_text.strip()
        or material_text.strip()
        or size_text.strip()
        or pendant_text.strip()
        or thickness_text.strip()
        or weight_text.strip()
        or extra_text.strip()
    )


def build_description_block(
    product_name: str,
    item_text: str,
    material_text: str,
    size_text: str,
    pendant_text: str,
    thickness_text: str,
    weight_text: str,
    extra_text: str = "",
) -> Image.Image:
    title_font = get_font(46, bold=True)
    body_font = get_font(28, bold=False)

    lines_raw = get_description_lines(
        item_text=item_text,
        material_text=material_text,
        size_text=size_text,
        pendant_text=pendant_text,
        thickness_text=thickness_text,
        weight_text=weight_text,
        extra_text=extra_text,
    )

    temp = Image.new("RGB", (PAGE_W, 100), PAGE_BG)
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
    has_title = bool(product_name.strip())
    text_start_y = top_pad + title_gap if has_title else top_pad

    height = text_start_y + len(wrapped_lines) * line_h + bottom_pad
    if height < 430:
        height = 430

    img = Image.new("RGB", (PAGE_W, height), PAGE_BG)
    draw = ImageDraw.Draw(img)

    if has_title:
        draw.text(
            (40, 82),
            product_name,
            font=title_font,
            fill=BLACK,
            anchor="la",
        )

    y = text_start_y
    for line in wrapped_lines:
        draw.text((40, y), line, font=body_font, fill=BLACK, anchor="la")
        y += line_h

    return img


def build_postfix_text_block() -> Image.Image:
    title_font = get_font(45, bold=True)
    body_font = get_font(26, bold=False)

    text = [
        (
            "GO GREEN PACKAGE",
            [
                "더파트오브는 지구의 환경 보호를 위해 노력합니다.",
                "패키지는 모두 재활용이 가능한 종이와 면으로 제작되었습니다.",
                "함께 보내드리는 면 파우치는 주얼리 보관 외에도 일상의 작은 소품들을",
                "담는 용도로 자유롭게 재사용해 보세요. 제품의 안전한 보관을 위한 폴리백과 더파트오브 정품 보증서를 함께 보내드립니다. 배송 건당 한 개의 패키지로 구성되나, 상품별로 개별 포장이 필요하신 경우 요청해 주시면 준비해 드리겠습니다.",
            ],
        ),
        (
            "ORDER",
            [
                "[일반 상품] 주문 확인 후 1~3일 내로 배송됩니다.",
                "[주문 제작 상품] 사이즈/이니셜 선택이 필요한 제품은 핸드메이드 주문",
                "제작으로 영업일 기준 7일-14일 제작 기간이 소요될 수 있습니다.",
                "급한 주문건은 카카오톡 채널 @thepartof로 문의 바랍니다.",
                "상품 제작은 주문 확인 후 시작되며 검수 후 출고됩니다.",
            ],
        ),
        (
            "EXCHANGE / RETURN",
            [
                "모든 교환 및 환불 문의는 카카오톡 채널 @thepartof 또는 홈페이지",
                "Q&A 게시판을 통해 접수해 주시기 바랍니다.",
                "더파트오브의 모든 제품은 엄격하고 꼼꼼한 검수 과정을 거쳐 출고됩니다.",
                "혹시라도 제품에 결함이 있는 경우에는 수령 후 24시간 이내에 카카오톡  상담이나 게시판을 통해 사진과 함께 접수 부탁드립니다.",
                "원활한 처리를 위해 접수 완료 시점으로부터 7일 이내에 배송된 택배사를 통한 제품 회수가 이루어져야 합니다.",
                "확인된 초기 상품 불량의 경우에는 동일한 새 제품으로 교환해 드립니다.",
                "제품 착용 이후에 발생하는 결함이나 문제는 A/S 상담을 통해 안내받으실 수 있으며 수리 내용에 따라 비용이 발생할 수 있습니다.",
            ],
        ),
        (
            "AFTER SERVICE",
            [
                "품질 보증 기간은 보증서 기준이며, 제품별로 수리 가능 여부가 다를 수",
                "있습니다. 제품을 보내시기 전에 A/S 가능 여부를 카카오톡 채널을 통해 확인바랍니다.",
                "A/S 문의 : 카카오톡 채널 @thepartof",
            ],
        ),
        (
            "ATTENTION",
            [
                "착용 흔적/오염/훼손이 있는 경우 교환 및 반품이 제한될 수 있습니다.",
                "제작 과정상의 미세한 스크래치, 기포, 천연석의 컬러, 톤, 크기 등은 상품/교환 환불 사유에 해당 되지 않습니다.",
                "사용자의 환경이나 해상도 설정에 따라 실제 제품의 색상과 다소 차이가  있을 수 있습니다.",
                "금속 알레르기 반응이 있는 고객님께서는 소재를 충분히 확인하신 후",
                "신중한 구매를 부탁드립니다.",
                "구매 전 미리 공지해 드린 유의 사항을 숙지하지 않아 발생하는 문제에   대해서는 처리가 어려울 수 있습니다.",
                "기타 제품 불량은 소비자 분쟁 해결 기준에 따라 공정하게 보상해 드립니다.",
            ],
        ),
    ]

    temp = Image.new("RGB", (PAGE_W, 100), PAGE_BG)
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

    img = Image.new("RGB", (PAGE_W, h), PAGE_BG)
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
    canvas = Image.new("RGB", (PAGE_W, total_h), PAGE_BG)

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
    pendant_text,
    thickness_text,
    weight_text,
    extra_text,
    model_imgs,
    product_imgs,
):
    blocks = []

    main_block = resize_cover(main_img, PAGE_W, 980)
    blocks.append(add_bg_border(main_block, PHOTO_BORDER, bg=PAGE_BG, fit_mode="cover"))
    blocks.append(spacer(PHOTO_GAP, bg=PAGE_BG))

    if has_description_content(
        product_name=product_name,
        item_text=item_text,
        material_text=material_text,
        size_text=size_text,
        pendant_text=pendant_text,
        thickness_text=thickness_text,
        weight_text=weight_text,
        extra_text=extra_text,
    ):
        desc_block = build_description_block(
            product_name=product_name,
            item_text=item_text,
            material_text=material_text,
            size_text=size_text,
            pendant_text=pendant_text,
            thickness_text=thickness_text,
            weight_text=weight_text,
            extra_text=extra_text,
        )
        blocks.append(desc_block)
        blocks.append(spacer(PHOTO_GAP, bg=PAGE_BG))

    for img in model_imgs:
        model_block = resize_cover(img, PAGE_W, MODEL_CUT_H)
        blocks.append(add_bg_border(model_block, PHOTO_BORDER, bg=PAGE_BG, fit_mode="cover"))
        blocks.append(spacer(PHOTO_GAP, bg=PAGE_BG))

    for img in product_imgs:
        product_block = build_product_image_block(
            img,
            border=PHOTO_BORDER,
            max_h=PRODUCT_CUT_H,
            bg=PAGE_BG,
        )
        blocks.append(product_block)
        blocks.append(spacer(PHOTO_GAP, bg=PAGE_BG))

    if POST_BOX_PATH.exists():
        post_box = Image.open(POST_BOX_PATH)
        post_box = ImageOps.exif_transpose(post_box).convert("RGB")
        post_box_block = resize_cover(post_box, PAGE_W, PRODUCT_CUT_H)
        blocks.append(add_bg_border(post_box_block, PHOTO_BORDER, bg=PAGE_BG, fit_mode="cover"))
        blocks.append(spacer(PHOTO_GAP, bg=PAGE_BG))

    blocks.append(build_postfix_text_block())

    return stack_blocks(blocks)


def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
    app.config["MAX_CONTENT_LENGTH"] = 256 * 1024 * 1024

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            item_options=ITEM_OPTIONS,
            config_version=CONFIG_VERSION,
            font_ready=get_font_path(False) is not None or get_font_path(True) is not None,
            font_notice=KOREAN_FONT_NOTICE,
            post_box_exists=POST_BOX_PATH.exists(),
        )

    @app.post("/api/generate")
    def generate_detail_page():
        payload = request.get_json(silent=True) or {}
        fields = payload.get("fields") or {}

        try:
            main_data = payload.get("main_img")
            if not main_data:
                return jsonify({"error": "Main 사진 1장은 반드시 필요합니다."}), 400

            main_img = image_from_data_url(main_data)
            model_imgs = images_from_payload(payload, "model_imgs")
            product_imgs = images_from_payload(payload, "product_imgs")

            result = build_detail_page(
                main_img=main_img,
                product_name=fields.get("product_name", ""),
                item_text=fields.get("item_text", "NECKLACE"),
                material_text=fields.get("material_text", "S925"),
                size_text=fields.get("size_text", ""),
                pendant_text=fields.get("pendant_text", ""),
                thickness_text=fields.get("thickness_text", ""),
                weight_text=fields.get("weight_text", ""),
                extra_text=fields.get("extra_text", ""),
                model_imgs=model_imgs,
                product_imgs=product_imgs,
            )
        except FileNotFoundError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": f"상세페이지 생성 중 오류가 발생했습니다: {exc}"}), 400

        return jsonify(
            {
                "imageData": image_to_data_url(result, "JPEG", quality=92),
                "width": result.width,
                "height": result.height,
                "fileName": "detail_page.jpg",
            }
        )

    @app.errorhandler(RequestEntityTooLarge)
    def request_entity_too_large(_exc):
        return jsonify({"error": "이미지 데이터가 너무 큽니다. 사진 수나 원본 크기를 줄여주세요."}), 413

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8501"))
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
