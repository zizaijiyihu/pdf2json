#!/bin/bash

# KM Agent 项目启动脚本
# 自动启动后端 API 服务和前端 UI 服务

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== KM Agent 启动脚本 ===${NC}\n"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3，请先安装 Python 3${NC}"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到 Node.js，请先安装 Node.js${NC}"
    exit 1
fi

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}错误: 未找到 npm，请先安装 npm${NC}"
    exit 1
fi

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}项目目录: ${PROJECT_ROOT}${NC}\n"

# 激活 Python 虚拟环境
VENV_PATH="${VENV_PATH:-$HOME/projects/venv}"
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
    echo -e "${GREEN}✓ 已激活虚拟环境: $VENV_PATH${NC}"
    echo -e "  Python: $(which python)"
    echo -e "  Pip: $(which pip)\n"
else
    echo -e "${RED}错误: 未找到虚拟环境 $VENV_PATH${NC}"
    echo -e "${RED}请先创建虚拟环境或通过 VENV_PATH=/your/venv/path ./start.sh 指定${NC}"
    exit 1
fi

# 1. 检查 Python 依赖
echo -e "${BLUE}[1/4] 检查 Python 依赖...${NC}"
if [ -f "requirements.txt" ]; then
    "$VENV_PATH/bin/pip" install -r requirements.txt
    echo -e "${GREEN}✓ Python 依赖已安装${NC}\n"
else
    echo -e "${RED}警告: 未找到 requirements.txt${NC}\n"
fi

# 2. 检查前端依赖
echo -e "${BLUE}[2/4] 检查前端依赖...${NC}"
if [ -d "ui" ]; then
    cd ui
    if [ ! -d "node_modules" ]; then
        echo "首次运行，安装前端依赖..."
        npm install
    fi
    cd ..
    echo -e "${GREEN}✓ 前端依赖已就绪${NC}\n"
else
    echo -e "${RED}警告: 未找到 ui 目录${NC}\n"
fi

# 3. 启动后端 API 服务
echo -e "${BLUE}[3/4] 启动后端 API 服务 (端口 5000)...${NC}"
python3 -u -m app_api.api 2>&1 | tee /tmp/km_agent_api.log &
API_PID=$!
echo -e "${GREEN}✓ 后端服务已启动 (PID: $API_PID)${NC}"
echo -e "  日志文件: /tmp/km_agent_api.log\n"

# 等待后端服务启动
echo "等待后端服务就绪..."
for i in {1..30}; do
    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务就绪${NC}\n"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}错误: 后端服务启动超时${NC}"
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# 4. 启动前端 UI 服务
echo -e "${BLUE}[4/4] 启动前端 UI 服务 (端口 8080)...${NC}"
cd ui
npm run dev > /tmp/km_agent_ui.log 2>&1 &
UI_PID=$!
cd ..
echo -e "${GREEN}✓ 前端服务已启动 (PID: $UI_PID)${NC}"
echo -e "  日志文件: /tmp/km_agent_ui.log\n"

# 等待前端服务启动
echo "等待前端服务就绪..."
sleep 3

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   KM Agent 已成功启动！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  后端 API: ${BLUE}http://localhost:5000${NC}"
echo -e "  前端 UI:  ${BLUE}http://localhost:8080${NC}"
echo ""
echo -e "  后端 PID: ${API_PID}"
echo -e "  前端 PID: ${UI_PID}"
echo ""
echo -e "  停止服务: kill $API_PID $UI_PID"
echo -e "  或者运行: ./stop.sh"
echo ""
echo -e "${BLUE}提示: 浏览器访问 http://localhost:8080 开始使用${NC}"
echo ""

# 保存 PID 到文件
echo "$API_PID" > /tmp/km_agent_api.pid
echo "$UI_PID" > /tmp/km_agent_ui.pid

# 等待用户中断
echo -e "按 Ctrl+C 停止所有服务..."
trap "echo -e '\n${BLUE}正在停止服务...${NC}'; kill $API_PID $UI_PID 2>/dev/null || true; rm -f /tmp/km_agent_*.pid; echo -e '${GREEN}服务已停止${NC}'; exit 0" INT

# 保持脚本运行
wait
