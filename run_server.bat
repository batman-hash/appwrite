@echo off
setlocal

echo ===========================================
echo  CYBERGHOST Web App (Flask)
echo ===========================================

cd /d "%~dp0"

if exist "myenv\Scripts\activate.bat" (
    call "myenv\Scripts\activate.bat"
)

set HOST=127.0.0.1
set PORT=8011
set BASE_URL=http://127.0.0.1:8011
set PUBLIC_BASE_URL=%BASE_URL%
set STATIC_BASE_URL=%BASE_URL%
set CORS_ORIGINS=http://localhost:8011,http://127.0.0.1:8011
set SINGLE_INSTANCE=true
set PROJECT_SINGLE_INSTANCE=true

set PID_FILE=backend\webapp.pid
set PROJECT_PID_FILE=project.pid
set APP_RUNNING=
set PROJECT_RUNNING=

if exist "%PID_FILE%" (
    set /p APP_PID=<"%PID_FILE%"
    if not "%APP_PID%"=="" (
        tasklist /fi "PID eq %APP_PID%" | findstr /i "%APP_PID%" >nul
        if not errorlevel 1 (
            set APP_RUNNING=1
        )
    )
)

if exist "%PROJECT_PID_FILE%" (
    set /p PROJECT_PID=<"%PROJECT_PID_FILE%"
    if not "%PROJECT_PID%"=="" (
        tasklist /fi "PID eq %PROJECT_PID%" | findstr /i "%PROJECT_PID%" >nul
        if not errorlevel 1 (
            set PROJECT_RUNNING=1
        )
    )
)

if defined APP_RUNNING (
    echo App already running (PID %APP_PID%). Opening browser only.
    start "" %BASE_URL%/index.html
    goto :eof
)

if defined PROJECT_RUNNING (
    echo Another project process is running (PID %PROJECT_PID%).
    echo Stop it first, then run this launcher again.
    goto :eof
)

start "CYBERGHOST Flask" cmd /k "python backend\webapp.py --host %HOST% --port %PORT%"
timeout /t 2 >nul
start "" %BASE_URL%/index.html
