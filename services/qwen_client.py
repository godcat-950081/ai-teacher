"""
Qwen Realtime API客户端
处理与Qwen API的WebSocket连接和通信
"""

import asyncio
import json
import logging
import os

import websockets

logger = logging.getLogger(__name__)

# 从环境变量获取配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
REGION = os.getenv("DASHSCOPE_REGION", "beijing")

# API端点配置
API_ENDPOINTS = {
    "beijing": "wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen3-omni-flash-realtime",
    "singapore": "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model=qwen3-omni-flash-realtime",
    "virginia": "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model=qwen3-omni-flash-realtime",
}

QWEN_API_URL = API_ENDPOINTS.get(REGION, API_ENDPOINTS["beijing"])


class QwenRealtimeClient:
    """Qwen-Omni-Realtime WebSocket客户端"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.ws = None
        self.client_ws = None

    async def connect(self):
        """连接到Qwen服务"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            logger.info(f"Connecting to {QWEN_API_URL}...")
            self.ws = await websockets.connect(
                QWEN_API_URL,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
                max_size=10 * 1024 * 1024,
                compression=None,
            )
            logger.info(f"✅ Connected to Qwen API (Region: {REGION})")
            return True
        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"❌ Invalid status code: {e.status_code}")
            if hasattr(e, "headers"):
                logger.error(f"   Response headers: {e.headers}")
            return False
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"❌ WebSocket error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect: {type(e).__name__}: {e}")
            return False

    async def send_session_update(self, config):
        """发送会话配置"""
        session_update = {
            "event_id": f"event_{os.urandom(8).hex()}",
            "type": "session.update",
            "session": config,
        }
        await self.ws.send(json.dumps(session_update))
        logger.info("Session configuration sent")

    async def send_audio(self, audio_base64):
        """发送音频数据"""
        event = {
            "event_id": f"event_{os.urandom(8).hex()}",
            "type": "input_audio_buffer.append",
            "audio": audio_base64,
        }
        await self.ws.send(json.dumps(event))

    async def send_image(self, image_base64):
        """发送图片数据"""
        event = {
            "event_id": f"event_{os.urandom(8).hex()}",
            "type": "input_image_buffer.append",
            "image": image_base64,
        }
        await self.ws.send(json.dumps(event))

    async def send_text_message(self, text):
        """发送文本消息（用于触发AI响应）"""
        event = {
            "event_id": f"event_{os.urandom(8).hex()}",
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}],
            },
        }
        await self.ws.send(json.dumps(event))
        logger.info(f"📤 Sent conversation.item.create with text: {text[:60]}...")

        # 触发响应生成
        response_event = {
            "event_id": f"event_{os.urandom(8).hex()}",
            "type": "response.create",
        }
        await self.ws.send(json.dumps(response_event))
        logger.info("📤 Sent response.create to trigger AI")

    async def commit_audio(self):
        """提交音频缓冲区并触发响应（手动模式）"""
        commit_event = {
            "event_id": f"event_{os.urandom(8).hex()}",
            "type": "input_audio_buffer.commit",
        }
        await self.ws.send(json.dumps(commit_event))
        logger.info("📤 Committed audio buffer")

        response_event = {
            "event_id": f"event_{os.urandom(8).hex()}",
            "type": "response.create",
        }
        await self.ws.send(json.dumps(response_event))
        logger.info("📤 Triggered response.create")

    async def cancel_response(self):
        """取消当前正在进行的响应"""
        event = {
            "event_id": f"event_{os.urandom(8).hex()}",
            "type": "response.cancel",
        }
        await self.ws.send(json.dumps(event))
        logger.info("🛑 Sent response.cancel")

    async def clear_audio_buffer(self):
        """清空输入音频缓冲区"""
        event = {
            "event_id": f"event_{os.urandom(8).hex()}",
            "type": "input_audio_buffer.clear",
        }
        await self.ws.send(json.dumps(event))
        logger.info("🧹 Cleared audio buffer")

    async def send_keepalive(self):
        """发送心跳保持连接活跃"""
        try:
            event = {
                "event_id": f"event_{os.urandom(8).hex()}",
                "type": "session.update",
                "session": {},
            }
            await self.ws.send(json.dumps(event))
            logger.debug("💓 Sent keepalive")
        except Exception as e:
            logger.error(f"Failed to send keepalive: {e}")

    async def handle_qwen_messages(self, client_ws):
        """处理来自Qwen的消息并转发给客户端"""
        try:
            async for message in self.ws:
                data = json.loads(message)
                event_type = data.get("type", "")

                # 记录重要事件
                if event_type not in [
                    "response.audio.delta",
                    "response.text.delta",
                    "response.audio_transcript.delta",
                ]:
                    logger.info(f"📥 Qwen event: {event_type}")

                # 响应事件处理
                if event_type == "response.created":
                    logger.info("🎤 AI response started")
                elif event_type == "response.done":
                    response = data.get("response", {})
                    output = response.get("output", [])
                    logger.info(
                        f"✅ AI response completed - output items: {len(output)}"
                    )

                    # 记录输出内容摘要
                    for idx, item in enumerate(output):
                        content = item.get("content", [])
                        logger.info(f"   Output[{idx}]: {len(content)} content parts")
                        for c in content:
                            c_type = c.get("type", "unknown")
                            if c_type == "audio":
                                transcript = c.get("transcript", "")
                                logger.info(f"     - Audio: {len(transcript)} chars")
                            elif c_type == "text":
                                text_content = c.get("text", "")
                                preview = text_content[:50]
                                logger.info(
                                    f"     - Text: {len(text_content)} chars, preview: {preview}..."
                                )

                elif event_type == "error":
                    error_msg = data.get("error", {})
                    logger.error(f"❌ Qwen API error: {error_msg}")
                elif event_type == "response.audio_transcript.delta":
                    delta = data.get("delta", "")
                    if delta:
                        logger.debug(f"📝 Transcript delta: {delta[:30]}...")
                elif event_type == "response.audio.delta":
                    delta = data.get("delta", "")
                    if delta:
                        logger.debug(f"🔊 Audio delta: {len(delta)} bytes")

                # 转发消息给前端客户端
                try:
                    await client_ws.send(json.dumps(data))
                except Exception as e:
                    logger.error(f"❌ Failed to send to client: {e}")
                    break

        except websockets.exceptions.ConnectionClosedOK:
            logger.info("✅ Qwen connection closed normally")
        except websockets.exceptions.ConnectionClosedError as e:
            if e.code == 1011:
                logger.warning("⚠️ Qwen Response timeout (code 1011)")
            else:
                logger.warning(f"⚠️ Qwen connection closed: {e.code} - {e.reason}")

            # 通知客户端连接已断开
            try:
                error_msg = e.reason if e.reason else "Response timeout"
                await client_ws.send(
                    json.dumps(
                        {
                            "type": "connection_error",
                            "message": f"与Qwen服务的连接已断开: {error_msg}",
                            "code": e.code,
                        }
                    )
                )
            except:
                pass
        except Exception as e:
            logger.error(f"❌ Error handling Qwen messages: {type(e).__name__}: {e}")

    async def close(self):
        """关闭连接"""
        if self.ws:
            await self.ws.close()
            logger.info("Qwen connection closed")
