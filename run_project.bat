@echo off
cd /d "C:\Users\neeks\Desktop\project"

start "" cmd /k "python app.py"

timeout /t 3 >nul

start "" http://127.0.0.1:5000