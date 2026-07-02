import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import tempfile
import webbrowser
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps  # PyInstaller collection hint


HOST = "127.0.0.1"
PORT = 8501
URL = f"http://localhost:{PORT}"
HEARTBEAT_TIMEOUT_SECONDS = 12
SHUTDOWN_CHECK_SECONDS = 1


def bundled_path() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def wait_until_ready() -> None:
    for _ in range(80):
        try:
            with socket.create_connection((HOST, PORT), timeout=0.25):
                return
        except OSError:
            time.sleep(0.25)


def browser_candidates() -> list[Path]:
    candidates: list[Path] = []

    if sys.platform == "win32":
        roots = [
            os.environ.get("PROGRAMFILES"),
            os.environ.get("PROGRAMFILES(X86)"),
            os.environ.get("LOCALAPPDATA"),
        ]
        for root in [Path(p) for p in roots if p]:
            candidates.extend(
                [
                    root / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                    root / "Google" / "Chrome" / "Application" / "chrome.exe",
                ]
            )
        for name in ("msedge", "chrome"):
            path = shutil.which(name)
            if path:
                candidates.append(Path(path))
    elif sys.platform == "darwin":
        candidates.extend(
            [
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
            ]
        )
    else:
        for name in ("google-chrome", "microsoft-edge", "chromium", "chromium-browser"):
            path = shutil.which(name)
            if path:
                candidates.append(Path(path))

    seen: set[Path] = set()
    existing: list[Path] = []
    for path in candidates:
        resolved = path.resolve() if path.exists() else path
        if path.exists() and resolved not in seen:
            seen.add(resolved)
            existing.append(path)
    return existing


def launch_managed_browser(profile_dir: Path) -> subprocess.Popen | None:
    for browser in browser_candidates():
        command = [
            str(browser),
            f"--app={URL}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-mode",
        ]
        try:
            return subprocess.Popen(command)
        except OSError:
            continue
    return None


def open_browser_when_ready(flask_app) -> None:
    wait_until_ready()

    temp_dir = Path(tempfile.mkdtemp(prefix="tpof-browser-"))
    browser_process = launch_managed_browser(temp_dir)
    if browser_process is None:
        shutil.rmtree(temp_dir, ignore_errors=True)
        webbrowser.open(URL)
        return

    flask_app.config["DESKTOP_BROWSER_PID"] = browser_process.pid
    browser_process.wait()
    shutil.rmtree(temp_dir, ignore_errors=True)
    os._exit(0)


def exit_when_browser_closes(flask_app) -> None:
    if os.environ.get("TPOF_EXIT_ON_BROWSER_CLOSE") != "1":
        return

    while True:
        time.sleep(SHUTDOWN_CHECK_SECONDS)
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
        threading.Thread(target=open_browser_when_ready, args=(flask_app,), daemon=True).start()
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
