# 教学阶段管理功能说明

## 功能概述

现在AI英语外教支持动态切换教学阶段，每个阶段使用独立的提示词，方便未来扩展更多教学阶段。

## 已实现的阶段

### 1. Vocabulary（词汇教学）

- **功能**：教授词汇的含义和发音
- **流程**：
  1. 介绍单词和简单释义
  2. 要求学生跟读
  3. 提供反馈
  4. 每个词练习2-3次

### 2. Article（文章阅读）

- **功能**：引导学生阅读和理解文章
- **流程**：
  1. 老师先完整朗读文章
  2. 学生跟读
  3. 老师询问理解情况
  4. 回答学生问题
  5. 练习困难部分

### 3. Question（问答练习）

- **功能**：练习回答问题（非复述）
- **流程**：
  1. 提出问题
  2. 学生回答（不是重复问题）
  3. 给予反馈
  4. 每个问题练习2-3次

### 4. Review（复习总结）

- **功能**：总结课程内容
- **流程**：
  1. 简要总结所学内容
  2. 询问最后问题
  3. 积极鼓励

## 技术实现

### 后端（lesson_manager.py）

#### 新增方法

```python
# 获取基础系统提示（适用于所有阶段）
lesson_manager._get_base_system_prompt() -> str

# 获取各阶段提示词
lesson_manager._get_vocabulary_stage_prompt() -> str
lesson_manager._get_article_stage_prompt() -> str
lesson_manager._get_question_stage_prompt() -> str
lesson_manager._get_review_stage_prompt() -> str

# 获取完整系统提示（所有阶段）
lesson_manager._get_tutor_system_prompt() -> str

# 根据阶段名称获取对应提示词（基础提示 + 阶段提示）
lesson_manager.get_stage_prompt(stage: str) -> str
```

#### 使用示例

```python
# 获取词汇阶段提示词
vocabulary_prompt = lesson_manager.get_stage_prompt('vocabulary')

# 获取文章阶段提示词
article_prompt = lesson_manager.get_stage_prompt('article')

# 获取问答阶段提示词
question_prompt = lesson_manager.get_stage_prompt('question')

# 获取复习阶段提示词
review_prompt = lesson_manager.get_stage_prompt('review')
```

### 后端（app.py）

#### WebSocket 消息处理

新增 `stage_change` 消息类型处理：

```python
{
    "type": "stage_change",
    "stage": "vocabulary"  # 可选: vocabulary, article, question, review
}
```

服务器收到此消息后会：

1. 获取对应阶段的提示词
2. 更新会话配置
3. 发送消息触发AI开始新阶段

### 前端（tutor.html + tutor.js）

#### UI 组件

在教学界面添加了阶段切换按钮：

- 📚 Vocabulary
- 📖 Article
- ❓ Questions
- ✅ Review

按钮样式：

- 默认：蓝色
- 悬停：深蓝色
- 激活：更深蓝色，加粗

#### JavaScript 方法

```javascript
// 切换教学阶段
tutor.switchStage(stage);

// 参数:
//   stage: 'vocabulary' | 'article' | 'question' | 'review'

// 功能:
//   1. 更新按钮激活状态
//   2. 通过 WebSocket 发送 stage_change 消息
//   3. 在对话区显示系统消息
```

## 扩展新阶段

### 步骤 1: 在 lesson_manager.py 中添加新阶段提示词

```python
def _get_new_stage_prompt(self) -> str:
    """新阶段提示词"""
    return """NEW STAGE:

Your task: [描述任务]

Instructions:
1. [步骤1]
2. [步骤2]
...

Example:
Teacher: "[示例对话]"
Student: "[学生回应]"
Teacher: "[老师反馈]"
"""
```

### 步骤 2: 更新 get_stage_prompt 方法

```python
def get_stage_prompt(self, stage: str) -> str:
    stage_methods = {
        "vocabulary": self._get_vocabulary_stage_prompt,
        "article": self._get_article_stage_prompt,
        "question": self._get_question_stage_prompt,
        "review": self._get_review_stage_prompt,
        "new_stage": self._get_new_stage_prompt,  # 添加新阶段
    }
    # ... 其余代码
```

### 步骤 3: 在前端 tutor.html 添加按钮

```html
<button class="stage" data-stage="new_stage">🆕 New Stage</button>
```

### 步骤 4: 在前端 tutor.js 更新阶段名称映射

```javascript
const stageNames = {
  vocabulary: "Vocabulary Teaching",
  article: "Article Reading",
  question: "Question Practice",
  review: "Lesson Review",
  new_stage: "New Stage Name", // 添加新阶段
};
```

## 使用场景

### 场景 1: 按顺序教学（自动）

不需要手动切换，AI 会按照课程计划自动进行所有阶段。

### 场景 2: 跳过某些阶段

如果学生已经掌握词汇，可以直接点击"📖 Article"按钮跳到文章阅读。

### 场景 3: 重复某个阶段

如果学生在问答环节表现不佳，可以再次点击"❓ Questions"按钮重新练习。

### 场景 4: 提前结束

任何时候都可以点击"✅ Review"按钮进入总结阶段，然后结束课程。

## 优势

1. **模块化**：每个阶段的提示词独立，易于维护和修改
2. **可扩展**：添加新阶段只需修改几处代码
3. **灵活性**：用户可以自由控制教学流程
4. **清晰性**：每个阶段有明确的教学目标和流程
5. **可测试**：每个阶段可以独立测试

## 注意事项

1. 阶段切换只在课程进行中（WebSocket 连接后）可用
2. 切换阶段会立即更新 AI 的行为模式
3. 建议在完成当前阶段后再切换，避免中断教学流程
4. 所有阶段都保持"简短响应"原则（1-2句话）

## 测试

运行测试脚本验证功能：

```bash
python test_stages.py
```

测试内容：

- 各阶段提示词获取
- 无效阶段错误处理
- 完整系统提示生成
