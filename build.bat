@echo off
setlocal enabledelayedexpansion

REM Build with PyInstaller
python -m PyInstaller --onefile --icon=mvsi.ico --add-data "mvsi.ico;." --add-data "steam_api64.dll;." main.py || exit /b 1

REM Check if build succeeded
if not exist dist\main.exe exit /b 1

REM Get date and time in DDMMYYHHMM format
for /f "tokens=1-3 delims=/- " %%a in ("%date%") do (
    set day=%%a
    set month=%%b
    set year=%%c
)
for /f "tokens=1-2 delims=:." %%x in ("%time%") do (
    set hour=%%x
    set minute=%%y
)

REM Pad hour and minute if needed
if 1!hour! LSS 110 set hour=0!hour!
if 1!minute! LSS 110 set minute=0!minute!

set datetime=%day%%month%%year%%hour%%minute%

REM Prepare release folder
mkdir release || exit /b 1
copy dist\main.exe release\ || exit /b 1


mkdir releases
move release\main.exe "releases\MVSI_Backup_tool_%datetime%.exe"

REM Cleanup
rd /s /q build
rd /s /q dist
del main.spec
rd /s /q release
