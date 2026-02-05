"""
AI English Teacher - 主应用入口
使用Qwen实时API的智能英语教学系统
"""

import logging

from flask import Flask

from routes.lesson_routes import lesson_routes
from routes.websocket_routes import register_websocket_routes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    """创建和配置Flask应用"""
    app = Flask(__name__)

    # 注册路由蓝图
    app.register_blueprint(lesson_routes)

    # 注册WebSocket路由
    register_websocket_routes(app)

    logger.info("✅ Application configured successfully")
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    logger.info("🚀 Starting AI English Teacher server...")
    logger.info("📚 Visit http://localhost:5000 to start learning")
    app.run(host="0.0.0.0", port=5000, debug=True)
