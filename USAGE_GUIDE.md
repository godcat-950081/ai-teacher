# AI英语外教 - 阶段切换功能使用指南

## 快速开始

### 1. 启动服务器

```bash
cd /home/lz/works/ai-teacher
python app.py
```

### 2. 打开浏览器

访问：http://localhost:5000/tutor

### 3. 创建课程

在左侧输入框中输入课程内容，使用以下格式：

```
单词:
eyebrow - 眉毛
gesture - 手势
nod - 点头

文章:
On her first day in Micronesia, Lisa thought people were ignoring her requests. When she asked for directions, people raised their eyebrows instead of speaking. Later, she learned that raising eyebrows means "yes" in Micronesian culture. This gesture confused her because in her country, people nod their heads to show agreement.

练习:
1. How do people show yes in Micronesia?
2. Why was Lisa confused?
3. What does a nod mean in most countries?
```

点击"Create Lesson"按钮。

### 4. 开始上课

点击"Start Lesson"按钮，AI老师会主动问候并开始授课。

### 5. 使用阶段切换功能

课程开始后，在对话区下方会出现四个阶段按钮：

- **📚 Vocabulary** - 词汇教学阶段
- **📖 Article** - 文章阅读阶段
- **❓ Questions** - 问答练习阶段
- **✅ Review** - 复习总结阶段

#### 自动模式（推荐新手）

不点击任何按钮，让AI按照默认流程自动进行：

1. 首先教授词汇
2. 然后引导阅读文章
3. 接着练习回答问题
4. 最后进行总结

#### 手动切换（适合自主学习）

**场景1：跳过词汇**
如果你已经认识这些单词，可以直接点击"📖 Article"跳到文章阅读。

**场景2：重复练习**
如果问答练习不太好，可以再次点击"❓ Questions"重新练习。

**场景3：快速结束**
任何时候都可以点击"✅ Review"进入总结，然后结束课程。

**场景4：回到某个阶段**
比如复习时想再看一遍文章，点击"📖 Article"即可。

## 阶段详细说明

### 📚 Vocabulary（词汇教学）

**AI会做什么：**

1. 逐个教授单词
2. 解释简单含义
3. 让学生跟读
4. 提供反馈（Good! / Try again）
5. 每个词练习2-3次

**你应该做什么：**

- 认真听取发音
- 跟读单词
- 如有疑问随时询问

**示例对话：**

```
Teacher: "First word: eyebrow. It means the hair above your eye. Please repeat: eyebrow."
Student: "Eyebrow."
Teacher: "Perfect! Next word: gesture. It means a movement with your hands or body. Please repeat: gesture."
Student: "Gesture."
Teacher: "Good! Any questions about the vocabulary?"
```

### 📖 Article（文章阅读）

**AI会做什么：**

1. **先朗读**整篇文章（不会跳过）
2. 让学生跟读
3. 询问理解情况
4. 回答学生的问题
5. 练习困难的部分

**你应该做什么：**

- 先听老师完整朗读
- 然后自己朗读
- 主动提出不理解的地方
- 练习困难的句子

**示例对话：**

```
Teacher: "Let me read the article first: On her first day in Micronesia, Lisa thought people were ignoring her requests... [完整朗读]. Now you try reading it."
Student: [朗读文章]
Teacher: "Excellent reading! Do you understand the story? Any difficult words?"
Student: "What does 'ignoring' mean?"
Teacher: "'Ignoring' means not paying attention to someone. Let's practice that sentence again."
```

### ❓ Questions（问答练习）

**AI会做什么：**

1. 提出问题
2. 听取学生的**回答**（不是重复问题）
3. 给予反馈
4. 每个问题练习2-3次

**你应该做什么：**

- **回答问题**，不要只是重复问题
- 用完整的句子回答
- 不确定时可以尝试，老师会纠正

**示例对话：**

```
Teacher: "Now answer this question: How do people show yes in Micronesia?"
Student: "They raise their eyebrows."
Teacher: "Excellent answer! Next question: Why was Lisa confused?"
Student: "Because people raised eyebrows instead of nodding."
Teacher: "That's right! Good job!"
```

**❌ 错误示范：**

```
Teacher: "How do people show yes in Micronesia?"
Student: "How do people show yes in Micronesia?"  // 不要只是重复问题
```

**✅ 正确示范：**

```
Teacher: "How do people show yes in Micronesia?"
Student: "They raise their eyebrows."  // 直接回答问题
```

### ✅ Review（复习总结）

**AI会做什么：**

1. 简要总结今天学到的内容
2. 询问最后的问题
3. 给予鼓励

**你应该做什么：**

- 听取总结
- 提出任何剩余问题
- 接受鼓励，继续学习

**示例对话：**

```
Teacher: "Today we learned words like 'eyebrow' and 'gesture', read about cultural differences in Micronesia, and practiced answering questions. Any final questions?"
Student: "No, thank you!"
Teacher: "Excellent work today! Keep practicing your reading!"
```

## 按钮使用技巧

### 激活状态

点击某个阶段按钮后，该按钮会变成**深蓝色加粗**，表示当前处于该阶段。

### 何时切换

建议在以下时机切换阶段：

- ✅ 完成当前阶段的练习
- ✅ AI询问"Any questions?"之后
- ❌ 避免在AI说话中途切换

### 切换效果

点击按钮后：

1. 对话区显示："Switching to: [阶段名称]"
2. AI立即切换到新阶段的教学模式
3. AI会开始新阶段的内容

## 常见问题

**Q: 必须按顺序进行每个阶段吗？**
A: 不必须。你可以根据需要自由切换，但建议新手按顺序学习。

**Q: 可以跳过某个阶段吗？**
A: 可以。比如已经掌握词汇，可以直接点击"Article"。

**Q: 可以重复某个阶段吗？**
A: 可以。任何时候点击对应按钮即可重新进入该阶段。

**Q: 阶段按钮什么时候显示？**
A: 点击"Start Lesson"开始课程后，按钮才会显示。

**Q: 切换阶段后会丢失之前的对话记录吗？**
A: 不会。所有对话都会保留在对话区。

**Q: AI不响应阶段切换怎么办？**
A: 确保WebSocket已连接（对话区显示"Connected to AI English Tutor"），然后再次点击按钮。

## 开发者信息

如需添加新的教学阶段，请参考：`STAGE_MANAGEMENT.md`
