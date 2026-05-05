import streamlit as st
from PIL import Image
import io

# 1. 페이지 설정 및 UI
st.set_page_config(page_title="Jewelry Detail Page Creator", layout="centered")
st.title("✨ 주얼리 상세페이지 자동 생성기")
st.markdown("---")
st.info("10장의 사진을 업로드하면 레퍼런스 스타일의 수직 통합 상세페이지를 생성합니다.")

# 2. 파일 업로드
uploaded_files = st.file_uploader(
    "사진을 업로드하세요 (파일명 순서대로 정렬됩니다)", 
    accept_multiple_files=True, 
    type=['jpg', 'jpeg', 'png', 'webp']
)

if uploaded_files:
    # 3. 옵션 설정
    col1, col2 = st.columns(2)
    with col1:
        target_width = st.number_input("상세페이지 가로 폭 (px)", value=860)
    with col2:
        spacing = st.number_input("이미지 간 간격 (px)", value=20)

    if st.button("상세페이지 생성하기"):
        with st.spinner("이미지를 병합 중입니다..."):
            # 이미지 로드 및 리사이징
            images = []
            total_height = 0
            
            # 파일 이름순 정렬
            sorted_files = sorted(uploaded_files, key=lambda x: x.name)
            
            for uploaded_file in sorted_files:
                img = Image.open(uploaded_file).convert("RGB")
                
                # 가로폭에 맞춰 비율 유지 리사이징
                aspect_ratio = img.height / img.width
                new_height = int(target_width * aspect_ratio)
                img_resized = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
                
                images.append(img_resized)
                total_height += new_height + spacing

            # 4. 빈 캔버스에 이미지 병합
            # 마지막 간격은 제거
            total_height -= spacing
            final_image = Image.new("RGB", (target_width, total_height), "white")
            
            current_y = 0
            for img in images:
                final_image.paste(img, (0, current_y))
                current_y += img.height + spacing

            # 5. 결과 미리보기 및 다운로드
            st.success("상세페이지 생성이 완료되었습니다!")
            
            # 파일 다운로드를 위한 메모리 버퍼
            buf = io.BytesIO()
            final_image.save(buf, format="JPEG", quality=95)
            byte_im = buf.getvalue()

            st.image(final_image, caption="생성된 상세페이지 미리보기 (축소됨)", use_container_width=True)
            
            st.download_button(
                label="결과물 다운로드 (JPG)",
                data=byte_im,
                file_name="jewelry_detail_page.jpg",
                mime="image/jpeg"
            )
