import os
import sys
from pathlib import Path


def bundled_path() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


if __name__ == "__main__":
    base = bundled_path()
    app_path = base / "app.py"

    os.chdir(base)

    # Streamlit을 import하기 전에 설정
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_BROWSER_SERVER_ADDRESS"] = "localhost"
    os.environ["STREAMLIT_BROWSER_SERVER_PORT"] = "8501"

    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),

        # 핵심: PyInstaller 실행 시 개발 모드 해제
        "--global.developmentMode=false",

        # 서버 포트
        "--server.port=8501",
        "--server.address=127.0.0.1",

        # 브라우저 자동 실행 주소
        "--browser.serverAddress=localhost",
        "--browser.serverPort=8501",

        "--server.headless=false",
        "--server.fileWatcherType=none",
    ]

    sys.exit(stcli.main())
