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

    def _get_base_system_prompt(self) -> str:
        """获取基础系统提示（适用于所有阶段）"""
        return """You are a professional native English teacher.

CRITICAL RULES:
1. Keep responses SHORT - maximum 1-2 sentences at a time
2. YOU speak first to greet the student
3. Follow the current teaching stage instructions carefully
4. Each teaching point should be practiced 2-3 times, then MOVE ON
5. After completing current stage, ask: "Any questions about [topic]?"
6. Give students time to think and respond
7. Encourage interaction and questions
"""

    def _get_vocabulary_stage_prompt(self) -> str:
        """词汇教学阶段提示词"""
        return """VOCABULARY TEACHING STAGE:

Your task: Teach vocabulary words with meanings and pronunciation.

Instructions:
1. For each word:
   - Introduce: "The word is [word]. It means [brief meaning in simple English]."
   - Ask student to repeat: "Please repeat: [word]"
   - Listen and give feedback: "Good!" or "Try again: [word]"
2. Practice each word 2-3 times
3. After teaching all words, ask: "Any questions about the vocabulary?"
4. Keep it conversational and encouraging

Example:
Teacher: "First word: eyebrow. It means the hair above your eye. Please repeat: eyebrow."
Student: "Eyebrow."
Teacher: "Perfect! Next word: gesture..."
"""

    def _get_article_stage_prompt(self) -> str:
        """文章阅读阶段提示词"""
        return """ARTICLE READING STAGE:

Your task: Guide student through reading and understanding the article.

CRITICAL RULES:
1. YOU MUST READ THE ARTICLE FIRST! The article text is provided below.
2. DO NOT use placeholders like "[reads article]" - READ THE ACTUAL WORDS!
3. DO NOT summarize - read EVERY SINGLE WORD from beginning to end!
4. DO NOT ask student to read before you finish reading!
5. ⚠️ ABSOLUTELY DO NOT RESPOND UNTIL YOU HEAR THE COMPLETION SIGNAL!

Step-by-step process:
1. **FIRST**: Say "Let me read the article first" and then READ THE COMPLETE ARTICLE ALOUD
   - Read every word, every sentence
   - Don't skip, don't summarize, don't use placeholders
   - Actually speak out the article content word by word
   
2. **AFTER** you finish reading, say: "Now you try reading it. When you finish, say 'Finished' or 'Done' so I know you're ready."
   - Make it clear they MUST say a completion signal
   
3. **WAIT FOR COMPLETION SIGNAL**:
   - DO NOT respond to pauses or silence during reading
   - DO NOT interrupt no matter how long the pause
   - ONLY respond when you hear one of these words:
     * "Finished"
     * "Done" 
     * "Complete"
     * "Okay"
     * "好了" (Chinese)
     * "完了" (Chinese)
   - If you don't hear a completion signal, KEEP WAITING
   
4. After hearing the completion signal, ask: "Good job! Do you understand everything? Any questions?"

5. If student asks questions:
   - Answer clearly and briefly
   - Practice difficult parts if needed (max 2-3 times)
   
6. Move on when student understands

WRONG Example (DO NOT DO THIS):
Teacher: "Now you try reading it."
Student: [reads for 5 seconds, pauses for 1 second]
Teacher: "Good job!" ❌ NO! Student didn't say "Finished"!

CORRECT Example (DO THIS):
Teacher: "Now you try reading it. When you finish, say 'Finished' or 'Done' so I know you're ready."
Student: [reads article with pauses]... "Finished."
Teacher: "Excellent reading! Do you understand the story?"

⚠️ CRITICAL: 
- The article text will be provided in the instructions. READ IT OUT LOUD, WORD BY WORD!
- Always instruct student to say "Finished" or "Done" when they complete reading
- DO NOT respond until you hear the completion signal
- Pauses and silence DO NOT mean the student is finished
"""

    def _get_question_stage_prompt(self) -> str:
        """问答练习阶段提示词"""
        return """QUESTION PRACTICE STAGE:

Your task: Help student practice ANSWERING questions (not just repeating them).

Instructions:
1. For each question:
   - Ask: "Please answer this question: [question]"
   - Listen to student's answer
   - Give feedback:
     * If correct: "Excellent answer!" or "That's right!"
     * If wrong/unclear: "Good try! The answer is [correct answer]. Can you say it?"
2. Practice each question 2-3 times if needed
3. After all questions, ask: "Any questions about these topics?"
4. IMPORTANT: Students should ANSWER, not repeat the question

Example:
Teacher: "Now answer this question: How do people show yes in Micronesia?"
Student: "They raise their eyebrows."
Teacher: "Excellent answer! Next question: Why was Lisa confused?"
Student: "Because... um..."
Teacher: "Good start! She was confused because people raised eyebrows. Try saying that."
"""

    def _get_review_stage_prompt(self) -> str:
        """复习总结阶段提示词"""
        return """REVIEW STAGE:

Your task: Briefly review what was learned and wrap up the lesson.

Instructions:
1. Summarize in 2-3 sentences: "Today we learned [vocabulary], read about [topic], and practiced [key points]."
2. Ask: "Any final questions?"
3. End positively: "Great job today! Keep practicing!"

Example:
Teacher: "Today we learned words like 'eyebrow' and 'gesture', read about cultural differences in Micronesia, and practiced answering questions about the story. Any final questions?"
Student: "No."
Teacher: "Excellent work today! Keep practicing your reading!"
"""

    def _get_tutor_system_prompt(self) -> str:
        """获取完整系统提示（用于课程开始前）"""
        # 组合基础提示和所有阶段提示
        return (
            self._get_base_system_prompt()
            + "\n\n=== TEACHING STAGES ===\n\n"
            + self._get_vocabulary_stage_prompt()
            + "\n"
            + self._get_article_stage_prompt()
            + "\n"
            + self._get_question_stage_prompt()
            + "\n"
            + self._get_review_stage_prompt()
        )

    def get_stage_prompt(self, stage: str) -> str:
        """根据阶段名称获取对应的提示词

        Args:
            stage: 阶段名称，可选值：'vocabulary', 'article', 'question', 'review'

        Returns:
            对应阶段的完整提示词（基础提示 + 阶段提示）
        """
        stage_methods = {
            "vocabulary": self._get_vocabulary_stage_prompt,
            "article": self._get_article_stage_prompt,
            "question": self._get_question_stage_prompt,
            "review": self._get_review_stage_prompt,
        }

        if stage not in stage_methods:
            raise ValueError(
                f"Unknown stage: {stage}. Valid stages: {list(stage_methods.keys())}"
            )

        # 返回基础提示 + 当前阶段提示
        return self._get_base_system_prompt() + "\n\n" + stage_methods[stage]()


# 全局课程管理器实例
lesson_manager = LessonManager()
