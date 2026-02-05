// AI English Tutor - Frontend Application
class AIEnglishTutor {
    constructor() {
        this.lessonId = null;
        this.ws = null;
        this.isRecording = false;
        this.audioContext = null;
        this.mediaStream = null;
        this.scriptProcessor = null;
        this.analyser = null;

        // 音频播放相关
        this.playbackContext = null;
        this.audioQueue = [];
        this.isPlaying = false;

        // 计时器
        this.lessonStartTime = null;
        this.timerInterval = null;

        // 图片列表
        this.images = [];

        // 当前阶段
        this.currentStage = 'vocabulary'; // 默认是vocabulary阶段

        // 防止重复点击阶段按钮
        this.isStageChanging = false;

        this.transcriptArea = document.getElementById('transcriptArea');
        this.summaryArea = document.getElementById('summaryArea');
        this.stageControls = document.getElementById('stageControls');

        // 事件监听
        this.createLessonBtn.addEventListener('click', () => this.createLesson());
        this.startLessonBtn.addEventListener('click', () => this.startLesson());
        this.newLessonBtn.addEventListener('click', () => this.resetLesson());
        this.startRecordingBtn.addEventListener('click', () => this.startRecording());
        this.stopRecordingBtn.addEventListener('click', () => this.stopRecording());
        this.endLessonBtn.addEventListener('click', () => this.endLesson());

        // 阶段切换按钮
        document.querySelectorAll('.stage').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const stage = e.target.dataset.stage;
                this.switchStage(stage);
            });
        });

        // 图片上传
        this.imageUpload.addEventListener('click', () => this.imageInput.click());
        this.imageInput.addEventListener('change', (e) => this.handleImageUpload(e));
    }

    setupAudioVisualization() {
        const canvas = document.getElementById('audioCanvas');
        this.canvasCtx = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth;
        canvas.height = 80;
        this.drawVisualization();
    }

    drawVisualization() {
        const canvas = document.getElementById('audioCanvas');
        const ctx = this.canvasCtx;
        const width = canvas.width;
        const height = canvas.height;

        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, width, height);

        if (this.isRecording && this.analyser) {
            const bufferLength = this.analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            this.analyser.getByteTimeDomainData(dataArray);

            ctx.lineWidth = 2;
            ctx.strokeStyle = '#1e3c72';
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
            ctx.strokeStyle = '#ccc';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(0, height / 2);
            ctx.lineTo(width, height / 2);
            ctx.stroke();
        }

        requestAnimationFrame(() => this.drawVisualization());
    }

    async handleImageUpload(event) {
        const files = Array.from(event.target.files);

        for (const file of files) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const base64 = e.target.result;
                this.images.push(base64);

                // 显示预览
                const img = document.createElement('img');
                img.src = base64;
                this.imagePreview.appendChild(img);
            };
            reader.readAsDataURL(file);
        }
    }

    async createLesson() {
        const text = this.lessonText.value.trim();

        if (!text && this.images.length === 0) {
            alert('Please enter lesson topic or upload images!');
            return;
        }

        this.createLessonBtn.disabled = true;
        this.createLessonBtn.innerHTML = '<span class="loader"></span> Creating...';

        try {
            // 创建课程
            const response = await fetch('/api/lessons', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    images: this.images
                })
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to create lesson');
            }

            this.lessonId = data.lesson_id;
            document.getElementById('lessonId').textContent = this.lessonId;
            this.updateStatus('preparing');

            // 准备课程计划
            await this.prepareLesson();

        } catch (error) {
            console.error('Error creating lesson:', error);
            alert('Failed to create lesson: ' + error.message);
            this.createLessonBtn.disabled = false;
            this.createLessonBtn.textContent = 'Create Lesson';
        }
    }

    async prepareLesson() {
        try {
            const response = await fetch(`/api/lessons/${this.lessonId}/prepare`, {
                method: 'POST'
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to prepare lesson');
            }

            // 显示课程计划
            const plan = data.lesson_plan;
            document.getElementById('planTopic').textContent = plan.topic;
            document.getElementById('planDuration').textContent = plan.estimated_duration;

            const objectivesList = document.getElementById('planObjectives');
            objectivesList.innerHTML = '';
            plan.objectives.forEach(obj => {
                const li = document.createElement('li');
                li.textContent = obj;
                objectivesList.appendChild(li);
            });

            document.getElementById('lessonPlanDisplay').classList.remove('hidden');
            this.updateStatus('ready');

            // 切换显示
            this.prepareArea.classList.add('hidden');
            this.lessonInfoArea.classList.remove('hidden');
            this.startLessonBtn.disabled = false;

        } catch (error) {
            console.error('Error preparing lesson:', error);
            alert('Failed to prepare lesson: ' + error.message);
        }
    }

    async startLesson() {
        try {
            const response = await fetch(`/api/lessons/${this.lessonId}/start`, {
                method: 'POST'
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to start lesson');
            }

            this.updateStatus('in-progress');

            // 连接WebSocket
            await this.connectWebSocket();

            // 切换显示
            this.welcomeArea.style.display = 'none';
            this.teachingArea.style.display = 'block';
            this.stageControls.style.display = 'flex';

            // 开始计时
            this.startTimer();

        } catch (error) {
            console.error('Error starting lesson:', error);
            alert('Failed to start lesson: ' + error.message);
        }
    }

    async connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/tutor/${this.lessonId}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('✅ Connected to tutor WebSocket');
            this.addTranscript('system', 'Connected to AI English Tutor. The teacher will greet you soon...');
            this.reconnectAttempts = 0; // 重置重连计数
        };

        this.ws.onmessage = (event) => {
            this.handleServerMessage(JSON.parse(event.data));
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = (event) => {
            console.log(`WebSocket closed with code ${event.code}`);

            // 如果是课程正在进行中，尝试重连
            if (this.lessonId && !this.reconnecting) {
                if (event.code === 1011) {
                    this.addTranscript('system', '⚠️ Connection timeout. Reconnecting...');
                } else {
                    this.addTranscript('system', '⚠️ Connection lost. Reconnecting...');
                }
                this.reconnectWebSocket();
            }
        };
    }

    reconnectWebSocket() {
        if (this.reconnecting) return;

        this.reconnecting = true;
        this.reconnectAttempts = (this.reconnectAttempts || 0) + 1;

        const maxAttempts = 5;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 10000); // 指数退避，最多10秒

        if (this.reconnectAttempts > maxAttempts) {
            this.addTranscript('system', '❌ Failed to reconnect after multiple attempts. Please refresh the page.');
            this.reconnecting = false;
            return;
        }

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${maxAttempts})...`);

        setTimeout(() => {
            this.reconnecting = false;
            this.connectWebSocket();
        }, delay);
    }

    switchStage(stage) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            return;
        }

        // 防止重复点击
        if (this.isStageChanging) {
            console.warn('⚠️ Stage change in progress, please wait...');
            return;
        }

        // 如果已经是当前阶段，忽略
        if (this.currentStage === stage) {
            console.log(`Already in ${stage} stage`);
            return;
        }

        console.log(`🔄 Switching to stage: ${stage}`);

        // 设置标志
        this.isStageChanging = true;
        this.currentStage = stage;

        // 更新按钮状态
        document.querySelectorAll('.stage').forEach(btn => {
            if (btn.dataset.stage === stage) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // 发送阶段切换消息
        this.ws.send(JSON.stringify({
            type: 'stage_change',
            stage: stage
        }));

        // 添加系统消息
        const stageNames = {
            'vocabulary': 'Vocabulary Teaching',
            'article': 'Article Reading',
            'question': 'Question Practice',
            'review': 'Lesson Review'
        };
        this.addTranscript('system', `Switching to: ${stageNames[stage]}`);

        // 2秒后重置标志（给服务端时间处理）
        setTimeout(() => {
            this.isStageChanging = false;
            console.log('✅ Stage change completed, can switch again');
        }, 2000);
    }

    handleServerMessage(data) {
        const eventType = data.type;

        switch (eventType) {
            case 'session.created':
            case 'session.updated':
                console.log('Session configured');
                break;

            case 'response.created':
                console.log('🎤 AI started generating response');
                break;

            case 'response.text.delta':
            case 'response.audio_transcript.delta':
                if (data.delta) {
                    console.log(`📝 Received text: "${data.delta}"`);
                    this.appendToCurrentTranscript('ai', data.delta);
                }
                break;

            case 'response.text.done':
            case 'response.audio_transcript.done':
                console.log('✅ Text generation complete');
                this.finalizeCurrentTranscript();
                break;

            case 'response.audio.delta':
                if (data.delta) {
                    console.log(`🔊 Received audio chunk: ${data.delta.length} bytes`);
                    this.playAudio(data.delta);
                }
                break;

            case 'response.done':
                console.log('✅ AI response completed');
                // 检查是否有输出
                const response = data.response || {};
                const output = response.output || [];
                console.log(`   Output items: ${output.length}`);
                if (output.length === 0) {
                    console.warn('⚠️ No output in response! AI may have been interrupted.');
                }
                break;

            case 'connection_error':
                console.error('Connection error:', data.message);
                this.addTranscript('system', `⚠️ ${data.message}`);
                break;

            case 'error':
                console.error('Server error:', data.error || data.message);
                this.addTranscript('system', 'Error: ' + (data.error?.message || data.message));
                break;
        }
    }

    currentTranscriptText = '';
    currentTranscriptElement = null;

    appendToCurrentTranscript(role, text) {
        if (!this.currentTranscriptElement) {
            this.currentTranscriptText = text;
            this.currentTranscriptElement = this.createTranscriptElement(role, text);
            this.transcriptArea.appendChild(this.currentTranscriptElement);
        } else {
            this.currentTranscriptText += text;
            const contentDiv = this.currentTranscriptElement.querySelector('.content');
            contentDiv.textContent = this.currentTranscriptText;
        }

        this.transcriptArea.scrollTop = this.transcriptArea.scrollHeight;
    }

    finalizeCurrentTranscript() {
        this.currentTranscriptElement = null;
        this.currentTranscriptText = '';
    }

    createTranscriptElement(role, content) {
        const div = document.createElement('div');
        div.className = `transcript-entry ${role}`;

        const roleSpan = document.createElement('div');
        roleSpan.className = 'role';
        roleSpan.textContent = role === 'ai' ? '🎓 Teacher' : '👤 You';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';
        contentDiv.textContent = content;

        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = new Date().toLocaleTimeString();

        div.appendChild(roleSpan);
        div.appendChild(contentDiv);
        div.appendChild(timestamp);

        return div;
    }

    addTranscript(role, content) {
        const element = this.createTranscriptElement(role, content);
        this.transcriptArea.appendChild(element);
        this.transcriptArea.scrollTop = this.transcriptArea.scrollHeight;
    }

    async startRecording() {
        try {
            console.log('🎤 Starting microphone...');

            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000
            });

            const source = this.audioContext.createMediaStreamSource(this.mediaStream);

            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 2048;
            source.connect(this.analyser);

            const bufferSize = 4096;
            this.scriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

            this.scriptProcessor.onaudioprocess = (e) => {
                if (!this.isRecording) return;

                const inputData = e.inputBuffer.getChannelData(0);
                const pcm16 = this.convertToPCM16(inputData);
                const base64Audio = this.arrayBufferToBase64(pcm16);

                // 持续发送音频数据，VAD会自动检测语音结束并触发响应
                this.sendMessage({
                    type: "audio",
                    audio: base64Audio
                });
            };

            source.connect(this.scriptProcessor);
            this.scriptProcessor.connect(this.audioContext.destination);

            this.isRecording = true;
            this.startRecordingBtn.disabled = true;
            this.stopRecordingBtn.disabled = false;

            console.log('✅ Microphone started - VAD will auto-detect speech');

        } catch (error) {
            console.error('Failed to start recording:', error);
            alert('Failed to access microphone: ' + error.message);
        }
    }

    stopRecording() {
        // Stop按钮只是暂停麦克风，不影响业务逻辑
        // 用户可以随时Start/Stop来控制麦克风开关
        this.isRecording = false;

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

        // ⚠️ 不再自动发送commit_audio
        // Stop按钮只是静音麦克风，不触发任何业务逻辑
        // VAD会自动检测语音结束并触发响应

        this.startRecordingBtn.disabled = false;
        this.stopRecordingBtn.disabled = true;

        console.log('🔇 Microphone stopped (muted)');
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
            this.audioQueue.push(base64Audio);

            if (!this.isPlaying) {
                this.playNextAudio();
            }
        } catch (error) {
            console.error('Audio playback error:', error);
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

            if (!this.playbackContext) {
                this.playbackContext = new (window.AudioContext || window.webkitAudioContext)({
                    sampleRate: 24000
                });
            }

            const audioBuffer = this.decodePCM16(arrayBuffer, this.playbackContext);
            const source = this.playbackContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.playbackContext.destination);

            source.onended = () => {
                this.playNextAudio();
            };

            source.start();

        } catch (error) {
            console.error('Audio playback error:', error);
            this.playNextAudio();
        }
    }

    decodePCM16(arrayBuffer, audioContext) {
        const view = new DataView(arrayBuffer);
        const numSamples = Math.floor(arrayBuffer.byteLength / 2);

        const audioBuffer = audioContext.createBuffer(1, numSamples, 24000);
        const channelData = audioBuffer.getChannelData(0);

        for (let i = 0; i < numSamples; i++) {
            const sample = view.getInt16(i * 2, true);
            channelData[i] = sample / 32768.0;
        }

        return audioBuffer;
    }

    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    startTimer() {
        this.lessonStartTime = Date.now();
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.lessonStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            document.getElementById('lessonTimer').textContent =
                `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    async endLesson() {
        if (!confirm('Are you sure you want to end this lesson? This will close the session and return to the start page.')) {
            return;
        }

        console.log('🏁 Ending lesson...');

        // 1. 停止录音
        this.stopRecording();

        // 2. 停止计时器
        this.stopTimer();

        // 3. 关闭WebSocket连接
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        // 4. 停止所有音频播放
        this.audioQueue = [];
        this.isPlaying = false;
        if (this.playbackContext) {
            this.playbackContext.close();
            this.playbackContext = null;
        }

        // 5. 完全重置到初始状态
        this.resetLesson();

        console.log('✅ Lesson ended, returned to start page');
    }

    resetLesson() {
        this.lessonId = null;
        this.images = [];
        this.lessonText.value = '';
        this.imagePreview.innerHTML = '';

        this.prepareArea.classList.remove('hidden');
        this.lessonInfoArea.classList.add('hidden');
        this.welcomeArea.style.display = 'block';
        this.teachingArea.style.display = 'none';
        this.summaryArea.style.display = 'none';
        this.stageControls.style.display = 'none';
        this.transcriptArea.innerHTML = '<p style="text-align: center; color: #999;">Conversation will appear here...</p>';

        // 重置阶段按钮状态
        document.querySelectorAll('.stage').forEach(btn => {
            btn.classList.remove('active');
        });

        this.createLessonBtn.disabled = false;
        this.createLessonBtn.textContent = 'Create Lesson';

        this.stopTimer();

        if (this.ws) {
            this.ws.close();
        }
    }

    updateStatus(status) {
        const badge = document.getElementById('lessonStatus');
        badge.className = 'status-badge status-' + status;
        badge.textContent = status.replace('_', ' ').toUpperCase();
    }
}

// Initialize the application
const tutor = new AIEnglishTutor();
