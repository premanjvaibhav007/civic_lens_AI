@echo off
REM CivicLens AI - Database Backup Utility (Windows)
setlocal enabledelayedexpansion

set BACKUP_DIR=backups
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

set SQLITE_DB=civiclens.db
set BACKUP_FILE=%BACKUP_DIR%\civiclens_sqlite_%TIMESTAMP%.db

if exist "%SQLITE_DB%" (
    echo Backing up %SQLITE_DB% to %BACKUP_FILE%...
    copy /y "%SQLITE_DB%" "%BACKUP_FILE%"
    echo [OK] Backup saved to %BACKUP_FILE%
) else (
    echo [ERROR] Database %SQLITE_DB% not found!
    exit /b 1
)
