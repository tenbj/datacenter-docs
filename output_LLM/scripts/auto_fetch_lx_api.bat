@echo off
chcp 65001 > nul
echo ================================================
echo 领星API文档自动更新脚本
echo 运行时间: %date% %time%
echo ================================================

REM 切换到脚本目录
cd /d "%~dp0"

REM 运行Python脚本
python auto_fetch_lx_api.py

REM 检查执行结果
if %errorlevel% neq 0 (
    echo.
    echo [错误] 脚本执行失败！错误码: %errorlevel%
    pause
    exit /b %errorlevel%
)

echo.
echo [成功] 脚本执行完成！
echo ================================================

REM 如果是手动运行，暂停显示结果
if "%1"=="" pause
