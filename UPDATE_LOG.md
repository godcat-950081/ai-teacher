# AI English Tutor - 更新日志

## 2026-01-15 更新

### 🎯 主要改进

#### 1. AI 老师主动问候功能

**问题**: 之前需要学生先说话，AI 才会响应。

**解决方案**:

- 修改了`lesson_manager.py`中的 system prompt，明确要求 AI 在课程开始时立即主动问候
- 在`app.py`的 WebSocket 连接建立后，自动发送触发消息让 AI 开始授课
- 添加了`send_text_message()`方法用于发送初始触发消息

**效果**: 现在连接成功后，AI 会立即说："Hello! Welcome to today's English lesson!" 并开始介绍课程。

#### 2. 基于上传图片内容授课

**问题**: AI 没有按照上传的图片内容进行教学。

**解决方案**:

- 在 system prompt 中强调："You MUST teach based on the content visible in these images"
- 将课程计划的详细信息（包括图片数量、词汇、练习等）完整注入到 instructions 中
- 在 instructions 中明确标注了三个部分：
  - `=== LESSON PLAN (FOLLOW THIS CONTENT) ===` - 课程计划详情
  - `=== IMAGES PROVIDED ===` - 图片信息说明
  - `=== STUDENT'S REQUEST ===` - 学生输入的文本请求

**效果**: AI 现在会：

1. 根据图片中的具体内容（单词、句子、对话等）进行教学
2. 引用图片中的具体内容
3. 按照生成的课程计划大纲逐步授课

### 📝 技术细节

#### 修改的文件

1. **lesson_manager.py**

   - 更新了`_get_tutor_system_prompt()`方法
   - 新增"IMPORTANT INSTRUCTIONS"部分强调主动问候
   - 明确要求："YOU MUST IMMEDIATELY greet the student warmly WITHOUT waiting for them to speak first"

2. **app.py**
   - 在`QwenRealtimeClient`类中新增`send_text_message()`方法
   - 修改了`tutor_websocket()`函数中的 instructions 构建逻辑
   - 在 WebSocket 连接建立后添加了初始触发消息
   - 修复了属性名称错误（`input_text` → `user_input_text`）

### 🔍 工作流程

```
1. 用户上传图片/输入文本
   ↓
2. AI生成个性化课程计划（包含图片内容分析）
   ↓
3. 用户点击"Start Lesson"
   ↓
4. WebSocket连接建立
   ↓
5. 发送详细的instructions（包含课程计划+图片信息）
   ↓
6. 自动发送触发消息
   ↓
7. AI立即主动问候："Hello! Welcome to..."
   ↓
8. AI按照课程计划和图片内容开始授课
   ↓
9. 学生与AI进行互动对话
```

### ✅ 测试建议

1. **测试主动问候**:

   - 创建课程后点击"Start Lesson"
   - 不要点击"Start Recording"
   - 应该能听到 AI 主动问候

2. **测试图片教学**:
   - 上传一张英语教材图片（如包含单词表或对话的页面）
   - 生成课程计划
   - 开始课程
   - AI 应该会提到图片中的具体内容进行教学

### 📋 System Prompt 关键改进

**之前**:

```
At the beginning of the lesson:
- Greet the student in a friendly and encouraging manner.
```

**现在**:

```
IMPORTANT INSTRUCTIONS:
1. When the lesson starts, YOU MUST IMMEDIATELY greet the student warmly
   WITHOUT waiting for them to speak first.
2. After greeting, explain the lesson topic based on the lesson plan provided.
3. You MUST teach according to the content shown in the images.

At the beginning of the lesson (START SPEAKING FIRST):
- Greet the student (e.g., "Hello! Welcome to today's English lesson!")
- Briefly introduce the lesson topic and what you will cover.
- Start teaching immediately based on the lesson plan content.
```

### 🎓 Instructions 注入示例

```
You are a professional native English teacher...

=== LESSON PLAN (FOLLOW THIS CONTENT) ===
Topic: Daily Greetings and Introductions
Objectives:
  - Learn common greeting phrases
  - Practice self-introduction
  - Improve pronunciation

Lesson Outline:
  - Step 1: Warm-up with basic greetings
  - Step 2: Vocabulary introduction
  - Step 3: Practice conversations
  - Step 4: Pronunciation drills

Key Vocabulary: hello, goodbye, nice to meet you, how are you

=== IMAGES PROVIDED ===
The student has uploaded 2 image(s) showing the learning material.
You MUST teach based on the content visible in these images.
Refer to specific words, sentences, or dialogues from the images.

=== STUDENT'S REQUEST ===
I want to learn how to greet people in English
```

---

## 后续可优化项

1. **图片内容识别增强**: 可以在课程准备阶段，先用 Qwen-VL 提取图片中的文字内容，作为结构化数据传递给教学 session
2. **上下文记忆**: 可以在对话过程中记录已教过的内容，避免重复
3. **自适应难度**: 根据学生的表现实时调整教学难度
4. **多轮对话优化**: 改进对话流畅性，让教学更自然

---

**更新时间**: 2026-01-15  
**版本**: v1.1.0  
**状态**: ✅ 已测试，可以使用
