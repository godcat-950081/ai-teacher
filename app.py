"""
Qwen-Omni-Realtime Demo Server
基于Flask和WebSocket的实时音视频聊天服务
"""

import asyncio
import base64
import json
import logging
import os
import re

import websockets
from flask import Flask, jsonify, render_template, request
from flask_sock import Sock

# 导入课程管理器
from lesson_manager import LessonPlan, LessonStatus, lesson_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
sock = Sock(app)

# 从环境变量获取API Key和区域配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
REGION = os.getenv("DASHSCOPE_REGION", "beijing")  # beijing, singapore, virginia

if not DASHSCOPE_API_KEY:
    logger.warning("DASHSCOPE_API_KEY not set in environment variables")

# Qwen-Omni-Realtime API配置（根据区域选择）
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
                ping_interval=20,  # 更频繁的心跳检测
                ping_timeout=10,
                close_timeout=10,
                max_size=10 * 1024 * 1024,  # 10MB 最大消息大小
                compression=None,  # 禁用压缩以提高稳定性
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

        # 触发响应生成
        response_event = {
            "event_id": f"event_{os.urandom(8).hex()}",
            "type": "response.create",
        }
        await self.ws.send(json.dumps(response_event))

    async def commit_audio(self):
        """提交音频缓冲区并触发响应（手动模式）"""
        # 1. 提交音频缓冲区
        commit_event = {
            "event_id": f"event_{os.urandom(8).hex()}",
            "type": "input_audio_buffer.commit",
        }
        await self.ws.send(json.dumps(commit_event))
        logger.info("📤 Committed audio buffer")

        # 2. 触发响应生成
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

    async def send_keepalive(self):
        """发送心跳保持连接活跃（防止长时间无响应导致超时）"""
        try:
            # 发送一个空的会话更新作为心跳
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

                # 只记录重要事件，减少日志噪音
                if event_type not in [
                    "response.audio.delta",
                    "response.text.delta",
                    "response.audio_transcript.delta",
                ]:
                    logger.info(f"📥 Qwen event: {event_type}")

                # 转发消息给前端客户端
                try:
                    await client_ws.send(json.dumps(data))
                except Exception as e:
                    logger.error(f"❌ Failed to send to client: {e}")
                    break

        except websockets.exceptions.ConnectionClosedOK:
            logger.info("✅ Qwen connection closed normally")
        except websockets.exceptions.ConnectionClosedError as e:
            # 1011 是 Response timeout 错误
            if e.code == 1011:
                logger.warning(
                    f"⚠️ Qwen Response timeout (code 1011), connection will be closed"
                )
            else:
                logger.warning(
                    f"⚠️ Qwen connection closed with error: {e.code} - {e.reason}"
                )
            # 通知客户端连接已断开
            try:
                await client_ws.send(
                    json.dumps(
                        {
                            "type": "connection_error",
                            "message": f"与Qwen服务的连接已断开: {e.reason if e.reason else 'Response timeout'}",
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


@app.route("/")
def index():
    """渲染主页 - 基础示例"""
    return render_template("index.html")


@app.route("/tutor")
def tutor_page():
    """AI英语外教页面"""
    return render_template("tutor.html")


@app.route("/health")
def health():
    """健康检查"""
    return jsonify(
        {
            "status": "ok",
            "api_configured": bool(DASHSCOPE_API_KEY),
            "region": REGION,
            "api_endpoint": QWEN_API_URL,
        }
    )


# ============= AI English Tutor API =============


@app.route("/api/lessons", methods=["POST"])
def create_lesson():
    """创建新课程"""
    try:
        data = request.json
        text_input = data.get("text", "")
        images = data.get("images", [])  # base64 编码的图片列表

        logger.info(
            f"📝 Creating lesson with text: '{text_input}', images: {len(images)}"
        )

        lesson_id = lesson_manager.create_lesson(text_input, images)

        return jsonify(
            {
                "success": True,
                "lesson_id": lesson_id,
                "message": "Lesson created successfully",
            }
        )
    except Exception as e:
        logger.error(f"Error creating lesson: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/lessons/<lesson_id>", methods=["GET"])
def get_lesson(lesson_id):
    """获取课程信息"""
    lesson = lesson_manager.get_lesson(lesson_id)
    if not lesson:
        return jsonify({"success": False, "error": "Lesson not found"}), 404

    return jsonify({"success": True, "lesson": lesson.to_dict()})


def extract_lesson_info(text):
    """从用户输入中提取课程信息"""
    text_lower = text.lower() if text else ""

    # 检测是否包含结构化内容
    has_vocabulary = (
        "单词" in text or "vocabulary" in text_lower or "words:" in text_lower
    )
    has_article = (
        "文章" in text
        or "article" in text_lower
        or "passage" in text_lower
        or "text:" in text_lower
    )
    has_questions = "练习" in text or "questions" in text_lower or "?" in text

    # 如果有结构化内容，提取主题
    if has_vocabulary or has_article:
        # 尝试从文章中提取主题
        if "Micronesia" in text:
            return "Communication and Body Language"
        elif "India" in text:
            return "Cross-Cultural Communication"

    # 检测主题关键词
    topics_map = {
        "greeting": "Greetings and Introductions",
        "introduction": "Greetings and Introductions",
        "email": "Business Email Writing",
        "business": "Business English Communication",
        "restaurant": "Restaurant and Food Ordering",
        "food": "Food and Dining Vocabulary",
        "travel": "Travel English",
        "shopping": "Shopping Conversations",
    }

    for keyword, topic_name in topics_map.items():
        if keyword in text_lower:
            return topic_name

    # 默认主题
    return "English Practice"


def parse_structured_lesson(text):
    """解析结构化的课程内容（单词、文章、练习）"""
    result = {"vocabulary": [], "articles": [], "questions": []}

    # 分割文本
    sections = text.split("\n")
    current_section = None
    article_lines = []

    for line in sections:
        line = line.strip()
        if not line:
            continue

        # 识别章节标题
        if "单词" in line or "vocabulary" in line.lower():
            current_section = "vocabulary"
            if article_lines:
                result["articles"].append("\n".join(article_lines))
                article_lines = []
            continue
        elif "文章" in line or "article" in line.lower() or "passage" in line.lower():
            current_section = "article"
            continue
        elif (
            "练习" in line or "questions" in line.lower() or "exercise" in line.lower()
        ):
            if article_lines:
                result["articles"].append("\n".join(article_lines))
                article_lines = []
            current_section = "questions"
            continue

        # 提取内容
        if current_section == "vocabulary":
            # 提取单词（可能用逗号或顿号分隔）
            words = line.replace("，", ",").split(",")
            for word in words:
                word = word.strip()
                if word and not word.endswith(":") and not word.endswith("："):
                    result["vocabulary"].append(word)
        elif current_section == "article":
            article_lines.append(line)
        elif current_section == "questions":
            if "?" in line:
                # 清理序号
                question = line.lstrip("0123456789. ")
                result["questions"].append(question)

    # 添加最后收集的文章
    if article_lines:
        result["articles"].append("\n".join(article_lines))

    return result


@app.route("/api/lessons/<lesson_id>/prepare", methods=["POST"])
def prepare_lesson(lesson_id):
    """准备课程（生成课程计划）- 基于用户输入创建结构化教学计划"""
    lesson = lesson_manager.get_lesson(lesson_id)
    if not lesson:
        return jsonify({"success": False, "error": "Lesson not found"}), 404

    try:
        logger.info(
            f"📚 Preparing lesson {lesson_id}, user_input: '{lesson.user_input_text[:100] if lesson.user_input_text else 'None'}...', has_images: {len(lesson.user_input_images) > 0}"
        )

        # 基于用户输入创建结构化课程计划（不调用外部AI API）
        user_text = lesson.user_input_text or "General English conversation practice"

        # 解析结构化内容
        parsed = parse_structured_lesson(user_text)

        # 提取主题
        topic = extract_lesson_info(user_text)

        # 构建课程大纲和练习
        objectives = []
        outline = []
        exercises = []
        vocabulary = (
            parsed["vocabulary"]
            if parsed["vocabulary"]
            else ["practice", "learn", "improve"]
        )

        # 根据解析的内容创建课程结构
        if parsed["vocabulary"]:
            objectives.append(f"Learn {len(parsed['vocabulary'])} new vocabulary words")
            outline.append(
                "Step 1: Vocabulary - Teach each word with meaning, practice 2-3 times"
            )
            exercises.append(
                {
                    "type": "vocabulary",
                    "content": ", ".join(parsed["vocabulary"][:15]),  # 最多15个单词
                }
            )

        if parsed["articles"]:
            objectives.append("Read and understand the article")
            outline.append(
                "Step 2: Article - Teacher reads first, then student reads, answer questions"
            )
            for i, article in enumerate(parsed["articles"][:2], 1):  # 最多2篇文章
                exercises.append(
                    {"type": "reading", "content": article}  # 完整文章内容
                )

        if parsed["questions"]:
            objectives.append("Answer questions about the content")
            outline.append(
                "Step 3: Questions - Student ANSWERS each question (not just repeat)"
            )
            for q in parsed["questions"][:5]:  # 最多5个问题
                exercises.append(
                    {"type": "question", "content": q}  # 改为question类型而不是speaking
                )

        # 添加总结步骤
        outline.append("Step 4: Review - Summarize key points and final Q&A")

        # 如果没有解析到结构化内容，使用通用结构
        if not objectives:
            objectives = [
                "Learn key vocabulary",
                "Practice pronunciation",
                "Improve fluency",
            ]
            outline = [
                "Warm-up and introduction",
                "Vocabulary learning",
                "Practice and conversation",
                "Review and summary",
            ]
            exercises = [{"type": "speaking", "content": "General practice"}]

        # 估算时长（可以从用户输入中提取，如果没有则默认20分钟）
        duration = 20
        duration_match = re.search(
            r"(\d+)\s*分钟|(\d+)\s*minutes?", user_text, re.IGNORECASE
        )
        if duration_match:
            duration = int(duration_match.group(1) or duration_match.group(2))

        # 创建课程计划
        plan = LessonPlan(
            lesson_id=lesson_id,
            topic=topic,
            objectives=objectives,
            outline=outline,
            exercises=exercises,
            vocabulary=vocabulary[:10],  # 最多10个单词
            estimated_duration=duration,
            created_at=lesson.created_at,
        )

        lesson_manager.update_lesson_plan(lesson_id, plan)

        logger.info(
            f"✅ Lesson plan created: {topic} ({len(vocabulary)} words, {len(parsed['articles'])} articles, {len(parsed['questions'])} questions)"
        )
        return jsonify({"success": True, "lesson_plan": plan.to_dict()})

    except Exception as e:
        logger.error(f"Error preparing lesson: {e}, using fallback")
        # 使用默认课程计划作为后备
        plan = LessonPlan(
            lesson_id=lesson_id,
            topic="Daily Conversation Practice",
            objectives=[
                "Practice greeting and introductions",
                "Learn common daily phrases",
                "Improve pronunciation and fluency",
            ],
            outline=[
                "1. Warm-up: Greetings",
                "2. Vocabulary: Common phrases",
                "3. Practice: Role-play conversations",
                "4. Pronunciation exercises",
                "5. Summary and feedback",
            ],
            exercises=[
                {"type": "reading", "content": "Hello, how are you today?"},
                {"type": "speaking", "content": "Introduce yourself"},
                {"type": "listening", "content": "Listen and repeat"},
            ],
            vocabulary=["hello", "goodbye", "thank you", "please", "excuse me"],
            estimated_duration=20,
            created_at=lesson.created_at,
        )

        lesson_manager.update_lesson_plan(lesson_id, plan)

        return jsonify({"success": True, "lesson_plan": plan.to_dict()})
    except Exception as e:
        logger.error(f"Error preparing lesson: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/lessons/<lesson_id>/start", methods=["POST"])
def start_lesson(lesson_id):
    """开始课程"""
    lesson = lesson_manager.get_lesson(lesson_id)
    if not lesson:
        return jsonify({"success": False, "error": "Lesson not found"}), 404

    if lesson.status != LessonStatus.READY:
        return jsonify({"success": False, "error": "Lesson is not ready to start"}), 400

    lesson_manager.start_lesson(lesson_id)

    return jsonify({"success": True, "message": "Lesson started"})


@app.route("/api/lessons/<lesson_id>/complete", methods=["POST"])
def complete_lesson(lesson_id):
    """完成课程"""
    lesson = lesson_manager.get_lesson(lesson_id)
    if not lesson:
        return jsonify({"success": False, "error": "Lesson not found"}), 404

    data = request.json
    summary = data.get("summary", "")

    lesson_manager.complete_lesson(lesson_id, summary)

    return jsonify({"success": True, "message": "Lesson completed"})


@sock.route("/ws")
def websocket(ws):
    """处理WebSocket连接 - 基础示例"""
    logger.info("New WebSocket connection from client (Basic Demo)")

    if not DASHSCOPE_API_KEY:
        ws.send(
            json.dumps({"type": "error", "message": "DASHSCOPE_API_KEY not configured"})
        )
        return

    # 使用asyncio运行异步WebSocket逻辑
    async def handle_connection():
        client = QwenRealtimeClient(DASHSCOPE_API_KEY)

        # 连接到Qwen服务
        if not await client.connect():
            ws.send(
                json.dumps(
                    {"type": "error", "message": "Failed to connect to Qwen API"}
                )
            )
            return

        try:
            # 发送初始会话配置
            await client.send_session_update(
                {
                    "modalities": ["text", "audio"],
                    "voice": "Cherry",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",  # 改用 pcm16，更通用
                    "instructions": "你是一个友好的AI助手，请用中文回答问题。",
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "silence_duration_ms": 800,
                    },
                }
            )

            # 创建任务处理来自Qwen的消息
            qwen_task = asyncio.create_task(
                client.handle_qwen_messages(MockWebSocket(ws))
            )

            # 处理来自客户端的消息
            while True:
                try:
                    message = ws.receive(timeout=0.1)
                    if message is None:
                        await asyncio.sleep(0.01)
                        continue

                    data = json.loads(message)
                    msg_type = data.get("type", "")

                    # 只记录非音频消息，减少日志噪音
                    if msg_type != "audio":
                        logger.info(f"📤 Client event: {msg_type}")

                    # 根据消息类型处理
                    if msg_type == "audio":
                        await client.send_audio(data.get("audio", ""))
                    elif msg_type == "image":
                        await client.send_image(data.get("image", ""))
                    elif msg_type == "commit_audio":
                        await client.commit_audio()
                    elif msg_type == "session.update":
                        await client.send_session_update(data.get("session", {}))

                except Exception as e:
                    if "timed out" not in str(e):
                        logger.error(f"Error receiving from client: {e}")
                        break
                    await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            await client.close()
            if "qwen_task" in locals():
                qwen_task.cancel()

    # 运行异步处理
    asyncio.run(handle_connection())


class MockWebSocket:
    """模拟WebSocket接口用于Flask-Sock"""

    def __init__(self, ws):
        self.ws = ws

    async def send(self, message):
        self.ws.send(message)


@sock.route("/ws/tutor/<lesson_id>")
def tutor_websocket(ws, lesson_id):
    """AI英语外教 WebSocket连接"""
    logger.info(f"New tutor WebSocket connection for lesson: {lesson_id}")

    lesson = lesson_manager.get_lesson(lesson_id)
    if not lesson:
        ws.send(json.dumps({"type": "error", "message": "Lesson not found"}))
        return

    if not DASHSCOPE_API_KEY:
        ws.send(
            json.dumps({"type": "error", "message": "DASHSCOPE_API_KEY not configured"})
        )
        return

    # 使用asyncio运行异步WebSocket逻辑
    async def handle_tutor_connection():
        client = QwenRealtimeClient(DASHSCOPE_API_KEY)

        # 连接到Qwen服务
        if not await client.connect():
            ws.send(
                json.dumps(
                    {"type": "error", "message": "Failed to connect to Qwen API"}
                )
            )
            return

        try:
            # 发送AI外教会话配置
            instructions = lesson.system_prompt

            # 添加详细的课程计划信息
            if lesson.lesson_plan:
                instructions += f"\n\n=== LESSON PLAN ===\n"
                instructions += f"Topic: {lesson.lesson_plan.topic}\n"
                instructions += (
                    f"Duration: {lesson.lesson_plan.estimated_duration} minutes\n\n"
                )

                instructions += f"Objectives:\n"
                for i, obj in enumerate(lesson.lesson_plan.objectives, 1):
                    instructions += f"  {i}. {obj}\n"

                instructions += f"\nTeaching Steps (FOLLOW IN ORDER, ask 'Any questions?' after each step):\n"
                for i, step in enumerate(lesson.lesson_plan.outline, 1):
                    instructions += f"  {i}. {step}\n"

                instructions += f"\nVocabulary to teach (with meanings):\n"
                for i, word in enumerate(lesson.lesson_plan.vocabulary, 1):
                    instructions += f"  {i}. {word}\n"

                if lesson.lesson_plan.exercises:
                    instructions += f"\nContent to practice:\n"
                    for i, ex in enumerate(lesson.lesson_plan.exercises, 1):
                        ex_type = ex.get("type", "practice")
                        ex_content = ex.get("content", "")

                        if ex_type == "vocabulary":
                            instructions += f"\n  [VOCABULARY] Words: {ex_content}\n"
                        elif ex_type == "reading":
                            instructions += (
                                f"\n  [ARTICLE] Full text to read:\n  {ex_content}\n"
                            )
                        elif ex_type == "question":
                            instructions += f"\n  [QUESTION {i}] Student must ANSWER: {ex_content}\n"
                        else:
                            instructions += f"\n  [{ex_type.upper()}] {ex_content}\n"

                instructions += f"\n\nREMINDERS:"
                instructions += (
                    f"\n- For vocabulary: teach meaning, practice pronunciation"
                )
                instructions += f"\n- For articles: YOU read first, then student reads, then discuss"
                instructions += (
                    f"\n- For questions: student must ANSWER them, not just repeat"
                )
                instructions += (
                    f"\n- After each step, ask: 'Any questions about [topic]?'"
                )
                instructions += f"\n- Each item 2-3 times, then move on"

            # 添加完整的用户输入内容
            if lesson.user_input_text:
                instructions += f"\n\n=== ORIGINAL LEARNING MATERIAL (for reference) ===\n{lesson.user_input_text}\n"

            await client.send_session_update(
                {
                    "modalities": ["text", "audio"],
                    "voice": "Jennifer",  # 使用美式英语女声
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "instructions": instructions,
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "silence_duration_ms": 800,
                    },  # 默认启用VAD
                }
            )

            # 创建任务处理来自Qwen的消息
            qwen_task = asyncio.create_task(
                client.handle_qwen_messages(MockWebSocket(ws))
            )

            # 创建心跳任务，每30秒发送一次保活信号（防止长时间朗读导致超时）
            async def keepalive_loop():
                while True:
                    await asyncio.sleep(30)
                    await client.send_keepalive()

            keepalive_task = asyncio.create_task(keepalive_loop())

            # 等待一小段时间让session配置生效
            await asyncio.sleep(0.5)

            # 发送初始消息触发AI开始授课（AI会主动问候并开始讲课）
            await client.send_text_message(
                "Please start the lesson now. Greet the student and begin teaching."
            )
            logger.info("📤 Sent initial trigger message to start the lesson")

            # 处理来自客户端的消息
            while True:
                try:
                    message = ws.receive(timeout=0.1)
                    if message is None:
                        await asyncio.sleep(0.01)
                        continue

                    data = json.loads(message)
                    msg_type = data.get("type", "")

                    # 只记录非音频消息
                    if msg_type != "audio":
                        logger.info(f"📤 Tutor client event: {msg_type}")

                    # 根据消息类型处理
                    if msg_type == "audio":
                        await client.send_audio(data.get("audio", ""))
                    elif msg_type == "image":
                        await client.send_image(data.get("image", ""))
                    elif msg_type == "commit_audio":
                        await client.commit_audio()
                    elif msg_type == "session.update":
                        await client.send_session_update(data.get("session", {}))
                    elif msg_type == "stage_change":
                        # 处理阶段切换
                        stage = data.get("stage", "")
                        logger.info(f"🔄 Switching to stage: {stage}")

                        try:
                            # 获取该阶段的提示词
                            stage_prompt = lesson_manager.get_stage_prompt(stage)

                            # 构建包含学习材料的完整指令
                            full_instructions = stage_prompt

                            # 添加学习材料（根据阶段）
                            if lesson.lesson_plan:
                                if stage == "vocabulary":
                                    full_instructions += (
                                        "\n\n=== VOCABULARY TO TEACH ===\n"
                                    )
                                    for i, word in enumerate(
                                        lesson.lesson_plan.vocabulary[:15], 1
                                    ):
                                        full_instructions += f"{i}. {word}\n"

                                elif stage == "article":
                                    # 查找文章内容
                                    article_content = ""
                                    for ex in lesson.lesson_plan.exercises:
                                        if ex.get("type") == "reading":
                                            article_content = ex.get("content", "")
                                            break

                                    if article_content:
                                        full_instructions += "\n\n=== THE ARTICLE YOU MUST READ ALOUD ===\n"
                                        full_instructions += article_content
                                        full_instructions += "\n\n⚠️ IMPORTANT: Read every word of the above article aloud. Do NOT just say '[reads article]' - actually read it word by word!\n"

                                elif stage == "question":
                                    full_instructions += (
                                        "\n\n=== QUESTIONS FOR PRACTICE ===\n"
                                    )
                                    q_num = 1
                                    for ex in lesson.lesson_plan.exercises:
                                        if ex.get("type") == "question":
                                            full_instructions += (
                                                f"{q_num}. {ex.get('content', '')}\n"
                                            )
                                            q_num += 1

                            # 更新会话配置
                            # 只在article阶段禁用VAD（需要学生手动点击Stop Recording）
                            # 其他阶段使用VAD自动检测（来回对话）
                            turn_detection_config = (
                                None
                                if stage == "article"
                                else {
                                    "type": "server_vad",
                                    "threshold": 0.5,
                                    "silence_duration_ms": 800,
                                }
                            )

                            await client.send_session_update(
                                {
                                    "instructions": full_instructions,
                                    "turn_detection": turn_detection_config,
                                }
                            )

                            # 取消当前正在进行的响应（如果有）
                            try:
                                await client.cancel_response()
                                await asyncio.sleep(0.2)
                            except Exception as e:
                                logger.debug(f"No active response to cancel: {e}")

                            # 等待配置生效
                            await asyncio.sleep(0.8)

                            # 发送非常强烈的中断和切换指令
                            stage_messages = {
                                "vocabulary": "INTERRUPT! Stop everything. Forget previous context. NEW TASK: Teach vocabulary NOW. Say: 'Let's start with vocabulary. First word is...' and introduce the first word immediately.",
                                "article": "INTERRUPT! Stop everything. Forget previous context. NEW TASK: Read the article aloud NOW. Say: 'Let me read the article for you.' Then immediately start reading the complete article word by word without any delay.",
                                "question": "INTERRUPT! Stop everything. Forget previous context. NEW TASK: Ask questions NOW. Say: 'Time for questions.' Then immediately ask the first question.",
                                "review": "INTERRUPT! Stop everything. Forget previous context. NEW TASK: Review the lesson NOW. Say: 'Let's review.' Then immediately summarize what we learned.",
                            }
                            trigger_msg = stage_messages.get(
                                stage,
                                f"INTERRUPT! Stop everything. Switch to {stage} stage NOW.",
                            )

                            # 创建用户消息并触发响应
                            await client.send_text_message(trigger_msg)

                            logger.info(
                                f"✅ Switched to {stage} stage with learning material, AI will start immediately"
                            )

                        except ValueError as e:
                            logger.error(f"Invalid stage: {e}")

                    # 记录对话到课程
                    if msg_type in ["audio", "text"]:
                        content = data.get("content", "")
                        if content:
                            lesson_manager.add_transcript(lesson_id, "user", content)

                except Exception as e:
                    if "timed out" not in str(e):
                        logger.error(f"Error receiving from tutor client: {e}")
                        break
                    await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Tutor connection error: {type(e).__name__}: {e}")
        finally:
            logger.info("🔌 Closing tutor connection...")
            await client.close()
            if "qwen_task" in locals():
                qwen_task.cancel()
                try:
                    await qwen_task
                except asyncio.CancelledError:
                    pass
            if "keepalive_task" in locals():
                keepalive_task.cancel()
                try:
                    await keepalive_task
                except asyncio.CancelledError:
                    pass
            logger.info("✅ Tutor connection cleaned up")

    # 运行异步处理
    asyncio.run(handle_tutor_connection())


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 AI English Tutor Server")
    print("=" * 70)
    print(f"✅ API Key configured: {bool(DASHSCOPE_API_KEY)}")
    print(f"🌍 Region: {REGION.upper()}")
    print(f"🔗 API Endpoint: {QWEN_API_URL}")
    print(f"🌐 Server starting on http://localhost:5000")
    print("=" * 70)
    print("\n📚 Available pages:")
    print("   - Basic Demo: http://localhost:5000")
    print("   - AI English Tutor: http://localhost:5000/tutor")
    print("\n💡 提示：")
    print("   - 如在中国大陆，使用北京区域的 API Key")
    print("   - 如在海外，设置 DASHSCOPE_REGION=singapore 或 virginia")
    print("   - 示例: export DASHSCOPE_REGION=singapore\n")

    app.run(host="0.0.0.0", port=5000, debug=True)
