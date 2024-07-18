#!/bin/bash

# 启动 Docker 容器并获取容器 ID
CONTAINER_ID=$(docker run -d -e PULSAR_URL=pulsar://localhost:6650 -e PORT=8081 --network host youxam/uplion-main:latest)
if [ $? -ne 0 ]; then
    echo "Failed to start Docker container!"
    exit 1
fi

# 定义清理函数
cleanup() {
    echo "Stopping Docker container..."
    docker stop $CONTAINER_ID
    echo "Removing Docker container..."
    docker rm $CONTAINER_ID
    exit 0
}

# 设置 trap 捕捉退出信号 (例如，Ctrl+C, exit 等)
trap cleanup EXIT

检查目录是否存在并运行 Pulsar
if [[ -d ~/apache-pulsar-3.3.0/bin ]]; then
    cd ~/apache-pulsar-3.3.0/bin
    ./pulsar standalone
    PULSAR_PID=$!
else
    echo "Can't find the directory!"
    exit 1
fi