# tpof

Jewelry detail page maker.

## Run

```bash
pip install -r requirements.txt
python run_app.py
```

The app opens at `http://localhost:8501`.

## What It Does

- Load and save detail-page config JSON files
- Upload and crop one main image
- Upload and crop multiple model images
- Upload, crop, and rotate multiple product images
- Generate and download the final JPG detail page

The UI runs on Flask instead of Streamlit. Crop and rotation work happens in the browser with Cropper.js, so the Python server only runs when the final JPG is generated.
