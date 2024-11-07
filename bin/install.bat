@echo off
echo Installing dependencies...

REM 检查Python和pip是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    exit /b 1
)

pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is not installed
    exit /b 1
)

REM 创建并激活虚拟环境
python -m venv venv
call venv\Scripts\activate

REM 更新pip
python -m pip install --upgrade pip

REM 安装依赖
pip install -r requirements.txt

echo Installation completed successfully!
pause