"""
课程管理路由
处理课程的CRUD操作
"""

import logging
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from lesson_manager import Lesson, LessonStatus
from services.lesson_service import create_fallback_lesson_plan, create_lesson_plan

logger = logging.getLogger(__name__)

# 创建蓝图
lesson_routes = Blueprint("lesson_routes", __name__)

# 全局存储（简单实现，生产环境应使用数据库）
lessons_storage = {}
lesson_plans_storage = {}


@lesson_routes.route("/")
def index():
    """首页 - 显示所有课程"""
    logger.info("📄 Loading index page")
    return render_template("index.html")


@lesson_routes.route("/api/lessons", methods=["GET"])
def get_lessons():
    """获取所有课程列表"""
    logger.info("📋 Getting all lessons")
    lessons_list = [
        {
            "id": lesson.id,
            "topic": lesson.topic,
            "status": lesson.status.value,
            "created_at": lesson.created_at,
            "started_at": lesson.started_at,
            "ended_at": lesson.ended_at,
        }
        for lesson in lessons_storage.values()
    ]
    return jsonify(lessons_list)


@lesson_routes.route("/api/lessons", methods=["POST"])
def create_lesson():
    """创建新课程"""
    data = request.json
    lesson_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()

    logger.info(f"📝 Creating new lesson: {lesson_id}")

    # 创建课程
    lesson = Lesson(
        id=lesson_id,
        topic=data.get("topic", "New Lesson"),
        status=LessonStatus.CREATED,
        created_at=created_at,
    )

    lessons_storage[lesson_id] = lesson
    logger.info(f"✅ Lesson created: {lesson_id} - {lesson.topic}")

    return jsonify(
        {
            "id": lesson.id,
            "topic": lesson.topic,
            "status": lesson.status.value,
            "created_at": lesson.created_at,
        }
    )


@lesson_routes.route("/api/lessons/<lesson_id>", methods=["GET"])
def get_lesson(lesson_id):
    """获取课程详情"""
    lesson = lessons_storage.get(lesson_id)
    if not lesson:
        return jsonify({"error": "Lesson not found"}), 404

    return jsonify(
        {
            "id": lesson.id,
            "topic": lesson.topic,
            "status": lesson.status.value,
            "created_at": lesson.created_at,
            "started_at": lesson.started_at,
            "ended_at": lesson.ended_at,
        }
    )


@lesson_routes.route("/api/lessons/<lesson_id>", methods=["DELETE"])
def delete_lesson(lesson_id):
    """删除课程"""
    if lesson_id in lessons_storage:
        lesson = lessons_storage[lesson_id]
        del lessons_storage[lesson_id]
        if lesson_id in lesson_plans_storage:
            del lesson_plans_storage[lesson_id]
        logger.info(f"🗑️  Lesson deleted: {lesson_id}")
        return jsonify({"message": "Lesson deleted successfully"})

    return jsonify({"error": "Lesson not found"}), 404


@lesson_routes.route("/api/lessons/<lesson_id>/prepare", methods=["POST"])
def prepare_lesson(lesson_id):
    """准备课程（生成课程计划）"""
    lesson = lessons_storage.get(lesson_id)
    if not lesson:
        return jsonify({"error": "Lesson not found"}), 404

    data = request.json
    user_text = data.get("text", "")

    logger.info(f"📚 Preparing lesson: {lesson_id}")
    logger.info(f"User input: {user_text[:200]}...")

    try:
        # 创建课程计划
        plan = create_lesson_plan(lesson_id, user_text, lesson.created_at)
        lesson_plans_storage[lesson_id] = plan

        # 更新课程状态
        lesson.status = LessonStatus.PREPARED
        logger.info(f"✅ Lesson prepared: {lesson_id} - {plan.topic}")

        return jsonify(
            {
                "lesson_id": lesson_id,
                "topic": plan.topic,
                "objectives": plan.objectives,
                "outline": plan.outline,
                "vocabulary": plan.vocabulary,
                "estimated_duration": plan.estimated_duration,
            }
        )

    except Exception as e:
        logger.error(f"❌ Lesson preparation failed: {str(e)}", exc_info=True)
        # 使用后备课程计划
        plan = create_fallback_lesson_plan(lesson_id, lesson.created_at)
        lesson_plans_storage[lesson_id] = plan
        lesson.status = LessonStatus.PREPARED

        return jsonify(
            {
                "lesson_id": lesson_id,
                "topic": plan.topic,
                "objectives": plan.objectives,
                "outline": plan.outline,
                "vocabulary": plan.vocabulary,
                "estimated_duration": plan.estimated_duration,
                "warning": "Used fallback plan due to error",
            }
        )


@lesson_routes.route("/tutor/<lesson_id>")
def tutor(lesson_id):
    """进入教学页面"""
    lesson = lessons_storage.get(lesson_id)
    if not lesson:
        logger.error(f"❌ Lesson not found: {lesson_id}")
        return "Lesson not found", 404

    plan = lesson_plans_storage.get(lesson_id)
    if not plan:
        logger.error(f"❌ Lesson plan not found: {lesson_id}")
        return "Lesson plan not found. Please prepare the lesson first.", 404

    logger.info(f"👨‍🏫 Loading tutor page for lesson: {lesson_id}")
    return render_template("tutor.html")


@lesson_routes.route("/api/lessons/<lesson_id>/plan", methods=["GET"])
def get_lesson_plan(lesson_id):
    """获取课程计划"""
    plan = lesson_plans_storage.get(lesson_id)
    if not plan:
        return jsonify({"error": "Lesson plan not found"}), 404

    return jsonify(
        {
            "lesson_id": plan.lesson_id,
            "topic": plan.topic,
            "objectives": plan.objectives,
            "outline": plan.outline,
            "exercises": plan.exercises,
            "vocabulary": plan.vocabulary,
            "estimated_duration": plan.estimated_duration,
        }
    )


# 辅助函数：从其他模块访问存储
def get_lesson_from_storage(lesson_id):
    """获取课程对象"""
    return lessons_storage.get(lesson_id)


def get_lesson_plan_from_storage(lesson_id):
    """获取课程计划对象"""
    return lesson_plans_storage.get(lesson_id)
