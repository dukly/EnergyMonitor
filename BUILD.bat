@echo off
echo Building the application with Nuitka...
powershell -Command "$env:PYTHONPATH='src'; python -m nuitka --mode=onefile --windows-icon-from-ico=icon.ico --include-package=libraries --include-package=tasks --output-dir=dist --python-flag=-O --jobs=20 src/main.py"
echo Build completed. The executable is located in the 'dist' directory.
