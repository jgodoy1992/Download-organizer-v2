@echo off
cd /D "%~d0"
echo Running virtual environment ...
call venv\Scripts\activate
echo Running python Script
python main.py
pause