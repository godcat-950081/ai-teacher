# 区域选择指南

## 🌍 什么是区域（Region）？

Qwen-Omni-Realtime 服务部署在不同的地理区域，需要根据你的位置选择对应的区域以获得最佳性能。

## 📍 如何选择区域？

### 中国大陆用户

- **区域**: `beijing`（北京）
- **API 端点**: `wss://dashscope.aliyuncs.com/api-ws/v1/realtime`
- **获取 API Key**: [北京区域控制台](https://bailian.console.aliyun.com/?tab=model#/api-key)

### 国际/海外用户

- **区域**: `singapore`（新加坡）或 `virginia`（弗吉尼亚）
- **API 端点**: `wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime`
- **获取 API Key**: [国际区域控制台](https://bailian.console.aliyun.com/?tab=model#/api-key)

## ⚙️ 配置方法

### 方法 1: 环境变量（推荐）

```bash
# 中国大陆
export DASHSCOPE_API_KEY="your-api-key"
export DASHSCOPE_REGION="beijing"

# 国际用户
export DASHSCOPE_API_KEY="your-api-key"
export DASHSCOPE_REGION="singapore"
```

### 方法 2: 使用配置脚本

```bash
./setup.sh
```

### 方法 3: .env 文件

编辑 `.env` 文件：

```
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_REGION=beijing
```

## 🧪 测试连接

运行测试工具检查配置：

```bash
python test_connection.py
```

该工具会：

- ✅ 检查 API Key 是否设置
- ✅ 测试当前区域连接
- ✅ 可选：测试所有区域找到最佳连接
- ✅ 提供详细的诊断信息

## ❌ 常见错误

### 错误 1: 连接超时

```
❌ 连接超时 (>10秒)
```

**原因**:

- 网络问题
- 选择了错误的区域
- 防火墙阻止

**解决**:

1. 检查网络连接
2. 尝试更换区域
3. 检查防火墙设置

### 错误 2: HTTP 401 错误

```
❌ HTTP 错误: 401
```

**原因**:

- API Key 无效
- API Key 不匹配该区域

**解决**:

1. 检查 API Key 是否正确
2. 确认 API Key 来自对应的区域
3. 重新生成 API Key

### 错误 3: Keepalive ping timeout

```
ERROR: keepalive ping timeout; no close frame received
```

**原因**:

- 网络不稳定
- 长时间无数据传输

**解决**:

1. 检查网络稳定性
2. 代码已优化心跳检测（ping_interval=20）
3. 考虑更换区域

## 🔄 更换区域

如果当前区域不稳定，可以随时更换：

```bash
# 停止服务 (Ctrl+C)

# 更换区域
export DASHSCOPE_REGION="singapore"

# 重启服务
python app.py
```

## 📊 区域对比

| 区域      | 适用地区    | API 端点                    | 延迟 |
| --------- | ----------- | --------------------------- | ---- |
| beijing   | 中国大陆    | dashscope.aliyuncs.com      | 低   |
| singapore | 东南亚/澳洲 | dashscope-intl.aliyuncs.com | 中   |
| virginia  | 美洲/欧洲   | dashscope-intl.aliyuncs.com | 高   |

**注意**:

- 不同区域的 API Key 不通用
- 需要在对应区域的控制台申请 API Key
- 新加坡和弗吉尼亚使用相同的国际端点

## 🛠️ 高级配置

### 修改心跳间隔

如果网络不稳定，可以调整心跳参数（在 `app.py` 中）：

```python
self.ws = await websockets.connect(
    QWEN_API_URL,
    extra_headers=headers,
    ping_interval=15,  # 更频繁 (默认: 20)
    ping_timeout=15,   # 更长超时 (默认: 10)
)
```

### 禁用压缩

已默认禁用压缩以提高稳定性：

```python
compression=None  # 禁用压缩
```

## 📞 获取帮助

如果遇到问题：

1. 运行 `python test_connection.py` 诊断
2. 查看服务日志获取详细错误
3. 检查 [官方文档](https://help.aliyun.com/zh/model-studio/realtime)
4. 参考 README.md 中的常见问题

## 🎯 快速决策

**我应该用哪个区域？**

```
你在哪里？
├─ 中国大陆 → beijing
├─ 港澳台 → singapore
├─ 亚洲其他 → singapore
├─ 欧洲 → virginia
└─ 美洲 → virginia
```

**不确定？** 运行 `python test_connection.py` 测试所有区域！
