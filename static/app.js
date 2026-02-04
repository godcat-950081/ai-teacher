// Qwen-Omni-Realtime 前端应用
class QwenRealtimeApp {
    constructor() {
        this.ws = null;
        this.audioContext = null;
        this.mediaStream = null;
        this.audioWorkletNode = null;
        this.isRecording = false;
        this.isConnected = false;
        this.responseText = '';
        this.audioChunks = [];
        
        // 音频播放相关
        this.playbackContext = null;
        this.audioQueue = [];
        this.isPlaying = false;
        
        this.initUI();
        this.setupAudioVisualization();
    }
    
    initUI() {
        // 按钮
        this.connectBtn = document.getElementById('connectBtn');
        this.startRecordBtn = document.getElementById('startRecordBtn');
        this.stopRecordBtn = document.getElementById('stopRecordBtn');
        this.clearLogBtn = document.getElementById('clearLogBtn');
        
        // 状态
        this.connectionStatus = document.getElementById('connectionStatus');
        this.connectionText = document.getElementById('connectionText');
        this.recordingStatus = document.getElementById('recordingStatus');
        this.recordingText = document.getElementById('recordingText');
        
        // 设置
        this.voiceSelect = document.getElementById('voiceSelect');
        this.languageSelect = document.getElementById('languageSelect');
        this.vadMode = document.getElementById('vadMode');
        this.outputMode = document.getElementById('outputMode');
        
        // 日志和响应
        this.logContainer = document.getElementById('logContainer');
        this.responseTextEl = document.getElementById('responseText');
        
        // 事件监听
        this.connectBtn.addEventListener('click', () => this.toggleConnection());
        this.startRecordBtn.addEventListener('click', () => this.startRecording());
        this.stopRecordBtn.addEventListener('click', () => this.stopRecording());
        this.clearLogBtn.addEventListener('click', () => this.clearLog());
    }
    
    setupAudioVisualization() {
        const canvas = document.getElementById('audioVisualizer');
        this.canvasCtx = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth;
        canvas.height = 80;
        
        this.drawVisualization();
    }
    
    drawVisualization() {
        const canvas = document.getElementById('audioVisualizer');
        const ctx = this.canvasCtx;
        const width = canvas.width;
        const height = canvas.height;
        
        ctx.fillStyle = '#fff';
        ctx.fillRect(0, 0, width, height);
        
        if (this.isRecording && this.analyser) {
            const bufferLength = this.analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            this.analyser.getByteTimeDomainData(dataArray);
            
            ctx.lineWidth = 2;
            ctx.strokeStyle = '#667eea';
            ctx.beginPath();
            
            const sliceWidth = width / bufferLength;
            let x = 0;
            
            for (let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * height / 2;
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
                
                x += sliceWidth;
            }
            
            ctx.lineTo(width, height / 2);
            ctx.stroke();
        } else {
            // 绘制静止波形
            ctx.strokeStyle = '#ccc';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(0, height / 2);
            ctx.lineTo(width, height / 2);
            ctx.stroke();
        }
        
        requestAnimationFrame(() => this.drawVisualization());
    }
    
    async toggleConnection() {
        if (this.isConnected) {
            this.disconnect();
        } else {
            await this.connect();
        }
    }
    
    async connect() {
        try {
            this.log('正在连接到服务器...', 'info');
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.updateConnectionStatus(true);
                this.log('✅ WebSocket连接成功', 'success');
                
                this.connectBtn.textContent = '🔌 断开连接';
                this.connectBtn.classList.remove('success');
                this.connectBtn.classList.add('danger');
                this.startRecordBtn.disabled = false;
                
                // 发送会话配置
                this.sendSessionUpdate();
            };
            
            this.ws.onmessage = (event) => {
                this.handleServerMessage(JSON.parse(event.data));
            };
            
            this.ws.onerror = (error) => {
                this.log('❌ WebSocket错误: ' + error, 'error');
            };
            
            this.ws.onclose = () => {
                this.disconnect();
            };
            
        } catch (error) {
            this.log('❌ 连接失败: ' + error.message, 'error');
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        if (this.isRecording) {
            this.stopRecording();
        }
        
        // 清理音频队列和播放状态
        this.audioQueue = [];
        this.isPlaying = false;
        if (this.playbackContext) {
            this.playbackContext.close();
            this.playbackContext = null;
        }
        
        this.isConnected = false;
        this.updateConnectionStatus(false);
        this.log('🔌 已断开连接', 'info');
        
        this.connectBtn.textContent = '🔌 连接服务';
        this.connectBtn.classList.remove('danger');
        this.connectBtn.classList.add('success');
        this.startRecordBtn.disabled = true;
        this.stopRecordBtn.disabled = true;
    }
    
    sendSessionUpdate() {
        const modalities = this.outputMode.value.split(',');
        const vadModeValue = this.vadMode.value;
        const language = this.languageSelect.value;
        
        // 根据语言生成系统指令
        const instructions = {
            'zh': '你是一个友好的AI助手，请用中文回答问题。',
            'en': 'You are a friendly AI assistant. Please respond in English.',
            'ja': 'あなたは親切なAIアシスタントです。日本語で回答してください。',
            'ko': '당신은 친절한 AI 어시스턴트입니다. 한국어로 답변해주세요.',
            'es': 'Eres un asistente de IA amigable. Por favor responde en español.',
            'fr': 'Vous êtes un assistant IA amical. Veuillez répondre en français.'
        };
        
        const config = {
            modalities: modalities,
            voice: this.voiceSelect.value,
            input_audio_format: "pcm16",
            output_audio_format: "pcm16",
            instructions: instructions[language] || instructions['zh']
        };
        
        if (vadModeValue === "server_vad") {
            config.turn_detection = {
                type: "server_vad",
                threshold: 0.5,
                silence_duration_ms: 800
            };
        } else {
            config.turn_detection = null;
        }
        
        this.sendMessage({
            type: "session.update",
            session: config
        });
        
        this.log('📤 已发送会话配置', 'info');
    }
    
    async startRecording() {
        try {
            this.log('🎤 正在启动麦克风...', 'info');
            
            // 请求麦克风权限
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });
            
            // 创建音频上下文
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000
            });
            
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            
            // 创建分析器用于可视化
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 2048;
            source.connect(this.analyser);
            
            // 创建ScriptProcessor处理音频
            const bufferSize = 4096;
            this.scriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
            
            this.scriptProcessor.onaudioprocess = (e) => {
                if (!this.isRecording) return;
                
                const inputData = e.inputBuffer.getChannelData(0);
                const pcm16 = this.convertToPCM16(inputData);
                const base64Audio = this.arrayBufferToBase64(pcm16);
                
                // 发送音频数据到服务器
                this.sendMessage({
                    type: "audio",
                    audio: base64Audio
                });
            };
            
            source.connect(this.scriptProcessor);
            this.scriptProcessor.connect(this.audioContext.destination);
            
            this.isRecording = true;
            this.updateRecordingStatus(true);
            this.log('✅ 录音已开始', 'success');
            
            this.startRecordBtn.disabled = true;
            this.stopRecordBtn.disabled = false;
            
        } catch (error) {
            this.log('❌ 麦克风启动失败: ' + error.message, 'error');
        }
    }
    
    stopRecording() {
        this.isRecording = false;
        this.updateRecordingStatus(false);
        
        if (this.scriptProcessor) {
            this.scriptProcessor.disconnect();
            this.scriptProcessor = null;
        }
        
        if (this.analyser) {
            this.analyser.disconnect();
            this.analyser = null;
        }
        
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        // 如果是手动模式，发送提交信号
        if (this.vadMode.value === "manual") {
            this.sendMessage({
                type: "commit_audio"
            });
            this.log('📤 已提交音频缓冲区', 'info');
        }
        
        this.log('⏹️ 录音已停止', 'info');
        this.startRecordBtn.disabled = false;
        this.stopRecordBtn.disabled = true;
    }
    
    convertToPCM16(float32Array) {
        const buffer = new ArrayBuffer(float32Array.length * 2);
        const view = new DataView(buffer);
        
        for (let i = 0; i < float32Array.length; i++) {
            let s = Math.max(-1, Math.min(1, float32Array[i]));
            s = s < 0 ? s * 0x8000 : s * 0x7FFF;
            view.setInt16(i * 2, s, true);
        }
        
        return buffer;
    }
    
    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        
        return btoa(binary);
    }
    
    base64ToArrayBuffer(base64) {
        const binaryString = atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        return bytes.buffer;
    }
    
    async playAudio(base64Audio) {
        try {
            // 将音频数据加入队列
            this.audioQueue.push(base64Audio);
            
            // 如果没有在播放，开始播放
            if (!this.isPlaying) {
                this.playNextAudio();
            }
        } catch (error) {
            this.log('❌ 音频播放失败: ' + error.message, 'error');
        }
    }
    
    async playNextAudio() {
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            return;
        }
        
        this.isPlaying = true;
        const base64Audio = this.audioQueue.shift();
        
        try {
            const arrayBuffer = this.base64ToArrayBuffer(base64Audio);
            
            // 创建新的音频上下文（如果需要）
            if (!this.playbackContext) {
                this.playbackContext = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: 24000  // Qwen 输出的 PCM16 是 24000 Hz
                });
            }
            
            // 解码 PCM16 音频
            const audioBuffer = this.decodePCM16(arrayBuffer, this.playbackContext);
            const source = this.playbackContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.playbackContext.destination);
            
            // 播放结束后继续播放队列中的下一个
            source.onended = () => {
                this.playNextAudio();
            };
            
            source.start();
            
        } catch (error) {
            this.log('❌ 音频播放失败: ' + error.message, 'error');
            // 继续播放下一个
            this.playNextAudio();
        }
    }
    
    decodePCM16(arrayBuffer, audioContext) {
        // 解码 PCM16 格式（16位有符号整数，小端序）
        const view = new DataView(arrayBuffer);
        const numSamples = Math.floor(arrayBuffer.byteLength / 2);
        
        // 创建音频缓冲区，采样率 24000Hz（Qwen 输出采样率）
        const audioBuffer = audioContext.createBuffer(1, numSamples, 24000);
        const channelData = audioBuffer.getChannelData(0);
        
        for (let i = 0; i < numSamples; i++) {
            // 读取 2 个字节（小端序，16位有符号整数）
            const sample = view.getInt16(i * 2, true);
            
            // 归一化到 [-1, 1] 范围
            // 16位最大值是 32767 (2^15 - 1)
            channelData[i] = sample / 32768.0;
        }
        
        return audioBuffer;
    }
    
    decodePCM24(arrayBuffer, audioContext) {
        // 正确解码 PCM24 格式（24位有符号整数，小端序）
        const view = new DataView(arrayBuffer);
        const numSamples = Math.floor(arrayBuffer.byteLength / 3);
        
        // 创建音频缓冲区，采样率 24000Hz
        const audioBuffer = audioContext.createBuffer(1, numSamples, 24000);
        const channelData = audioBuffer.getChannelData(0);
        
        for (let i = 0; i < numSamples; i++) {
            // 读取 3 个字节（小端序）
            const byte1 = view.getUint8(i * 3);      // 低位字节
            const byte2 = view.getUint8(i * 3 + 1);  // 中位字节
            const byte3 = view.getUint8(i * 3 + 2);  // 高位字节
            
            // 组合成 24 位整数
            let value = (byte3 << 16) | (byte2 << 8) | byte1;
            
            // 处理符号位（24位有符号数）
            if (value & 0x800000) {
                value = value - 0x1000000;  // 转换为负数
            }
            
            // 归一化到 [-1, 1] 范围
            // 24位最大值是 8388607 (2^23 - 1)
            channelData[i] = value / 8388607.0;
        }
        
        return audioBuffer;
    }
    
    handleServerMessage(data) {
        const eventType = data.type;
        
        this.log(`📥 收到事件: ${eventType}`, 'info');
        
        switch (eventType) {
            case 'session.created':
            case 'session.updated':
                this.log('✅ 会话已配置', 'success');
                break;
                
            case 'input_audio_buffer.speech_started':
                this.log('🎙️ 检测到语音开始', 'info');
                break;
                
            case 'input_audio_buffer.speech_stopped':
                this.log('🎙️ 检测到语音停止', 'info');
                break;
                
            case 'response.text.delta':
                if (data.delta) {
                    this.responseText += data.delta;
                    this.updateResponseDisplay();
                }
                break;
                
            case 'response.text.done':
                this.log('💬 文本响应完成', 'response');
                break;
                
            case 'response.audio_transcript.delta':
                if (data.delta) {
                    this.responseText += data.delta;
                    this.updateResponseDisplay();
                }
                break;
                
            case 'response.audio.delta':
                if (data.delta) {
                    // 播放音频片段
                    this.playAudio(data.delta);
                }
                break;
                
            case 'response.audio.done':
                this.log('🔊 音频响应完成', 'response');
                break;
                
            case 'response.done':
                this.log('✅ 响应完成', 'success');
                this.responseText = '';
                break;
                
            case 'error':
                this.log('❌ 错误: ' + data.message, 'error');
                break;
                
            default:
                // 其他事件也记录
                break;
        }
    }
    
    updateResponseDisplay() {
        this.responseTextEl.textContent = this.responseText || '等待模型响应...';
    }
    
    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }
    
    updateConnectionStatus(connected) {
        if (connected) {
            this.connectionStatus.classList.add('connected');
            this.connectionText.textContent = '已连接';
        } else {
            this.connectionStatus.classList.remove('connected');
            this.connectionText.textContent = '未连接';
        }
    }
    
    updateRecordingStatus(recording) {
        if (recording) {
            this.recordingStatus.classList.add('recording');
            this.recordingText.textContent = '正在录音';
        } else {
            this.recordingStatus.classList.remove('recording');
            this.recordingText.textContent = '未录音';
        }
    }
    
    log(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        
        const time = new Date().toLocaleTimeString('zh-CN');
        entry.innerHTML = `<span class="log-time">[${time}]</span> ${message}`;
        
        this.logContainer.appendChild(entry);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
    }
    
    clearLog() {
        this.logContainer.innerHTML = '';
        this.log('日志已清空', 'info');
    }
}

// 初始化应用
const app = new QwenRealtimeApp();
