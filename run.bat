@echo off
:: Set terminal to UTF-8 to handle special characters (Japanese, accents, etc.)
chcp 65001 >nul

:: Activate the virtual environment
call .venv\Scripts\activate

:: Update dependencies from requirements.txt (forces latest yt-dlp and fork)
echo [INFO] Updating dependencies...
pip install -q --upgrade -r requirements.txt

:: Run the downloader
python main.py

:: Keep the window open if the script finishes or crashes
pause
