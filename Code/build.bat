@echo off
echo Building Space Station Explorer...
python build_exe.py %*
echo.
echo If successful, the executable is dist\SpaceStationExplorer.exe
echo (saves stay in dist\saves\ — keep _internal next to the EXE)
echo Press any key to exit...
pause > nul
