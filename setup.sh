#!/bin/bash

# Qwen-Omni-Realtime 快速配置脚本

echo "===================================="
echo "  Qwen-Omni-Realtime 配置向导"
echo "===================================="
echo ""

# 检查虚拟环境
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "❌ 错误：未找到虚拟环境 venv/ 或 .venv/"
    echo "   请先创建虚拟环境：python -m venv venv"
    exit 1
fi

echo "1. 请选择你的地理位置："
echo "   1) 中国大陆 (北京)"
echo "   2) 国际/海外 (新加坡)"
echo "   3) 国际/海外 (弗吉尼亚)"
echo ""
read -p "请输入选项 (1/2/3): " region_choice

case $region_choice in
    1)
        REGION="beijing"
        REGION_NAME="北京"
        API_CONSOLE="https://bailian.console.aliyun.com/?tab=model#/api-key"
        ;;
    2)
        REGION="singapore"
        REGION_NAME="新加坡"
        API_CONSOLE="https://bailian.console.aliyun.com/?tab=model#/api-key"
        ;;
    3)
        REGION="virginia"
        REGION_NAME="弗吉尼亚"
        API_CONSOLE="https://bailian.console.aliyun.com/?tab=model#/api-key"
        ;;
    *)
        echo "❌ 无效的选项"
        exit 1
        ;;
esac

echo ""
echo "✅ 已选择区域：$REGION_NAME"
echo ""
echo "2. 请输入你的 DASHSCOPE_API_KEY："
echo "   获取地址：$API_CONSOLE"
echo ""
read -p "API Key: " api_key

if [ -z "$api_key" ]; then
    echo "❌ API Key 不能为空"
    exit 1
fi

# 创建 .env 文件
echo "# Qwen-Omni-Realtime 配置" > .env
echo "# 生成时间: $(date)" >> .env
echo "" >> .env
echo "DASHSCOPE_API_KEY=$api_key" >> .env
echo "DASHSCOPE_REGION=$REGION" >> .env
echo "" >> .env
echo "FLASK_ENV=development" >> .env
echo "FLASK_DEBUG=True" >> .env

echo ""
echo "===================================="
echo "  ✅ 配置完成！"
echo "===================================="
echo ""
echo "配置信息："
echo "  区域: $REGION_NAME"
echo "  API Key: ${api_key:0:20}..."
echo ""
echo "下一步："
echo "  1. 激活虚拟环境: source .venv/bin/activate"
echo "  2. 安装依赖: pip install -r requirements.txt"
echo "  3. 启动服务: python app.py"
echo ""
