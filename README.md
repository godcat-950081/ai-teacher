# AI English Tutor 🎓

基于通义千问实时多模态（Qwen-Omni-Realtime）的智能英语外教应用，支持实时语音互动教学。

## ✨ 功能特性

- 🎯 **实时语音对话** - 自然流畅的语音交互，像和真人外教对话
- 📚 **智能课程生成** - 输入文本或上传图片，AI自动生成个性化教学计划
- 🎓 **专业教学流程** - 词汇→文章→练习→复习，循序渐进
- 🔄 **灵活阶段切换** - 可随时跳转到任意教学阶段
- 🎙️ **发音纠正** - AI实时纠正发音，提供标准示范
- 📊 **可视化界面** - 实时对话记录、音频波形、课程计时

## 🚀 快速开始

### 系统要求

- Python 3.8+
- 阿里云百炼 API Key（[获取地址](https://bailian.console.aliyun.com/?tab=model#/api-key)）
- 带麦克风的设备
- Chrome/Edge/Safari 浏览器

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-teacher
```

2. **创建虚拟环境**
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置API Key**

根据你的地理位置选择区域：

| 地理位置 | 区域设置 | API端点 |
|---------|---------|---------|
| 🇨🇳 中国大陆 | `beijing` | dashscope.aliyuncs.com |
| 🌏 港澳台/东南亚 | `singapore` | dashscope-intl.aliyuncs.com |
| 🌍 欧美 | `virginia` | dashscope-intl.aliyuncs.com |

创建 `.env` 文件：
```env
DASHSCOPE_API_KEY=your-api-key-here
DASHSCOPE_REGION=beijing  # 根据你的位置选择
```

5. **启动服务**
```bash
python app.py
```

6. **访问应用**
打开浏览器访问：http://localhost:5000

## 📖 使用指南

### 创建课程

#### 方式一：文本输入

使用结构化格式输入课程内容：

```
单词：indigenous, fluent, gesture
文章：Gordon lives in Sweden and his wife Chris is learning Swedish...
练习：
1. Where does Gordon live?
2. What language is Chris learning?
```

或简单描述主题：
- "练习餐厅点餐英语"
- "学习工作面试常用表达"

#### 方式二：上传图片

上传教材图片，AI自动识别内容并生成教学计划。

### 教学阶段

#### 📚 Vocabulary（词汇）
AI逐个教授单词发音、含义和用法，学生跟读练习。

#### 📖 Article（文章）
AI先完整朗读文章，然后学生跟读，最后回答理解问题。

#### ❓ Questions（练习）
AI提问，学生回答（不是重复问题），AI给予反馈。

#### ✅ Review（复习）
总结本节课内容，巩固重点知识。

### 使用技巧

💡 **最佳实践**
- 在安静环境中使用
- 说话清晰，语速适中
- 用完整句子回答问题
- 不要害怕犯错

⚠️ **常见错误**
```
老师："Where does Gordon live?"
学生："Where does Gordon live?"  ❌ 不要重复问题
学生："He lives in Sweden."      ✅ 直接回答
```

## ❓ 常见问题

### Q: 连接失败或频繁断开？
1. 检查区域配置是否正确（中国大陆用 `beijing`）
2. 确认API Key来自对应区域的控制台
3. 检查网络连接是否稳定

### Q: HTTP 401错误？
API Key无效或区域不匹配，请重新检查配置。

### Q: 听不到AI老师的声音？
1. 检查浏览器音量设置
2. 查看浏览器控制台是否有错误
3. 确认麦克风权限已授予

### Q: AI朗读时中途停止？
这是正常的，AI会自动检测1.5秒的停顿。朗读长文章时的自然停顿不会触发响应。

### Q: 阶段切换后AI没反应？
点击阶段切换按钮后，AI会自动开始。如果没有反应，可以说"Hello"或"Start"触发。

## 📁 项目结构

```
ai-teacher/
├── app.py                      # 主应用入口
├── lesson_manager.py           # 课程数据模型
├── services/                   # 业务服务层
│   ├── qwen_client.py         # Qwen API客户端
│   └── lesson_service.py      # 课程准备服务
├── handlers/                   # 业务处理层
│   └── stage_handler.py       # 阶段切换处理
├── routes/                     # 路由层
│   ├── lesson_routes.py       # 课程管理API
│   └── websocket_routes.py    # WebSocket通信
├── templates/                  # HTML模板
│   ├── index.html             # 首页
│   └── tutor.html             # 教学页面
└── static/                     # 前端JS
    ├── app.js
    └── tutor.js
```

## 🛠️ 技术栈

- **后端**: Flask + Flask-Sock + WebSocket
- **前端**: Vanilla JavaScript + Web Audio API
- **AI模型**: Qwen3-Omni-Flash-Realtime
- **音频**: PCM16 (16kHz输入 / 24kHz输出)

## 📚 更多资源

- [开发文档](DEVELOPMENT.md) - 详细的技术文档和开发指南
- [官方文档](https://help.aliyun.com/zh/model-studio/realtime) - 阿里云实时API文档
- [测试脚本](test_structure.py) - 验证代码结构的测试工具

## 📝 更新日志

### v1.3.0 (2026-02-05)
- ✅ 代码重构：模块化架构，提高可维护性
- ✅ 优化文档：合并为README.md + DEVELOPMENT.md

### v1.2.0 (2026-01-18)
- ✅ VAD静音检测优化：800ms → 1500ms
- ✅ 阶段切换立即生效：AI主动开始新阶段
- ✅ 文章阶段：AI先完整朗读

### v1.1.0 (2026-01-15)
- ✅ AI主动问候功能
- ✅ 基于图片内容授课
- ✅ 优化提示词设计

---

**当前版本**: v1.3.0
**最后更新**: 2026-02-05
