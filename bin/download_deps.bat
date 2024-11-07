@echo off
echo Downloading dependencies...

REM 创建依赖目录
if not exist "packages" mkdir packages
cd packages

REM 下载依赖包
pip download -r ..\requirements.txt

echo Dependencies downloaded successfully!
cd ..
pause