# tpof

Jewelry detail page maker.

## Run

```bash
pip install -r requirements.txt
python run_app.py
```

The app opens at `http://localhost:8501`.

## Build Desktop Apps

```bash
pip install -r requirements.txt -r requirements-dev.txt
python build_desktop.py
```

The build creates a single `dist/TPOF.exe` file on Windows and `dist/TPOF-mac.zip` on macOS. The GitHub Actions workflow builds both artifacts automatically for the PR branch.
In desktop builds, closing the browser tab also shuts down the local app process.

## What It Does

- Load and save detail-page config JSON files
- Upload and crop one main image
- Upload and crop multiple model images
- Upload, crop, and drag-rotate multiple product images
- Generate and download the final JPG detail page

The UI runs on Flask instead of Streamlit. Crop and rotation work happens in the browser with the built-in editor, so the Python server only runs when the final JPG is generated.
