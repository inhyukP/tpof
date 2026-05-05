import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont

# --- 설정 값 ---
TARGET_WIDTH = 860         # 온라인 쇼핑몰/상세페이지 표준 가로 사이즈
MARGIN_BETWEEN = 20        # 이미지 사이의 여백 (픽셀)
BG_COLOR = (255, 255, 255) # 배경색 (흰색)

def select_images():
    """윈도우/맥 기본 파일 선택창을 띄워 여러 장의 이미지를 선택합니다."""
    root = tk.Tk()
    root.withdraw() # 메인 윈도우 숨김
    file_paths = filedialog.askopenfilenames(
        title="상세페이지로 만들 주얼리 사진들을 선택하세요 (순서대로 정렬됨)",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")]
    )
    return sorted(list(file_paths))

def add_marketing_copy(draw, width, current_y):
    """
    고급스러운 주얼리 마케팅 카피를 이미지 중간에 삽입하는 공간입니다.
    폰트 파일(.ttf) 경로를 지정하면 텍스트를 이미지에 렌더링할 수 있습니다.
    """
    # 텍스트 영역의 높이
    text_area_height = 200
    
    # 폰트 적용 예시 (Windows: malgun.ttf, Mac: AppleGothic 등 시스템 폰트 경로 지정 필요)
    # try:
    #     font = ImageFont.truetype("malgun.ttf", 24)
    #     copy_text = "시간이 지나도 변하지 않는 가치,\n섬세한 세공으로 완성된 하이엔드 컬렉션"
    #     draw.text((width//2 - 150, current_y + 80), copy_text, fill=(50, 50, 50), font=font, align="center")
    # except IOError:
    #     pass # 폰트가 없으면 생략
        
    return text_area_height

def generate_detail_page():
    image_paths = select_images()
    
    if not image_paths:
        print("이미지 선택이 취소되었습니다.")
        return

    print(f"총 {len(image_paths)}장의 이미지를 병합합니다...")

    images = []
    total_height = 0

    # 1. 이미지 로드 및 리사이징
    for path in image_paths:
        try:
            img = Image.open(path)
            # RGB 모드로 변환 (알파 채널 제거하여 저장 오류 방지)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
                
            aspect_ratio = img.height / img.width
            new_height = int(TARGET_WIDTH * aspect_ratio)
            img = img.resize((TARGET_WIDTH, new_height), Image.Resampling.LANCZOS)
            
            images.append(img)
            total_height += new_height + MARGIN_BETWEEN
        except Exception as e:
            print(f"이미지 로드 실패 ({path}): {e}")

    if not images:
        return

    # 마케팅 카피가 들어갈 여백 높이 추가 (가장 상단에 배치한다고 가정)
    text_area_height = 200
    total_height += text_area_height

    # 2. 전체 배경 캔버스 생성
    final_image = Image.new('RGB', (TARGET_WIDTH, total_height), color=BG_COLOR)
    draw = ImageDraw.Draw(final_image)

    current_y = 0

    # 3. 최상단 마케팅 텍스트 영역 렌더링
    current_y += add_marketing_copy(draw, TARGET_WIDTH, current_y)

    # 4. 캔버스에 순차적으로 이미지 페이스트
    for img in images:
        final_image.paste(img, (0, current_y))
        current_y += img.height + MARGIN_BETWEEN

    # 5. 최종 이미지 저장 (첫 번째 이미지가 있던 폴더에 저장)
    first_image_dir = os.path.dirname(image_paths[0])
    output_path = os.path.join(first_image_dir, "jewelry_detail_page_output.jpg")
    
    final_image.save(output_path, quality=95) # 고품질 JPEG로 저장
    
    # 완료 메시지 박스
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("작업 완료", f"상세페이지 생성이 완료되었습니다!\n저장 위치: {output_path}")
    print(f"완료되었습니다! 저장 위치: {output_path}")

if __name__ == "__main__":
    generate_detail_page()
