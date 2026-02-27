@echo off
echo Building EnergyMonitor with Nuitka...

cd /d %~dp0

py -3.12 -m nuitka ^
    --onefile ^
    --standalone ^
    --include-package=libraries ^
    --include-data-file=.env=.env ^
    --include-data-file=energymonitor.sqlite=energymonitor.sqlite ^
    --output-dir=. ^
    --python-flag=-O ^
    --jobs=8 ^
    src/main.py

echo.
echo ============================================
echo СБОРКА 
echo EXE лежит прямо в папке EnergyMonitor
echo ============================================
pause
