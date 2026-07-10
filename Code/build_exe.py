#!/usr/bin/env python3
"""
Build script for creating a Windows onedir executable of Space Station Explorer.
"""

import argparse
import os
import shutil
import sys
import subprocess


SPEC_FILE = "space_station_explorer.spec"
LINUX_ICON_PNG = os.path.join("packaging", "linux", "space_station_icon.png")
WINDOWS_ICON_ICO = os.path.join("build", "space_station_icon.ico")
# PyInstaller COLLECT writes here first; we then flatten into dist/ so the EXE
# sits next to the existing dist/saves/ folder from prior one-file builds.
BUNDLE_DIR = os.path.join("dist", "SpaceStationExplorer")
DIST_EXE = os.path.join("dist", "SpaceStationExplorer.exe")
ICON_SIZES = (16, 32, 48, 256)


def ensure_dependencies():
    """Verify PyInstaller and runtime deps are available."""
    try:
        import PyInstaller  # noqa: F401
        print("PyInstaller found.")
    except ImportError:
        print("PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("PyInstaller installed successfully.")
        except Exception as e:
            print(f"Failed to install PyInstaller: {e}")
            print("Please install PyInstaller manually with: pip install pyinstaller")
            sys.exit(1)

    try:
        import matplotlib  # noqa: F401
        import tkinter  # noqa: F401
        print("Required dependencies found.")
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install the required dependencies with: pip install -r requirements.txt")
        sys.exit(1)


def ensure_windows_icon():
    """Convert the shared Linux PNG icon to a multi-size ICO for the Windows EXE."""
    if not os.path.isfile(LINUX_ICON_PNG):
        print(f"ERROR: Linux icon not found at {LINUX_ICON_PNG}")
        print("The Windows build reuses packaging/linux/space_station_icon.png.")
        sys.exit(1)

    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow (PIL) is required to convert the icon to ICO.")
        print("It normally comes with matplotlib. Try: pip install pillow")
        sys.exit(1)

    os.makedirs("build", exist_ok=True)
    print(f"Converting {LINUX_ICON_PNG} -> {WINDOWS_ICON_ICO}")

    with Image.open(LINUX_ICON_PNG) as src:
        image = src.convert("RGBA")
        max_size = max(ICON_SIZES)
        base = image.copy()
        base.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        base.save(
            WINDOWS_ICON_ICO,
            format="ICO",
            sizes=[(s, s) for s in ICON_SIZES],
        )

    if not os.path.isfile(WINDOWS_ICON_ICO):
        print(f"ERROR: Failed to write {WINDOWS_ICON_ICO}")
        sys.exit(1)
    print("Icon ready.")


def flatten_bundle_into_dist():
    """Move onedir contents to dist/ so the EXE shares dist/saves/ with old builds.

    Layout after flatten:
      dist/SpaceStationExplorer.exe
      dist/_internal/
      dist/saves/   (left untouched if already present)
    """
    if not os.path.isdir(BUNDLE_DIR):
        print(f"ERROR: Expected onedir bundle at {BUNDLE_DIR}")
        sys.exit(1)

    print(f"Flattening {BUNDLE_DIR} into dist/ (preserving dist/saves/)...")
    for name in os.listdir(BUNDLE_DIR):
        if name == "saves":
            continue
        src = os.path.join(BUNDLE_DIR, name)
        dst = os.path.join("dist", name)
        if os.path.exists(dst):
            if os.path.isdir(dst) and not os.path.islink(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)
        shutil.move(src, dst)

    # Clear leftover bundle dir; merge any nested saves into dist/saves
    for name in os.listdir(BUNDLE_DIR):
        path = os.path.join(BUNDLE_DIR, name)
        if name == "saves":
            dest_saves = os.path.join("dist", "saves")
            os.makedirs(dest_saves, exist_ok=True)
            for save_name in os.listdir(path):
                save_src = os.path.join(path, save_name)
                save_dst = os.path.join(dest_saves, save_name)
                if not os.path.exists(save_dst):
                    shutil.move(save_src, save_dst)
            shutil.rmtree(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    os.rmdir(BUNDLE_DIR)

    if not os.path.isfile(DIST_EXE):
        print(f"ERROR: Flatten failed; {DIST_EXE} not found.")
        sys.exit(1)
    print("Flatten complete.")


def main():
    parser = argparse.ArgumentParser(description="Build Space Station Explorer (Windows onedir)")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Force a full PyInstaller rebuild (clears the analysis cache)",
    )
    args = parser.parse_args()

    print("Building Space Station Explorer executable...")
    ensure_dependencies()

    if not os.path.isfile(SPEC_FILE):
        print(f"ERROR: Spec file not found: {SPEC_FILE}")
        sys.exit(1)

    ensure_windows_icon()

    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        SPEC_FILE,
    ]
    if args.clean:
        pyinstaller_cmd.insert(-1, "--clean")
        print("Running PyInstaller with --clean (full rebuild)...")
    else:
        print("Running PyInstaller (incremental; pass --clean for a full rebuild)...")

    try:
        subprocess.check_call(pyinstaller_cmd)
        print("PyInstaller completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed with error code: {e.returncode}")
        sys.exit(1)

    flatten_bundle_into_dist()

    exe_path = os.path.abspath(DIST_EXE)
    print("\nBuild completed successfully!")
    print(f"Executable can be found at: {exe_path}")
    print("Keep the _internal folder next to the EXE.")
    print("Save files use dist/saves/ (same location as previous one-file builds).")


if __name__ == "__main__":
    main()
