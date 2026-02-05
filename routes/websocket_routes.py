"""
WebSocket路由
处理实时音频和消息通信
"""

import asyncio
import base64
import json
import logging
from datetime import datetime

from flask import Blueprint
from flask_sock import Sock

from handlers.stage_handler import get_system_prompt, handle_stage_switch
from lesson_manager import LessonStatus
from routes.lesson_routes import get_lesson_from_storage, get_lesson_plan_from_storage
from services.qwen_client import QwenRealtimeClient

logger = logging.getLogger(__name__)

# Sock实例将在register_websocket_routes中初始化
sock = None


def tutor_websocket_handler(ws, lesson_id):
    """教学WebSocket连接处理"""
    logger.info(f"🔌 WebSocket connected for lesson: {lesson_id}")

    lesson = get_lesson_from_storage(lesson_id)
    if not lesson:
        ws.send(json.dumps({"type": "error", "message": "Lesson not found"}))
        return

    plan = get_lesson_plan_from_storage(lesson_id)
    if not plan:
        ws.send(json.dumps({"type": "error", "message": "Lesson plan not found"}))
        return

    # 更新课程状态
    if lesson.status == LessonStatus.PREPARED:
        lesson.status = LessonStatus.IN_PROGRESS
        lesson.started_at = datetime.now().isoformat()
        logger.info(f"▶️  Lesson started: {lesson_id}")

    # 创建Qwen客户端
    qwen_ws = QwenRealtimeClient()
    message_handler_task = None

    try:
        # 运行异步处理
        asyncio.run(handle_websocket_session(ws, lesson, plan, qwen_ws))
    except Exception as e:
        logger.error(f"❌ WebSocket error: {str(e)}", exc_info=True)
        try:
            ws.send(json.dumps({"type": "error", "message": str(e)}))
        except:
            pass
    finally:
        # 清理资源
        if qwen_ws.ws:
            try:
                asyncio.run(qwen_ws.close())
            except:
                pass
        logger.info(f"🔌 WebSocket disconnected: {lesson_id}")


async def handle_websocket_session(client_ws, lesson, plan, qwen_ws):
    """处理WebSocket会话的异步逻辑"""
    message_handler_task = None

    try:
        # 1. 连接到Qwen API
        logger.info("🔗 Connecting to Qwen API...")
        await qwen_ws.connect()
        logger.info("✅ Connected to Qwen API")

        # 2. 配置会话
        system_prompt = get_system_prompt()
        session_config = {
            "voice": "longxiaochun",
            "language": "en",
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "sample_rate": 16000,
            "output_sample_rate": 24000,
            "system_prompt": system_prompt,
            "vad": {
                "silence_duration_ms": 1500,  # 1.5秒静音判断
                "silence_threshold": 0.3,
                "speaking_threshold": 0.6,
            },
        }
        await qwen_ws.send_session_update(session_config)
        logger.info("✅ Session configured with 1500ms silence detection")

        # 3. 启动消息处理任务
        message_handler_task = asyncio.create_task(
            qwen_ws.handle_qwen_messages(client_ws)
        )
        logger.info("✅ Message handler started")

        # 4. 发送初始提示词（开始单词教学）
        initial_prompt = plan.get_stage_prompt("vocabulary")
        await qwen_ws.send_text_message(initial_prompt)
        logger.info(f"✅ Initial prompt sent: {initial_prompt[:100]}...")

        # 5. 处理客户端消息
        while True:
            try:
                # 从客户端接收消息
                message_raw = client_ws.receive(timeout=30)
                if not message_raw:
                    logger.info("❌ Client disconnected (empty message)")
                    break

                message = json.loads(message_raw)
                msg_type = message.get("type")

                # 处理音频数据
                if msg_type == "audio":
                    audio_b64 = message.get("audio")
                    if audio_b64:
                        audio_data = base64.b64decode(audio_b64)
                        await qwen_ws.send_audio(audio_data)

                # 处理提交音频（用户停止说话）
                elif msg_type == "commit_audio":
                    await qwen_ws.commit_audio()
                    logger.info("✅ Audio committed")

                # 处理阶段切换
                elif msg_type == "switch_stage":
                    stage = message.get("stage")
                    logger.info(f"🔄 Stage switch request: {stage}")
                    await handle_stage_switch(qwen_ws, stage, plan, client_ws)

                # 处理取消响应
                elif msg_type == "cancel_response":
                    await qwen_ws.cancel_response()
                    logger.info("✅ Response cancelled by user")

                # 处理结束课程
                elif msg_type == "end_lesson":
                    logger.info("🏁 Ending lesson...")
                    lesson.status = LessonStatus.COMPLETED
                    lesson.ended_at = datetime.now().isoformat()
                    await client_ws.send(
                        json.dumps({"type": "lesson_ended", "message": "Lesson ended"})
                    )
                    break

            except TimeoutError:
                # 发送保活消息
                await qwen_ws.send_keepalive()
                continue
            except Exception as e:
                logger.error(f"❌ Error processing message: {str(e)}", exc_info=True)
                break

    except Exception as e:
        logger.error(f"❌ Session error: {str(e)}", exc_info=True)
        await client_ws.send(json.dumps({"type": "error", "message": str(e)}))
    finally:
        # 取消消息处理任务
        if message_handler_task and not message_handler_task.done():
            message_handler_task.cancel()
            try:
                await message_handler_task
            except asyncio.CancelledError:
                pass

        # 关闭Qwen连接
        await qwen_ws.close()
        logger.info("✅ Session cleaned up")


def register_websocket_routes(app):
    """注册WebSocket路由到应用"""
    global sock
    from flask_sock import Sock

    sock = Sock(app)

    # 注册WebSocket路由
    sock.route("/ws/tutor/<lesson_id>")(tutor_websocket_handler)

    logger.info("✅ WebSocket routes registered")
