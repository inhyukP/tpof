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
HEARTBEAT_TIMEOUT_SECONDS = 90
SHUTDOWN_CHECK_SECONDS = 1


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


def exit_when_browser_closes(flask_app) -> None:
    if os.environ.get("TPOF_EXIT_ON_BROWSER_CLOSE") != "1":
        return

    while True:
        time.sleep(SHUTDOWN_CHECK_SECONDS)
        if not flask_app.config.get("DESKTOP_CLIENT_CONNECTED"):
            continue

        now = time.monotonic()
        shutdown_at = flask_app.config.get("DESKTOP_SHUTDOWN_AT")
        if shutdown_at is not None and now >= shutdown_at:
            os._exit(0)

        last_heartbeat = flask_app.config.get("DESKTOP_LAST_HEARTBEAT", 0.0)
        if last_heartbeat and now - last_heartbeat > HEARTBEAT_TIMEOUT_SECONDS:
            os._exit(0)


if __name__ == "__main__":
    base = bundled_path()
    os.chdir(base)
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    os.environ.setdefault("TPOF_EXIT_ON_BROWSER_CLOSE", "1")

    from app import create_app

    flask_app = create_app()
    if os.environ.get("TPOF_OPEN_BROWSER", "1") == "1":
        threading.Thread(target=open_browser_when_ready, daemon=True).start()
    threading.Thread(target=exit_when_browser_closes, args=(flask_app,), daemon=True).start()

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
