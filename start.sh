#!/bin/bash

# 启动流转卡系统

echo "=========================================="
echo "启动流转卡系统..."
echo "=========================================="

# 检查MySQL服务
echo "检查MySQL服务..."
if ! command -v mysql &> /dev/null; then
    echo "错误: MySQL未安装"
    exit 1
fi

# 启动后端
echo ""
echo "启动后端服务..."
cd backend
python app.py &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)"
echo "后端地址: http://localhost:5000"

# 等待后端启动
sleep 3

# 测试后端连接
echo "测试后端连接..."
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务启动失败"
    exit 1
fi

# 启动前端
echo ""
echo "启动前端服务..."
cd ../frontend
npm start &
FRONTEND_PID=$!
echo "前端服务已启动 (PID: $FRONTEND_PID)"
echo "前端地址: http://localhost:8080 或 http://服务器IP:8080"

echo ""
echo "=========================================="
echo "系统启动完成！"
echo "=========================================="
echo "前端: http://localhost:8080 (本地) 或 http://服务器IP:8080 (外部)"
echo "后端: http://localhost:5000"
echo "后端健康检查: http://localhost:5000/health"
echo ""
echo "本地访问: 请在浏览器中访问 http://localhost:8080"
echo "外部访问: 请在浏览器中访问 http://服务器IP:8080"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "=========================================="

# 等待所有进程
wait $BACKEND_PID $FRONTEND_PID
