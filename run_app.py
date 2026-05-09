import os
import sys
from pathlib import Path

from streamlit.web import cli as stcli


def bundled_path() -> Path:
    # PyInstaller onefile/onedir 실행 시 내부 리소스 위치
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


if __name__ == "__main__":
    base = bundled_path()
    app_path = base / "app.py"

    # app.py 안에서 Path("assets/..."), Path("fonts/...")를 쓰므로
    # 작업 디렉터리를 번들 내부로 맞춘다.
    os.chdir(base)

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.headless=false",
        "--server.fileWatcherType=none",
    ]

    sys.exit(stcli.main())
