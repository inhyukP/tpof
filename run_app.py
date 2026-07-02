import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps  # PyInstaller collection hint


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
    os.chdir(base)
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

    from app import create_app

    flask_app = create_app()
    threading.Thread(target=open_browser_when_ready, daemon=True).start()

    try:
        from waitress import serve

        serve(flask_app, host=HOST, port=PORT, threads=8)
    except ImportError:
        flask_app.run(
            host=HOST,
            port=PORT,
            debug=False,
            threaded=True,
            use_reloader=False,
        )
