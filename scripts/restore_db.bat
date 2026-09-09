@echo off
REM CivicLens AI - Database Restore Utility (Windows)
setlocal

if "%~1"=="" (
    echo Usage: restore_db.bat ^<path_to_backup_file.db^>
    exit /b 1
)

set BACKUP_FILE=%~1
set TARGET_DB=civiclens.db

if not exist "%BACKUP_FILE%" (
    echo [ERROR] Backup file %BACKUP_FILE% does not exist!
    exit /b 1
)

if exist "%TARGET_DB%" (
    echo Creating safety backup of current %TARGET_DB% to %TARGET_DB%.bak...
    copy /y "%TARGET_DB%" "%TARGET_DB%.bak"
)

echo Restoring %BACKUP_FILE% to %TARGET_DB%...
copy /y "%BACKUP_FILE%" "%TARGET_DB%"
echo [OK] Database restored successfully.
