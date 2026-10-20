@echo off
setlocal
if not exist "%~dp0backend\.venv\Scripts\python.exe" (
    echo Python environment missing. Follow README setup first.
    exit /b 1
)
if not exist "%~dp0frontend\node_modules\.bin\vite.cmd" (
    echo Frontend dependencies missing. Run npm.cmd --prefix frontend ci.
    exit /b 1
)
start "SecScan API" /D "%~dp0backend" cmd.exe /k .venv\Scripts\python.exe app.py
start "SecScan Frontend" /D "%~dp0frontend" cmd.exe /k npm.cmd run dev
echo Servers starting in separate windows. Open http://127.0.0.1:8080/
echo Keep both windows open. Stop each server with Ctrl+C.
