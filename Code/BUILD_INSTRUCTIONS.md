# Space Station Explorer - Build Instructions

This document explains how to build and run the Space Station Explorer game as a standalone executable.

## Prerequisites

- Python 3.6 or higher
- Required packages from `requirements.txt`:
  - matplotlib (also pulls in Pillow, used to convert the shared icon for Windows)
  - PyInstaller (the Windows build script will install this automatically if missing)

## Building the Executable

### Windows

1. Double-click on the `build.bat` file (or run `build.bat` from a command prompt).
2. Wait for the build process to complete.
3. The executable will be created at `dist/SpaceStationExplorer.exe`, with a
   `_internal` folder beside it. Keep those together. Saves continue to live in
   `dist/saves/` (same place as older one-file builds), so existing save files
   keep working.

For a full rebuild that clears PyInstaller's cache:

```bat
build.bat --clean
```

The Windows EXE icon is generated at build time from the same image the Linux
AppImage uses: `packaging/linux/space_station_icon.png`.

### Manual Build (Windows)

You can also manually build the executable:

1. Install required packages: `pip install -r requirements.txt`
2. Run the build script: `python build_exe.py`
3. Optional full rebuild: `python build_exe.py --clean`

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

- **Windows:** double-click `SpaceStationExplorer.exe` in the `dist` folder
  (keep `_internal` next to it).
- **Linux:** run the `.AppImage` as described above.

## Save Files

- **Windows:** saves are stored in `dist/saves/` alongside the executable,
  so you can copy the whole `dist` folder (EXE, `_internal`, and `saves`)
  to another location or computer. Existing saves from previous builds in
  that folder are reused automatically.
- **Linux:** because an AppImage is mounted read-only, saves are stored in a
  per-user data directory instead:
  `~/.local/share/SpaceStationExplorer/saves`
  (honouring `$XDG_DATA_HOME` if set).

## Troubleshooting

- If the game doesn't start, try running it from the command line to see any error messages:
  - Open a command prompt in the executable's folder and type `SpaceStationExplorer.exe`

- If you get missing dependency errors during build, manually install them:
  - `pip install -r requirements.txt`
