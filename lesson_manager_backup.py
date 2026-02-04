"""
AI English Tutor - 数据模型和工具类
"""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class LessonStatus(Enum):
    """课程状态"""

    PREPARING = "preparing"  # 准备中
    READY = "ready"  # 准备完成
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


@dataclass
class LessonPlan:
    """课程计划"""

    lesson_id: str
    topic: str
    objectives: List[str]
    outline: List[str]
    exercises: List[Dict[str, str]]
    vocabulary: List[str]
    estimated_duration: int  # 分钟
    created_at: str

    def to_dict(self):
        return asdict(self)


@dataclass
class Lesson:
    """课程实例"""

    lesson_id: str
    user_input_text: Optional[str]
    user_input_images: List[str]  # base64 或 URL
    status: LessonStatus
    lesson_plan: Optional[LessonPlan]
    system_prompt: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    transcript: List[Dict[str, str]]  # 对话记录
    performance_summary: Optional[str]

    def to_dict(self):
        data = asdict(self)
        data["status"] = self.status.value
        return data


class LessonManager:
    """课程管理器"""

    def __init__(self):
        self.lessons: Dict[str, Lesson] = {}

    def create_lesson(self, text_input: Optional[str], images: List[str]) -> str:
        """创建新课程"""
        lesson_id = str(uuid.uuid4())
        lesson = Lesson(
            lesson_id=lesson_id,
            user_input_text=text_input,
            user_input_images=images,
            status=LessonStatus.PREPARING,
            lesson_plan=None,
            system_prompt=self._get_tutor_system_prompt(),
            created_at=datetime.now().isoformat(),
            started_at=None,
            completed_at=None,
            transcript=[],
            performance_summary=None,
        )
        self.lessons[lesson_id] = lesson
        return lesson_id

    def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """获取课程"""
        return self.lessons.get(lesson_id)

    def update_lesson_plan(self, lesson_id: str, plan: LessonPlan):
        """更新课程计划"""
        if lesson_id in self.lessons:
            self.lessons[lesson_id].lesson_plan = plan
            self.lessons[lesson_id].status = LessonStatus.READY

    def start_lesson(self, lesson_id: str):
        """开始课程"""
        if lesson_id in self.lessons:
            self.lessons[lesson_id].status = LessonStatus.IN_PROGRESS
            self.lessons[lesson_id].started_at = datetime.now().isoformat()

    def complete_lesson(self, lesson_id: str, summary: str):
        """完成课程"""
        if lesson_id in self.lessons:
            self.lessons[lesson_id].status = LessonStatus.COMPLETED
            self.lessons[lesson_id].completed_at = datetime.now().isoformat()
            self.lessons[lesson_id].performance_summary = summary

    def add_transcript(self, lesson_id: str, role: str, content: str):
        """添加对话记录"""
        if lesson_id in self.lessons:
            self.lessons[lesson_id].transcript.append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def _get_tutor_system_prompt(self) -> str:
        """获取AI外教系统提示"""
        return """You are a professional native English teacher.

CRITICAL RULES:
1. Keep responses SHORT - maximum 1-2 sentences at a time
2. YOU speak first to greet the student
3. Follow the lesson plan STEP BY STEP
4. Each teaching point should be practiced 2-3 times, then MOVE ON
5. After completing each step, ask: "Any questions about [step topic]?"

Teaching Flow by Step:

STEP 1 - VOCABULARY:
- Teach each word 2-3 times: "First word: [word]. It means [brief meaning]. Please repeat."
- After all words, ask: "Any questions about the vocabulary?"

STEP 2 - ARTICLE/TEXT:
- First, YOU read the full article aloud once
- Then say: "Now you try reading it."
- After student reads, ask: "Good! Do you understand everything? Any questions?"
- If student asks questions, answer them briefly and clearly
- Practice difficult parts if needed (max 2-3 times)

STEP 3 - QUESTIONS (Practice ANSWERING, not just reading):
- For each question, ask the student to ANSWER it, not just repeat the question
- Say: "Now answer this question: [question]"
- Listen to student's answer
- Give feedback: "Good answer!" or "Try answering like this: [example]"
- Practice each question 2-3 times
- After all questions, ask: "Any questions about these topics?"

STEP 4 - REVIEW:
- Briefly summarize what was learned
- Ask: "Any final questions?"

IMPORTANT: 
- Don't ask students to repeat questions - ask them to ANSWER
- Give students time to think and respond
- Encourage interaction and questions after each step
- Move forward systematically

Example for Article step:
Teacher: "Let me read the article first: [reads full article]. Now you try reading it."
Student: [reads]
Teacher: "Good job! Do you understand the story? Any difficult words or sentences?"

Example for Questions step:
Teacher: "Now let's practice. Question: How do people show yes in Micronesia? Please answer this question."
Student: "They raise their eyebrows."
Teacher: "Excellent answer! Let's try another one..."


# 全局课程管理器实例
lesson_manager = LessonManager()
