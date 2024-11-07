#!/bin/bash

echo "Downloading dependencies..."

# 创建依赖目录
mkdir -p packages
cd packages

# 下载依赖包
pip download -r ../requirements.txt

echo "Dependencies downloaded successfully!"
cd ..