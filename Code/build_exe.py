#!/usr/bin/env python3
"""
Build script for creating an executable of Space Station Explorer
"""

import os
import sys
import subprocess
import shutil
import platform

def main():
    print("Building Space Station Explorer executable...")
    
    # Check for PyInstaller
    try:
        import PyInstaller
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
    
    # Check for required dependencies
    try:
        import matplotlib
        import tkinter
        print("Required dependencies found.")
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install the required dependencies with: pip install -r requirements.txt")
        sys.exit(1)
    
    # Create build directory if it doesn't exist
    os.makedirs("build", exist_ok=True)
    
    # Create a spec file
    spec_file = "space_station_explorer.spec"
    with open(spec_file, "w") as f:
        f.write("""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_game.py'],
    pathex=[],
    binaries=[],
    datas=[('game/*.py', 'game')],
    hiddenimports=['matplotlib', 'matplotlib.backends.backend_tkagg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SpaceStationExplorer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='space_station_icon.ico' if os.path.exists('space_station_icon.ico') else None,
)
""")
    
    print("Spec file created.")
    
    # Determine the correct PyInstaller command based on platform
    pyinstaller_cmd = [sys.executable, "-m", "PyInstaller", "--clean", spec_file]
    
    # Run PyInstaller
    print("Running PyInstaller... (this may take a while)")
    try:
        subprocess.check_call(pyinstaller_cmd)
        print("PyInstaller completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller failed with error code: {e.returncode}")
        sys.exit(1)
    
    # Create saves directory directly in the dist folder, not under a separate game_data folder
    # This matches how the game will create saves when run as an EXE
    dist_folder = os.path.join("dist", "SpaceStationExplorer")
    
    # Success message
    print(f"\nBuild completed successfully!")
    print(f"Executable can be found at: {os.path.abspath(os.path.join(dist_folder, 'SpaceStationExplorer.exe'))}")
    print("\nTo run the game, simply double-click the executable file.")
    print("Save files will be stored in the 'saves' directory alongside the executable.")

if __name__ == "__main__":
    main() 