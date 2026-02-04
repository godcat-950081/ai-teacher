#!/bin/bash

# 快速切换到新加坡区域

echo "🔄 正在切换到新加坡区域..."
echo ""

# 检查 .env 文件
if [ -f ".env" ]; then
    # 更新 .env 文件
    if grep -q "DASHSCOPE_REGION" .env; then
        sed -i 's/DASHSCOPE_REGION=.*/DASHSCOPE_REGION=singapore/' .env
        echo "✅ 已更新 .env 文件中的区域设置"
    else
        echo "DASHSCOPE_REGION=singapore" >> .env
        echo "✅ 已添加区域设置到 .env 文件"
    fi
else
    echo "⚠️  未找到 .env 文件"
fi

# 设置当前会话的环境变量
export DASHSCOPE_REGION=singapore

echo ""
echo "✅ 区域已切换到：SINGAPORE (新加坡)"
echo ""
echo "当前会话已生效，请重启服务："
echo "  python app.py"
echo ""
