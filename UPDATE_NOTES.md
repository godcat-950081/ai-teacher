# 🚀 代码更新说明

## 主要改进

### 1. ✅ 区域选择支持

- 新增 `DASHSCOPE_REGION` 环境变量
- 支持三个区域：`beijing`（北京）、`singapore`（新加坡）、`virginia`（弗吉尼亚）
- 自动根据区域选择正确的 API 端点

### 2. 🔧 连接稳定性优化

- 优化心跳检测：`ping_interval=20`（更频繁）
- 增加超时配置：`close_timeout=10`
- 禁用压缩提高稳定性：`compression=None`
- 增大消息大小限制：`max_size=10MB`

### 3. 📝 日志改进

- 减少噪音：音频消息不再记录每一条
- 更详细的错误信息
- 添加 emoji 图标便于识别
- 区分连接错误类型（超时、权限、网络等）

### 4. 🛠️ 新增工具

#### `test_connection.py` - 连接测试工具

```bash
python test_connection.py
```

功能：

- 检查 API Key 配置
- 测试当前区域连接
- 可选：测试所有区域
- 提供诊断建议

#### `setup.sh` - 快速配置脚本

```bash
./setup.sh
```

功能：

- 交互式选择区域
- 输入 API Key
- 自动生成 .env 配置

#### `REGION_GUIDE.md` - 区域选择指南

详细的区域配置说明文档

### 5. 📄 文档更新

- README.md 添加区域配置说明
- 更新常见问题（连接问题排查）
- .env.example 添加区域配置示例

## 使用方法

### 快速开始（使用配置脚本）

```bash
# 1. 运行配置脚本
./setup.sh

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖（如果还没安装）
pip install -r requirements.txt

# 4. 测试连接
python test_connection.py

# 5. 启动服务
python app.py
```

### 手动配置

```bash
# 1. 设置环境变量
export DASHSCOPE_API_KEY="your-api-key"
export DASHSCOPE_REGION="beijing"  # 或 singapore / virginia

# 2. 测试连接
python test_connection.py

# 3. 启动服务
python app.py
```

## 针对你的问题

### 问题：连接不稳定，频繁出现 "keepalive ping timeout"

### 原因分析

1. 你使用的是北京的 API Key
2. 可能网络到北京端点不稳定
3. WebSocket 长连接维持困难

### 解决方案

#### 方案 1: 先测试连接（推荐）

```bash
python test_connection.py
```

这会告诉你：

- 当前配置是否能连接
- 哪个区域连接最稳定

#### 方案 2: 如果北京连接不稳定

**检查你的 API Key 是从哪个区域申请的：**

访问 https://help.aliyun.com/zh/model-studio/get-api-key

- 如果是"北京"区域的 Key → 保持 `DASHSCOPE_REGION=beijing`
- 如果是"新加坡"或"国际"区域的 Key → 改为 `DASHSCOPE_REGION=singapore`

**重要**: API Key 和区域必须匹配！

#### 方案 3: 如果在中国大陆且网络不稳定

```bash
# 保持使用北京区域，但已优化连接参数
export DASHSCOPE_REGION="beijing"
python app.py
```

代码已自动优化：

- 心跳间隔从 30s → 20s
- 禁用压缩减少错误
- 更好的错误处理和重连

#### 方案 4: 如果你在海外

```bash
# 切换到国际端点
export DASHSCOPE_REGION="singapore"
python app.py
```

## 新的启动信息

启动时会显示：

```
======================================================================
🚀 Qwen-Omni-Realtime Demo Server
======================================================================
✅ API Key configured: True
🌍 Region: BEIJING
🔗 API Endpoint: wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen3-omni-flash-realtime
🌐 Server starting on http://localhost:5000
======================================================================

💡 提示：
   - 如在中国大陆，使用北京区域的 API Key
   - 如在海外，设置 DASHSCOPE_REGION=singapore 或 virginia
   - 示例: export DASHSCOPE_REGION=singapore
```

## 日志改进示例

### 之前

```
INFO:__main__:Received from client: audio
INFO:__main__:Received from client: audio
INFO:__main__:Received from client: audio
...（大量重复）
```

### 现在

```
INFO:__main__:📤 Client event: session.update
INFO:__main__:📥 Qwen event: session.created
INFO:__main__:📤 Client event: commit_audio
INFO:__main__:📥 Qwen event: response.done
```

音频消息不再显示，日志清晰可读！

## 下一步建议

1. **立即测试**:

   ```bash
   python test_connection.py
   ```

2. **根据测试结果**:

   - ✅ 如果北京连接成功 → 继续使用
   - ❌ 如果北京连接失败 → 检查 API Key 区域，考虑切换

3. **查看详细指南**:
   ```bash
   cat REGION_GUIDE.md
   ```

## 文件清单

新增/修改的文件：

- ✅ `app.py` - 优化连接和日志
- ✅ `test_connection.py` - 连接测试工具
- ✅ `setup.sh` - 配置脚本
- ✅ `REGION_GUIDE.md` - 区域指南
- ✅ `README.md` - 更新文档
- ✅ `.env.example` - 添加区域配置
- ✅ `UPDATE_NOTES.md` - 本文档
