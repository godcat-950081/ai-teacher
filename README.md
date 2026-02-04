# Qwen-Omni-Realtime Demo

通义千问实时多模态（Qwen-Omni-Realtime）演示程序，支持实时音视频对话。

## 功能特性

- ✅ 实时语音对话
- ✅ 支持 VAD（语音活动检测）自动模式
- ✅ 支持手动录音模式
- ✅ 音频可视化
- ✅ 多种音色选择
- ✅ 实时文本和音频响应
- ✅ 简洁易用的 Web 界面

## 环境要求

- Python 3.8+
- 已有虚拟环境 `venv`
- 阿里云百炼 API Key

## 快速开始

### 1. 激活虚拟环境

```bash
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key 和区域

**获取 API Key：** 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/?tab=model#/api-key)

**重要提示：根据你的地理位置选择对应的区域！**

#### 方式一：使用环境变量（推荐）

**如果你在中国大陆：**

```bash
export DASHSCOPE_API_KEY="your-api-key-here"
export DASHSCOPE_REGION="beijing"
```

**如果你在海外：**

```bash
export DASHSCOPE_API_KEY="your-api-key-here"
export DASHSCOPE_REGION="singapore"  # 或 virginia
```

Windows 用户：

```cmd
set DASHSCOPE_API_KEY=your-api-key-here
set DASHSCOPE_REGION=beijing
```

#### 方式二：使用 .env 文件

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
# 然后编辑 .env 文件
```

### 4. 启动服务

```bash
python app.py
```

### 5. 访问测试页面

打开浏览器访问：http://localhost:5000

## 使用说明

### 基本操作

1. **连接服务**：点击"连接服务"按钮建立 WebSocket 连接
2. **配置设置**：选择音色、VAD 模式和输出格式
3. **开始录音**：点击"开始录音"按钮开始说话
4. **停止录音**：在手动模式下，点击"停止录音"提交音频

### VAD 模式说明

- **自动检测 (VAD)**：服务端自动检测语音起止，适合连续对话
- **手动模式**：需要手动点击停止录音来提交音频，适合精确控制

### 音色选择

支持多种音色，包括：

- 芊悦 (Cherry) - 阳光积极、亲切自然
- 苏瑶 (Serena) - 温柔小姐姐
- 晨煦 (Ethan) - 阳光温暖
- 千雪 (Chelsie) - 二次元虚拟女友
- 茉兔 (Momo) - 撒娇搞怪
- 十三 (Vivian) - 拽拽可爱

更多音色请参考：[音色列表](https://help.aliyun.com/zh/model-studio/realtime#73b4de11eihd2)

## 项目结构

```
ai-teacher/
├── app.py                  # Flask后端服务
├── requirements.txt        # Python依赖
├── README.md              # 项目文档
├── .env.example           # 环境变量示例
├── templates/
│   └── index.html         # 前端页面
├── static/
│   └── app.js             # 前端JavaScript
└── venv/                  # 虚拟环境（已存在）
```

## API 参考

### 支持的模型

- `qwen3-omni-flash-realtime` (稳定版)
- `qwen3-omni-flash-realtime-2025-12-01` (快照版)
- `qwen3-omni-flash-realtime-2025-09-15` (快照版)

### 支持的语言

中文、英语、法语、德语、俄语、意大利语、西班牙语、葡萄牙语、日语、韩语

### API 地址

- 中国内地（北京）：`wss://dashscope.aliyuncs.com/api-ws/v1/realtime`
- 国际（新加坡）：`wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime`

## 常见问题

### Q: 连接不稳定或频繁断开？

A:

1. **检查区域配置**：确保使用正确的区域
   - 中国大陆：`DASHSCOPE_REGION=beijing`
   - 海外：`DASHSCOPE_REGION=singapore` 或 `virginia`
2. **检查 API Key**：确保使用对应区域的 API Key
   - 北京区域需要北京的 API Key
   - 新加坡/弗吉尼亚需要国际区域的 API Key
3. **网络问题**：检查防火墙和代理设置
4. **查看日志**：运行时查看控制台的详细错误信息

### Q: 如何选择正确的区域？

A:

- **中国大陆用户**：使用 `beijing`
- **港澳台用户**：建议使用 `singapore`
- **其他国际用户**：使用 `singapore` 或 `virginia`

注意：不同区域需要在对应地域申请 API Key！

### Q: 浏览器提示麦克风权限被拒绝？

A: 请在浏览器设置中允许网站访问麦克风权限。

### Q: 连接失败怎么办？

A:

1. 确认已设置 `DASHSCOPE_API_KEY` 环境变量
2. 检查网络连接
3. 查看控制台日志获取详细错误信息

### Q: 没有声音输出？

A:

1. 确认选择了"文本+音频"输出模式
2. 检查浏览器音量设置
3. 查看浏览器控制台是否有音频播放错误

### Q: VAD 模式下没有自动响应？

A: VAD 模式需要检测到明显的语音停顿才会触发响应，可以尝试：

1. 说话后停顿 1-2 秒
2. 调整 VAD 阈值（目前默认为 0.5）
3. 切换到手动模式

## 技术架构

### 后端

- **Flask**：Web 框架
- **Flask-Sock**：WebSocket 支持
- **websockets**：异步 WebSocket 客户端

### 前端

- **原生 JavaScript**：无框架依赖
- **Web Audio API**：音频录制和播放
- **Canvas API**：音频可视化
- **WebSocket API**：实时通信

## 计费说明

Qwen-Omni-Realtime 根据不同模态的 Token 数计费：

- 新用户有免费额度（100 万 Token，90 天有效）
- 详细计费规则请参考：[模型列表](https://help.aliyun.com/zh/model-studio/models)

## 参考文档

- [Qwen-Omni-Realtime 官方文档](https://help.aliyun.com/zh/model-studio/realtime)
- [客户端事件参考](https://help.aliyun.com/zh/model-studio/client-events)
- [服务端事件参考](https://help.aliyun.com/zh/model-studio/server-events)

## 开发计划

- [ ] 添加图片输入支持（视频通话）
- [ ] 添加会话历史记录
- [ ] 支持多语言切换
- [ ] 添加更多音频格式支持
- [ ] 优化音频播放体验

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎提交 Issue。
