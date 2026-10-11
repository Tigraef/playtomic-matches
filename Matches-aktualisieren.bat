@echo off
chcp 65001 >nul
rem Holt neue Playtomic-Matches und öffnet Ordner + GitHub-Upload-Seite.
rem Muss im Projektordner liegen (neben README.md).
cd /d "%~dp0"
echo Hole Matches von Playtomic ...
echo.
py scripts\fetch_matches.py
if errorlevel 1 (
    echo.
    echo Fehler beim Abruf. Bitte die Ausgabe oben an Claude schicken.
    pause
    exit /b 1
)
echo.
echo Fertig. Jetzt data\matches.json ins Browserfenster ziehen und "Commit changes" klicken.
start "" explorer "%~dp0data"
start "" "https://github.com/Tigraef/playtomic-matches/upload/main/data"
pause
