# Space Station Explorer - Build Instructions

This document explains how to build and run the Space Station Explorer game as a standalone executable.

## Prerequisites

- Python 3.6 or higher
- Required packages (automatically installed by the build script):
  - matplotlib
  - PyInstaller

## Building the Executable

### Windows

1. Double-click on the `build.bat` file.
2. Wait for the build process to complete (this may take several minutes).
3. The executable will be created in the `dist/SpaceStationExplorer` folder.

### Manual Build (Windows)

You can also manually build the executable:

1. Install required packages: `pip install -r requirements.txt`
2. Run the build script: `python build_exe.py`

### Linux (AppImage)

The Linux build produces a single, portable, double-clickable
`SpaceStationExplorer-x86_64.AppImage` that bundles Python, tkinter and
matplotlib — no system Python is needed to run the result.

**Build prerequisites** (only needed to build, not to run the AppImage):

- `python3` (3.6+) with the tkinter system package:
  - Debian/Ubuntu: `sudo apt install python3-tk`
  - Fedora: `sudo dnf install python3-tkinter`
- Internet access on first run (to fetch `appimagetool`)

**Build:**

```bash
cd Code
./build_appimage.sh
```

The AppImage is written to `dist/SpaceStationExplorer-x86_64.AppImage`.

**Run:**

```bash
./dist/SpaceStationExplorer-x86_64.AppImage
```

Or mark it executable in your file manager (Properties → Permissions →
"Allow executing file as program") and double-click it.

## Running the Game

- **Windows:** double-click `SpaceStationExplorer.exe` in the
  `dist/SpaceStationExplorer` folder.
- **Linux:** run the `.AppImage` as described above.

## Save Files

- **Windows:** saves are stored in the `saves` folder alongside the executable,
  so you can copy the whole `dist/SpaceStationExplorer` folder (saves included)
  to another location or computer.
- **Linux:** because an AppImage is mounted read-only, saves are stored in a
  per-user data directory instead:
  `~/.local/share/SpaceStationExplorer/saves`
  (honouring `$XDG_DATA_HOME` if set).

## Troubleshooting

- If the game doesn't start, try running it from the command line to see any error messages:
  - Open a command prompt in the executable's folder and type `SpaceStationExplorer.exe`

- If you get missing dependency errors during build, manually install them:
  - `pip install matplotlib pyinstaller` 