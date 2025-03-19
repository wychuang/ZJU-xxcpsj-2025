@echo off
chcp 65001 >nul
echo 启动全自动语音交互助手...

:: 设置项目根目录（向上两级目录）
cd /d "%~dp0..\.."

:: 激活虚拟环境
if exist .venv\Scripts\activate.bat (
    echo 激活虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo 警告: 未找到虚拟环境
)

:: 运行主程序
python "%~dp0voice_assistant_auto.py"

:: 退出虚拟环境
if exist .venv\Scripts\deactivate.bat (
    call .venv\Scripts\deactivate.bat
)

pause
