"""
课程准备服务
处理课程内容解析和课程计划生成
"""

import logging
import re

from lesson_manager import LessonPlan

logger = logging.getLogger(__name__)


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

    # 如果有结构化内容，提取主题
    if has_vocabulary or has_article:
        # 尝试从文章中提取主题
        if "Micronesia" in text or "Sweden" in text or "India" in text:
            return "Cross-Cultural Communication and Language Learning"
        elif "Gordon" in text or "Chris" in text:
            return "Living Abroad and Language Learning"

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

        # 识别章节标题并提取同行内容
        if "单词" in line or "vocabulary" in line.lower():
            current_section = "vocabulary"
            if article_lines:
                result["articles"].append("\n".join(article_lines))
                article_lines = []

            # 提取同一行的单词（如：单词：word1, word2）
            if "：" in line:
                content = line.split("：", 1)[1]
            elif ":" in line:
                content = line.split(":", 1)[1]
            else:
                continue

            # 解析单词
            words = content.replace("，", ",").split(",")
            for word in words:
                word = word.strip()
                if word:
                    result["vocabulary"].append(word)
            continue

        elif "文章" in line or "article" in line.lower() or "passage" in line.lower():
            current_section = "article"
            # 保存之前的文章
            if article_lines:
                result["articles"].append("\n".join(article_lines))
                article_lines = []

            # 如果同一行有内容，也要提取
            if "：" in line:
                content = line.split("：", 1)[1].strip()
                if content:
                    article_lines.append(content)
            elif ":" in line:
                content = line.split(":", 1)[1].strip()
                if content:
                    article_lines.append(content)
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


def create_lesson_plan(lesson_id, user_text, created_at):
    """
    基于用户输入创建结构化课程计划

    Args:
        lesson_id: 课程ID
        user_text: 用户输入的课程内容
        created_at: 创建时间

    Returns:
        LessonPlan对象
    """
    if not user_text:
        user_text = "General English conversation practice"

    logger.info(f"📚 Creating lesson plan for: {user_text[:100]}...")

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
        for article in parsed["articles"][:2]:  # 最多2篇文章
            exercises.append({"type": "reading", "content": article})

    if parsed["questions"]:
        objectives.append("Answer questions about the content")
        outline.append(
            "Step 3: Questions - Student ANSWERS each question (not just repeat)"
        )
        for q in parsed["questions"][:5]:  # 最多5个问题
            exercises.append({"type": "question", "content": q})

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

    # 估算时长
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
        created_at=created_at,
    )

    logger.info(
        f"✅ Lesson plan created: {topic} "
        f"({len(vocabulary)} words, {len(parsed['articles'])} articles, "
        f"{len(parsed['questions'])} questions)"
    )

    return plan


def create_fallback_lesson_plan(lesson_id, created_at):
    """创建默认的后备课程计划"""
    logger.warning("Using fallback lesson plan")

    return LessonPlan(
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
        created_at=created_at,
    )
