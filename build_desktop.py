import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
SPEC = ROOT / "tpof.spec"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def archive_output() -> Path:
    system = platform.system().lower()
    if system == "windows":
        source = DIST / "TPOF.exe"
        if not source.exists():
            raise FileNotFoundError(f"Build output not found: {source}")
        return source
    elif system == "darwin":
        source = DIST / "TPOF.app"
        archive_base = DIST / "TPOF-mac"
    else:
        source = DIST / "TPOF"
        archive_base = DIST / f"TPOF-{system}"

    if not source.exists():
        raise FileNotFoundError(f"Build output not found: {source}")

    archive = Path(shutil.make_archive(str(archive_base), "zip", source.parent, source.name))
    return archive


def main() -> None:
    shutil.rmtree(DIST, ignore_errors=True)
    shutil.rmtree(BUILD, ignore_errors=True)
    run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(SPEC)])
    archive = archive_output()
    print(f"Built {archive}")


if __name__ == "__main__":
    main()
