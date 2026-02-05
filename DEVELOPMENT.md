# AI English Tutor - 开发文档 🛠️

本文档面向项目维护者和开发者，包含技术细节、架构说明、代码结构和问题修复记录。

## 📑 目录

- [技术架构](#技术架构)
- [代码结构](#代码结构)
- [模块详解](#模块详解)
- [教学阶段管理](#教学阶段管理)
- [提示词设计](#提示词设计)
- [按钮行为规范](#按钮行为规范)
- [阶段切换调试](#阶段切换调试)
- [扩展开发](#扩展开发)
- [问题修复记录](#问题修复记录)
- [开发最佳实践](#开发最佳实践)

---

## 技术架构

### 后端技术栈

- **Flask 2.x** - Web框架
- **Flask-Sock** - WebSocket支持
- **websockets** - 异步WebSocket客户端（连接Qwen API）
- **asyncio** - 异步IO处理
- **Pillow** - 图片处理
- **dashscope** - 阿里云百炼SDK

### 前端技术栈

- **原生JavaScript** - 无框架依赖
- **Web Audio API** - 音频录制和播放
- **Canvas API** - 音频波形可视化
- **WebSocket API** - 实时通信

### AI模型

- **Qwen3-Omni-Flash-Realtime** - 实时语音交互
- **Qwen-VL-Max** - 图片内容分析

### 音频格式

- **输入**: PCM16, 16kHz, 单声道
- **输出**: PCM16, 24kHz, 单声道
- **编码**: Base64传输

---

## 代码结构

### 📁 项目结构（模块化架构 v1.3.0）

```
ai-teacher/
├── app.py                      # 主应用入口（42行）
├── lesson_manager.py           # 课程数据模型
│
├── services/                   # 🔧 业务服务层
│   ├── __init__.py
│   ├── qwen_client.py         # Qwen API客户端（~250行）
│   └── lesson_service.py      # 课程准备服务（~270行）
│
├── handlers/                   # 🎯 业务处理层
│   ├── __init__.py
│   └── stage_handler.py       # 阶段切换处理（~100行）
│
├── routes/                     # 🛣️ 路由层
│   ├── __init__.py
│   ├── lesson_routes.py       # 课程管理API（~180行）
│   └── websocket_routes.py    # WebSocket通信（~190行）
│
├── static/                     # 前端静态文件
│   ├── app.js                 # 首页逻辑
│   └── tutor.js               # 教学页面逻辑
│
├── templates/                  # HTML模板
│   ├── index.html             # 首页
│   └── tutor.html             # 教学页面
│
├── test_structure.py          # 模块结构测试
├── requirements.txt           # Python依赖
├── .env                       # 环境配置
└── README.md                  # 用户文档
```

### 🔄 代码重构历史

**v1.3.0 (2026-02-05)** - 模块化重构
- **重构前**: 单文件 `app.py` (1039行)
- **重构后**: 按功能拆分为6个模块
- **优势**:
  - ✅ 职责分离清晰
  - ✅ 易于维护和测试
  - ✅ 代码复用性提高
  - ✅ 团队协作更友好

---

## 模块详解

### 1️⃣ app.py - 主应用入口 (42行)

**职责**: 创建和配置Flask应用，注册路由模块

**核心代码**:
```python
from routes.lesson_routes import lesson_routes
from routes.websocket_routes import register_websocket_routes

app = Flask(__name__)
app.register_blueprint(lesson_routes)
register_websocket_routes(app)
```

### 2️⃣ services/qwen_client.py - Qwen API客户端 (~250行)

**职责**: 与Qwen-Omni-Realtime API通信

**主要方法**:
- `connect()` - 建立WebSocket连接
- `send_audio(data)` - 发送音频数据
- `send_text_message(text)` - 发送文本消息
- `cancel_response()` - 取消当前响应
- `clear_audio_buffer()` - 清空音频缓冲区
- `handle_qwen_messages(client_ws)` - 处理API返回的消息流

**使用示例**:
```python
from services.qwen_client import QwenRealtimeClient

qwen_ws = QwenRealtimeClient()
await qwen_ws.connect()
await qwen_ws.send_text_message("Hello!")
```

### 3️⃣ services/lesson_service.py - 课程准备服务 (~270行)

**职责**: 解析用户输入并生成结构化课程计划

**主要函数**:
- `parse_structured_lesson(text)` - 解析结构化内容（单词/文章/练习）
- `extract_lesson_info(text)` - 提取课程主题
- `create_lesson_plan(...)` - 创建完整的课程计划
- `create_fallback_lesson_plan(...)` - 创建后备课程计划

**输入格式**:
```
单词：indigenous, fluent, Sweden
文章：Gordon lives in Sweden and his wife Chris is learning Swedish.
练习：
1. Where does Gordon live?
2. What language is Chris learning?
```

**输出**: `LessonPlan`对象，包含单词列表、文章内容、练习题、课程大纲等

### 4️⃣ handlers/stage_handler.py - 阶段切换处理 (~100行)

**职责**: 管理教学阶段之间的切换

**核心函数**:
```python
async def handle_stage_switch(qwen_ws, stage, lesson, client_ws):
    """处理阶段切换"""
    # 1. 取消当前响应
    await qwen_ws.cancel_response()

    # 2. 更新会话配置（带VAD）
    await qwen_ws.send_session_update({
        "voice": "longxiaochun",
        "vad": {"silence_duration_ms": 1500, ...}
    })

    # 3. 清理音频缓冲区
    await qwen_ws.clear_audio_buffer()

    # 4. 发送阶段提示词
    prompt = lesson.get_stage_prompt(stage)
    await qwen_ws.send_text_message(prompt)
```

### 5️⃣ routes/lesson_routes.py - 课程管理API (~180行)

**职责**: 提供课程CRUD操作的REST API

**主要路由**:
- `GET /` - 首页
- `GET /api/lessons` - 获取课程列表
- `POST /api/lessons` - 创建新课程
- `GET /api/lessons/<id>` - 获取课程详情
- `POST /api/lessons/<id>/prepare` - 准备课程
- `GET /tutor/<id>` - 进入教学页面

### 6️⃣ routes/websocket_routes.py - WebSocket通信 (~190行)

**职责**: 处理实时音频和消息通信

**主要路由**:
- `@sock.route('/ws/tutor/<lesson_id>')` - 教学WebSocket

**处理流程**:
1. 建立WebSocket连接
2. 连接Qwen API
3. 配置会话（系统提示词、VAD等）
4. 启动消息处理任务
5. 处理客户端消息（音频、阶段切换等）
6. 清理资源

---

## 教学阶段管理

### 阶段定义

系统支持4个教学阶段：

| 阶段 | 代码 | 功能 |
|------|------|------|
| 📚 词汇教学 | `vocabulary` | 逐个教授单词发音和含义 |
| 📖 文章阅读 | `article` | AI先朗读，学生跟读，回答问题 |
| ❓ 问答练习 | `questions` | AI提问，学生回答，AI反馈 |
| ✅ 复习总结 | `review` | 总结知识点，鼓励反馈 |

### 阶段切换流程

```
用户点击阶段按钮
  ↓
前端发送 {type: "switch_stage", stage: "article"}
  ↓
后端调用 handle_stage_switch()
  ↓
1. 取消当前响应 (cancel_response)
  ↓ 等待 300ms
2. 更新会话配置 (send_session_update)
  ↓ 等待 100ms
3. 清空音频缓冲 (clear_audio_buffer)
  ↓ 等待 200ms
4. 发送阶段提示词 (send_text_message)
  ↓
AI开始新阶段
```

### WebSocket消息格式

**阶段切换（前端→后端）**:
```json
{
  "type": "switch_stage",
  "stage": "article"
}
```

**音频数据（前端→后端）**:
```json
{
  "type": "audio",
  "audio": "base64_encoded_pcm16_data"
}
```

**音频提交（前端→后端）**:
```json
{
  "type": "commit_audio"
}
```

---

## 提示词设计
   - 使用**加粗**强调
   - 在结尾重复重要规则

### 提示词最佳实践

#### ✅ 好的提示词特征

```python
def _get_article_stage_prompt(self) -> str:
    return """ARTICLE READING STAGE:

Your task: Guide student through reading and understanding the article.

CRITICAL: YOU MUST READ THE ARTICLE FIRST! DO NOT ask student to read before you do!

Instructions:
1. **FIRST**, YOU must read the COMPLETE article aloud (every word, don't skip or summarize)
2. **AFTER** you finish reading, say: "Now you try reading it."
3. Listen patiently while student reads (don't interrupt even if they pause)
...

REMEMBER: Always read the full article yourself BEFORE asking student to read!
"""
```

**特点:**
- ✅ 使用CRITICAL警告
- ✅ 加粗强调关键词
- ✅ 明确禁止性指令（DO NOT）
- ✅ 具体的操作步骤
- ✅ 结尾重复提醒

#### ❌ 不好的提示词

```python
def _get_article_stage_prompt(self) -> str:
    return """ARTICLE READING STAGE:

Guide student to read the article.
Read the article together.
Answer questions if needed.
"""
```

**问题:**
- ❌ 指令模糊
- ❌ 没有强调顺序
- ❌ 缺少示例
- ❌ 没有明确谁先读

## 扩展新阶段

### 步骤1: 在lesson_manager.py中添加提示词方法

```python
def _get_new_stage_prompt(self) -> str:
    """新阶段提示词"""
    return """NEW STAGE NAME:

Your task: [明确的任务描述]

CRITICAL: [关键注意事项]

Instructions:
1. **FIRST**, [第一步]
2. **THEN**, [第二步]
3. [后续步骤...]

Example:
Teacher: "[示例对话]"
Student: "[学生回应]"
Teacher: "[老师反馈]"

Tips:
- [教学技巧1]
- [教学技巧2]

REMEMBER: [重要提醒]
"""
```

### 步骤2: 注册到get_stage_prompt方法

```python
def get_stage_prompt(self, stage: str) -> str:
    """根据阶段名称获取对应的提示词"""
    stage_methods = {
        "vocabulary": self._get_vocabulary_stage_prompt,
        "article": self._get_article_stage_prompt,
        "question": self._get_question_stage_prompt,
        "review": self._get_review_stage_prompt,
        "new_stage": self._get_new_stage_prompt,  # 添加新阶段
    }

    method = stage_methods.get(stage)
    if method:
        return self._get_base_system_prompt() + "\n\n" + method()
    else:
        return self._get_tutor_system_prompt()
```

### 步骤3: 在app.py中添加触发消息

```python
# 在 tutor_websocket() 函数的阶段切换处理中
if msg_type == "stage_change":
    stage = data.get("stage", "vocabulary")
    stage_prompt = lesson_manager.get_stage_prompt(stage)

    # 更新会话
    await client.send_session_update({
        "instructions": stage_prompt,
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.5,
            "silence_duration_ms": 1500,
        },
    })

    await asyncio.sleep(0.3)

    # 添加新阶段的触发消息
    stage_messages = {
        "vocabulary": "Now begin teaching the vocabulary...",
        "article": "Now start the article reading stage...",
        "question": "Now begin the question practice...",
        "review": "Now start the review...",
        "new_stage": "Now begin the new stage. [具体指令]",  # 新阶段
    }

    trigger_msg = stage_messages.get(stage, f"Now start the {stage} stage.")
    await client.send_text_message(trigger_msg)
```

### 步骤4: 在前端tutor.html中添加按钮

```html
<button class="stage" data-stage="new_stage">🆕 New Stage</button>
```

### 步骤5: 在前端tutor.js中添加名称映射

```javascript
switchStage(stage) {
    // 更新按钮状态
    document.querySelectorAll('.stage').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.stage === stage);
    });

    // 发送切换消息
    this.ws.send(JSON.stringify({
        type: 'stage_change',
        stage: stage
    }));

    // 显示系统消息
    const stageNames = {
        'vocabulary': 'Vocabulary Teaching',
        'article': 'Article Reading',
        'question': 'Question Practice',
        'review': 'Lesson Review',
        'new_stage': 'New Stage Name'  // 添加新阶段
    };

    this.addMessage('system', `Switching to ${stageNames[stage]}...`);
}
```

---

## 按钮行为规范

### 三类按钮的职责划分

#### 1️⃣ Start Speaking / Stop - 麦克风控制按钮

**设计原则**: **只控制麦克风，不影响业务逻辑**

**Start Speaking**:
```javascript
async startRecording() {
    // ✅ 请求麦克风权限
    // ✅ 开始捕获音频
    // ✅ 持续发送音频数据到服务器
    // ✅ VAD 自动检测语音结束
    // ✅ 更新按钮状态
}
```

**Stop**:
```javascript
stopRecording() {
    // ✅ 停止音频捕获
    // ✅ 关闭麦克风设备
    // ✅ 释放音频资源
    // ⚠️ 不发送 commit_audio
    // ⚠️ 不触发任何AI响应
    // ✅ 更新按钮状态
}
```

**工作流程**:
```
用户点击 Start Speaking
  → 麦克风开启，持续发送音频
  → 用户说话
  → VAD检测到1.5秒静音
  → 自动触发AI响应

用户点击 Stop
  → 麦克风关闭
  → 音频流停止
  → 不触发AI响应（单纯静音）
```

#### 2️⃣ 阶段按钮 - 业务逻辑控制

**设计原则**: 控制教学流程，切换教学阶段

**实现要点**:
```javascript
switchStage(stage) {
    // 防止快速重复点击
    if (this.isStageChanging) return;
    this.isStageChanging = true;
    setTimeout(() => this.isStageChanging = false, 2000);

    // 发送阶段切换消息
    this.ws.send(JSON.stringify({
        type: 'switch_stage',
        stage: stage
    }));

    // 更新UI状态
    this.updateStageButtons(stage);
}
```

**后端处理**:
```python
# 1. 取消当前响应
await qwen_ws.cancel_response()
await asyncio.sleep(0.3)

# 2. 更新会话配置（新提示词 + VAD）
await qwen_ws.send_session_update(config)
await asyncio.sleep(0.1)

# 3. 清空音频缓冲
await qwen_ws.clear_audio_buffer()
await asyncio.sleep(0.2)

# 4. 发送阶段提示词（触发AI）
await qwen_ws.send_text_message(prompt)
```

#### 3️⃣ End Lesson - 课程结束按钮

**设计原则**: 完全重置状态，返回初始页面

**实现要点**:
```javascript
async endLesson() {
    // 1. 停止录音
    this.stopRecording();

    // 2. 关闭WebSocket
    if (this.ws) {
        this.ws.close();
        this.ws = null;
    }

    // 3. 停止音频播放
    if (this.audioContext) {
        this.audioContext.close();
    }

    // 4. 清理UI状态
    this.clearAllMessages();
    this.resetTimer();

    // 5. 返回首页
    window.location.href = '/';
}
```

### 常见错误和修复

❌ **错误**: Stop按钮发送 `commit_audio`
```javascript
// 错误做法
stopRecording() {
    this.stopCapture();
    this.ws.send(JSON.stringify({type: 'commit_audio'})); // ❌ 会触发AI
}
```

✅ **正确**: Stop按钮只静音
```javascript
// 正确做法
stopRecording() {
    this.stopCapture();
    // 什么都不发送，只是停止麦克风
}
```

❌ **错误**: End Lesson不清理资源
```javascript
// 错误做法
endLesson() {
    window.location.href = '/';  // ❌ 资源泄漏
}
```

✅ **正确**: End Lesson完全清理
```javascript
// 正确做法
endLesson() {
    this.cleanup();  // 先清理所有资源
    window.location.href = '/';  // 再跳转
}
```

---

## 阶段切换调试

### 调试工具

**1. 浏览器控制台日志**

前端会输出详细日志：
```
🔄 Switching to stage: article
⏳ Stage changing, please wait...
📤 Sent switch_stage message
📥 Received: stage_changed
✅ Stage switched to: article
```

**2. 服务端日志**

后端会输出阶段切换步骤：
```
🔄 Stage switch requested: article
✅ Current response cancelled
✅ VAD configuration updated (silence: 1500ms)
✅ Audio buffer cleared
📝 Stage prompt: Now start the article stage...
✅ Stage switch complete → article
```

### 常见问题排查

#### 问题: 点击按钮没有反应

**可能原因**:
1. 快速重复点击被防抖拦截
2. WebSocket连接断开
3. 按钮防护锁未释放

**排查步骤**:
```javascript
// 1. 检查防抖状态
console.log('isStageChanging:', this.isStageChanging);

// 2. 检查WebSocket状态
console.log('WebSocket state:', this.ws?.readyState);

// 3. 强制释放锁（调试用）
this.isStageChanging = false;
```

#### 问题: AI切换后没有主动开始

**可能原因**:
1. 触发消息没有发送
2. VAD配置被禁用
3. 提示词不够明确

**排查步骤**:
```python
# 1. 检查日志是否显示发送了提示词
logger.info(f"📝 Stage prompt: {prompt[:100]}...")

# 2. 确认VAD配置
logger.info(f"VAD config: {session_config['vad']}")

# 3. 检查提示词内容
print(lesson.get_stage_prompt('article'))
```

#### 问题: AI响应立即结束，没有内容

**可能原因**:
1. response被过早cancel
2. 多次点击导致状态混乱
3. 音频缓冲区有问题

**解决方案**:
```python
# handlers/stage_handler.py
async def handle_stage_switch(...):
    # 确保足够的等待时间
    await qwen_ws.cancel_response()
    await asyncio.sleep(0.3)  # 增加等待

    await qwen_ws.send_session_update(...)
    await asyncio.sleep(0.1)

    await qwen_ws.clear_audio_buffer()
    await asyncio.sleep(0.2)  # 确保清理完成

    await qwen_ws.send_text_message(...)
```

### 测试清单

- [ ] 单次点击阶段按钮正常切换
- [ ] 快速点击阶段按钮被防抖保护
- [ ] 切换后AI立即主动开始
- [ ] Start/Stop按钮不影响阶段切换
- [ ] End Lesson完全清理资源
- [ ] 浏览器控制台无错误
- [ ] 服务端日志显示完整流程

---

## 扩展开发

### 添加新的教学阶段

假设要添加一个"pronunciation"（发音练习）阶段。

### 步骤1: 在lesson_manager.py中添加提示词方法

```python
def get_stage_prompt(self, stage: str) -> str:
    """获取指定阶段的提示词"""
    prompts = {
        "vocabulary": self._get_vocabulary_prompt(),
        "article": self._get_article_prompt(),
        "questions": self._get_questions_prompt(),
        "review": self._get_review_prompt(),
        "pronunciation": self._get_pronunciation_prompt(),  # 新增
    }
    return prompts.get(stage, self._get_vocabulary_prompt())

def _get_pronunciation_prompt(self) -> str:
    """发音练习阶段提示词"""
    return """PRONUNCIATION PRACTICE STAGE:

Your task: Help student improve pronunciation of specific words.

Instructions:
1. Choose a word that student had difficulty with
2. Demonstrate clear pronunciation (slowly first, then normal speed)
3. Ask student to repeat
4. Listen carefully and provide specific feedback
5. If incorrect, explain what needs improvement
6. Practice 3-5 times until pronunciation is good

Example:
Teacher: "Let's work on 'indigenous'. Listen: in-DI-je-nous. Now you try."
Student: "Indigenous."
Teacher: "Good! The stress is on 'DI'. Try again: in-DI-je-nous."

CRITICAL: Be patient and encouraging. Pronunciation takes practice!
"""
```

### 步骤2: 在handlers/stage_handler.py中添加映射

无需修改，`get_stage_prompt()`会自动处理新阶段。

### 步骤3: 在routes/websocket_routes.py中添加触发消息（如果需要）

```python
# 通常不需要修改，除非需要特殊触发逻辑
```

### 步骤4: 在前端tutor.html中添加按钮

```html
<button class="stage" data-stage="pronunciation">🗣️ Pronunciation</button>
```

### 步骤5: 在前端tutor.js中添加名称映射

```javascript
const stageNames = {
    'vocabulary': 'Vocabulary Teaching',
    'article': 'Article Reading',
    'questions': 'Question Practice',
    'review': 'Lesson Review',
    'pronunciation': 'Pronunciation Practice'  // 新增
};
```

完成！新阶段已添加，无需修改核心逻辑。

---

## 连接优化

### WebSocket配置

```python
self.ws = await websockets.connect(
    QWEN_API_URL,
    extra_headers=headers,
    ping_interval=20,      # 心跳间隔（秒）
    ping_timeout=10,       # 心跳超时（秒）
    close_timeout=10,      # 关闭超时（秒）
    max_size=10 * 1024 * 1024,  # 最大消息10MB
    compression=None       # 禁用压缩提高稳定性
)
```

### 区域选择

根据环境变量`DASHSCOPE_REGION`自动选择API端点：

```python
API_ENDPOINTS = {
    "beijing": "wss://dashscope.aliyuncs.com/api-ws/v1/realtime",
    "singapore": "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime",
    "virginia": "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime",
}

DASHSCOPE_REGION = os.getenv("DASHSCOPE_REGION", "beijing").lower()
QWEN_API_URL = API_ENDPOINTS.get(DASHSCOPE_REGION) + f"?model={MODEL_NAME}"
```

### 日志优化

减少噪音，只记录关键事件：

```python
# 不记录频繁的音频消息
if msg_type == "input_audio_buffer.append":
    return  # 不记录
elif msg_type.startswith("response.audio"):
    return  # 不记录

# 记录其他事件
logger.info(f"📤 Client event: {msg_type}")
logger.info(f"📥 Qwen event: {msg_type}")
```

## 问题修复记录

### 问题1: 朗读文章被打断 (2026-01-18)

**现象:**
- 用户朗读长文章时中间有停顿
- VAD检测到静音后过早触发AI响应
- 导致用户朗读被打断

**根本原因:**
- `silence_duration_ms` 设置为800ms太短
- 用户朗读时的自然停顿超过800ms

**解决方案:**
```python
# app.py
"turn_detection": {
    "type": "server_vad",
    "threshold": 0.5,
    "silence_duration_ms": 1500,  # 从800ms增加到1500ms
}
```

**效果:**
- 用户有1.5秒的停顿时间
- 不会因短暂停顿被打断
- 更自然的对话体验

### 问题2: 阶段切换后等待用户先说 (2026-01-18)

**现象:**
- 用户点击阶段切换按钮
- AI更新了提示词但不主动开始
- 需要用户先说话才能触发AI

**根本原因:**
- 只发送了`session.update`更新配置
- 没有发送触发消息让AI主动开始

**解决方案:**
```python
# 1. 更新会话配置
await client.send_session_update({
    "instructions": stage_prompt,
    "turn_detection": {...},
})

# 2. 等待配置生效
await asyncio.sleep(0.3)

# 3. 发送明确的触发消息
stage_messages = {
    "vocabulary": "Now begin teaching the vocabulary...",
    "article": "Now start the article reading stage. Read the full article aloud first.",
    "question": "Now begin the question practice. Ask the first question.",
    "review": "Now start the review. Summarize what we learned today."
}
trigger_msg = stage_messages.get(stage)
await client.send_text_message(trigger_msg)
```

**效果:**
- 阶段切换后AI立即主动开始
- 明确告诉AI该做什么
- 用户不需要先说话

### 问题3: 文章阶段Teacher不先朗读 (2026-01-18)

**现象:**
- 切换到文章阶段后，AI让学生先朗读
- 与教学设计不符

**根本原因:**
- 提示词中的指令不够强调
- AI可能误解为让学生先读

**解决方案:**

1. **在提示词中强调:**
```python
def _get_article_stage_prompt(self) -> str:
    return """ARTICLE READING STAGE:

CRITICAL: YOU MUST READ THE ARTICLE FIRST! DO NOT ask student to read before you do!

Instructions:
1. **FIRST**, YOU must read the COMPLETE article aloud (every word)
2. **AFTER** you finish reading, say: "Now you try reading it."
...

REMEMBER: Always read the full article yourself BEFORE asking student to read!
"""
```

2. **在触发消息中明确:**
```python
stage_messages = {
    "article": "Now start the article reading stage. Read the full article aloud first.",
}
```

**效果:**
- AI切换到文章阶段后立即开始朗读完整文章
- 朗读完成后才让学生跟读
- 符合正确的教学流程

### 问题4: AI不按图片内容教学 (2026-01-15)

**现象:**
- 上传图片后生成课程计划
- 但AI没有根据图片内容进行教学

**根本原因:**
- Instructions中没有包含图片信息说明
- 提示词没有强调使用图片内容

**解决方案:**

在Instructions中添加：
```python
instructions = f"""You are a professional native English teacher...

=== LESSON PLAN (FOLLOW THIS CONTENT) ===
{lesson_plan}

=== IMAGES PROVIDED ===
The student has uploaded {len(image_urls)} image(s) showing the learning material.
You MUST teach based on the content visible in these images.
Refer to specific words, sentences, or dialogues from the images.

=== STUDENT'S REQUEST ===
{user_input_text if user_input_text else "Not specified"}
"""
```

在基础提示中强调：
```python
def _get_base_system_prompt(self) -> str:
    return """...
IMPORTANT INSTRUCTIONS:
- You MUST teach according to the content shown in the images.
- Refer to specific words, sentences, or dialogues from the images.
..."""
```

**效果:**
- AI根据图片中的具体内容进行教学
- 引用图片中的单词、句子、对话等
- 按照课程计划大纲逐步授课

### 问题5: AI不主动问候 (2026-01-15)

**现象:**
- 课程开始后需要学生先说话
- AI才会开始授课

**根本原因:**
- WebSocket连接建立后没有发送触发消息
- 提示词没有强调主动开始

**解决方案:**

1. **在提示词中强调:**
```python
IMPORTANT INSTRUCTIONS:
1. When the lesson starts, YOU MUST IMMEDIATELY greet the student warmly
   WITHOUT waiting for them to speak first.
2. After greeting, explain the lesson topic based on the lesson plan provided.
```

2. **连接后发送触发消息:**
```python
# 连接建立后
await client.send_text_message(
    "Start the lesson now. Greet the student and begin teaching."
)
```

**效果:**
- AI连接成功后立即主动问候
- 介绍课程并开始教学
- 用户不需要先说话

## 开发最佳实践

### 提示词设计

1. **使用层次结构**
   - 基础提示（角色、原则）
   - 阶段提示（具体任务）
   - 示例对话（行为模板）

2. **强调关键行为**
   - 使用CRITICAL/IMPORTANT标记
   - 使用**加粗**突出关键词
   - 明确禁止性指令（DO NOT）
   - 在结尾重复重要规则

3. **提供具体示例**
   - 包含Teacher和Student的对话
   - 展示期望的交互模式
   - 覆盖常见场景

4. **测试与迭代**
   - 实际测试AI行为
   - 观察是否符合预期
   - 根据反馈调整提示词

### 阶段切换

1. **三步法**
   - 第一步：更新会话配置
   - 第二步：等待配置生效（300ms）
   - 第三步：发送触发消息

2. **明确的触发消息**
   - 告诉AI做什么
   - 不要用模糊的指令
   - 每个阶段有专门的触发词

3. **前端同步**
   - 更新按钮激活状态
   - 显示系统消息
   - 提供视觉反馈

### VAD配置

1. **根据场景调整**
   - 对话场景：800-1000ms
   - 朗读场景：1500-2000ms
   - 提问场景：1000-1500ms

2. **提供配置接口**
   - 允许用户调整
   - 保存用户偏好
   - 不同阶段不同配置

### 错误处理

1. **连接错误**
   - 提供详细的错误信息
   - 区分不同错误类型
   - 给出解决建议

2. **API错误**
   - 记录完整的错误日志
   - 捕获特定错误码
   - 优雅降级处理

3. **用户错误**
   - 友好的错误提示
   - 引导用户正确操作
   - 提供帮助文档链接

### 日志记录

1. **分级记录**
   - INFO: 关键事件
   - DEBUG: 详细调试信息
   - ERROR: 错误和异常

2. **减少噪音**
   - 不记录频繁的音频消息
   - 合并相似事件
   - 使用emoji增强可读性

3. **结构化信息**
   - 统一的日志格式
   - 包含上下文信息
   - 便于搜索和分析

## 测试

### 模块结构测试

```bash
python test_structure.py
```

**功能**:
- ✅ 测试所有模块是否可正常导入
- ✅ 验证Flask应用是否正确创建
- ✅ 检查所有路由是否注册
- ✅ 测试课程内容解析功能
- ✅ 验证系统提示词生成

**预期输出**:
```
🧪 Module Imports............ ✅ PASSED
🧪 App Creation.............. ✅ PASSED
🧪 Lesson Parsing............ ✅ PASSED
🧪 System Prompt............. ✅ PASSED

Total: 4/4 tests passed 🎉
```

### 手动测试清单
```

功能：
- 检查API Key配置
- 测试当前区域连接
- 可选测试所有区域
- 提供诊断建议

### 阶段测试

```bash
python test_stages.py
```

功能：
- 测试各个阶段的提示词
- 验证阶段切换逻辑
- 检查触发消息

### 手动测试清单

- [ ] 测试页面连接正常
- [ ] AI外教页面加载正常
- [ ] 文本输入生成课程计划
- [ ] 图片上传并分析
- [ ] 课程开始后AI主动问候
- [ ] 词汇阶段按预期工作
- [ ] 文章阶段AI先朗读
- [ ] 问答阶段正常提问和反馈
- [ ] 复习阶段总结正确
- [ ] 手动切换阶段生效
- [ ] 朗读长文章不被打断
- [ ] 麦克风权限正常获取
- [ ] 音频播放正常
- [ ] 对话文字正确显示

## 部署

### 环境变量

```bash
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_REGION=beijing  # 或 singapore / virginia
```

### 生产环境建议

1. **使用HTTPS**
   - 麦克风需要安全上下文
   - 配置SSL证书

2. **负载均衡**
   - WebSocket持久连接
   - 使用支持WebSocket的负载均衡器

3. **监控和日志**
   - 监控连接状态
   - 记录使用统计
   - 设置告警规则

4. **备份和恢复**
   - 定期备份配置
   - 准备故障转移方案

## 参考资源

- [Qwen-Omni-Realtime官方文档](https://help.aliyun.com/zh/model-studio/realtime)
- [客户端事件参考](https://help.aliyun.com/zh/model-studio/client-events)
- [服务端事件参考](https://help.aliyun.com/zh/model-studio/server-events)
- [音色列表](https://help.aliyun.com/zh/model-studio/realtime#73b4de11eihd2)
- [模型定价](https://help.aliyun.com/zh/model-studio/models)

---

**最后更新**: 2026-01-18
**文档版本**: v1.0.0
