@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   ZoneShot - 打包成單一 exe
echo ============================================
echo.

echo [1/3] 安裝依賴...
pip install -r requirements.txt -q
pip install pyinstaller -q
if errorlevel 1 (
    echo 依賴安裝失敗，請檢查 Python 與 pip。
    pause
    exit /b 1
)

echo [2/3] 打包（單一 exe，輸出：dist\ZoneShot.exe）...
echo 若出現「存取被拒」，請關閉本程式後，在「命令提示字元」中重新執行此 bat。
echo.
pyinstaller --noconfirm build_exe.spec
if errorlevel 1 (
    echo.
    echo 打包失敗。若為「存取被拒」或 WinError 5：
    echo   - 請在「命令提示字元」或 PowerShell 中手動執行此 bat（不要從 Cursor 執行）
    echo   - 或暫時將此資料夾排除於防毒即時掃描之外
    pause
    exit /b 1
)

echo [3/3] 完成。
echo.
echo 可執行檔位置： %~dp0dist\ZoneShot.exe
echo 可直接複製該 exe 到任何電腦執行，無需安裝 Python。
echo.
pause
