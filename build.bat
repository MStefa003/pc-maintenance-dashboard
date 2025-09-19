@echo off
echo Building PC Maintenance Dashboard...

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Build executable
echo Building executable...
pyinstaller --onefile --windowed --name "PC_Maintenance_Dashboard" main.py

REM Alternative build with spec file
REM pyinstaller build.spec

echo Build complete! Check the 'dist' folder for the executable.
pause
