"""
阶段切换处理器
处理不同教学阶段之间的切换和提示词生成
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


async def handle_stage_switch(qwen_ws, stage, lesson, client_ws):
    """
    处理教学阶段切换

    Args:
        qwen_ws: QwenRealtimeClient 实例
        stage: 目标阶段名称
        lesson: 当前课程对象
        client_ws: 客户端WebSocket连接
    """
    logger.info(f"🔄 Stage switch requested: {stage}")

    try:
        # Step 1: 取消当前响应
        await qwen_ws.cancel_response()
        logger.info("✅ Current response cancelled")
        await asyncio.sleep(0.3)

        # Step 2: 更新会话配置（使用1500ms静音检测）
        session_config = {
            "voice": "longxiaochun",
            "language": "en",
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "sample_rate": 16000,
            "output_sample_rate": 24000,
            "vad": {
                "silence_duration_ms": 1500,  # 1.5秒静音判断
                "silence_threshold": 0.3,
                "speaking_threshold": 0.6,
            },
        }
        await qwen_ws.send_session_update(session_config)
        logger.info("✅ VAD configuration updated (silence: 1500ms)")
        await asyncio.sleep(0.1)

        # Step 3: 清理音频缓冲区
        await qwen_ws.clear_audio_buffer()
        logger.info("✅ Audio buffer cleared")
        await asyncio.sleep(0.2)

        # Step 4: 获取阶段提示词
        prompt = lesson.get_stage_prompt(stage)
        if not prompt:
            error_msg = f"⚠️ Unknown stage: {stage}"
            logger.error(error_msg)
            await client_ws.send(f'{{"type": "error", "message": "{error_msg}"}}')
            return

        logger.info(f"📝 Stage prompt: {prompt[:100]}...")

        # Step 5: 触发阶段转换
        interrupt_prompt = (
            f"[STAGE CHANGE] Now starting: {stage}\n\n{prompt}\n\n"
            f"Please start teaching this new section immediately."
        )
        await qwen_ws.send_text_message(interrupt_prompt)
        logger.info(f"✅ Stage switch complete → {stage}")

        # 发送确认消息
        await client_ws.send(f'{{"type": "stage_changed", "stage": "{stage}"}}')

    except Exception as e:
        error_msg = f"❌ Stage switch error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        await client_ws.send(f'{{"type": "error", "message": "{error_msg}"}}')


def get_system_prompt():
    """获取系统提示词"""
    return """You are an experienced English teacher conducting a one-on-one online lesson via voice.

CRITICAL INSTRUCTIONS:
- Speak in English ONLY, always
- Keep responses SHORT (1-2 sentences max)
- After teaching vocabulary or reading, ask ONE simple question
- Wait for student to answer - DO NOT answer your own questions
- When student answers, give brief feedback then move on
- NEVER say the answer after asking a question

TEACHING FLOW:
1. Vocabulary: Teach word → pronunciation → usage → ask "Can you use it in a sentence?"
2. Article: Read first → student reads → ask ONE comprehension question
3. Questions: Ask question → WAIT → student answers → brief feedback

EXAMPLES:
✅ Good: "Great! Now, what does 'indigenous' mean?"
❌ Bad: "What does 'indigenous' mean? It means native to a place..."

Remember: WAIT for student responses. Be patient and encouraging."""
