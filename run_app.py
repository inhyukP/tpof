import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps  # PyInstaller 수집용


HOST = "127.0.0.1"
PORT = 8501
URL = f"http://localhost:{PORT}"


def bundled_path() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def open_browser_when_ready() -> None:
    for _ in range(80):
        try:
            with socket.create_connection((HOST, PORT), timeout=0.25):
                webbrowser.open(URL)
                return
        except OSError:
            time.sleep(0.25)

    webbrowser.open(URL)


if __name__ == "__main__":
    base = bundled_path()
    app_path = base / "app.py"

    os.chdir(base)

    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = HOST
    os.environ["STREAMLIT_SERVER_PORT"] = str(PORT)
    os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
    os.environ["STREAMLIT_BROWSER_SERVER_ADDRESS"] = "localhost"
    os.environ["STREAMLIT_BROWSER_SERVER_PORT"] = str(PORT)

    from streamlit.web import cli as stcli

    threading.Thread(target=open_browser_when_ready, daemon=True).start()

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--global.developmentMode=false",
        "--server.headless=true",
        f"--server.address={HOST}",
        f"--server.port={PORT}",
        "--server.fileWatcherType=none",
        "--browser.serverAddress=localhost",
        f"--browser.serverPort={PORT}",
    ]

    sys.exit(stcli.main())
