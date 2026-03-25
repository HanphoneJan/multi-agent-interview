<template>
  <view class="classic-page">
    <view class="topbar">
      <view>
        <text class="title">非实时面试</text>
        <text class="subtitle">支持摄像头预览，结束后自动上传视频并生成视频评估。</text>
      </view>
      <text class="status" :class="connectionStatus">{{ statusText }}</text>
    </view>

    <view class="stage card">
      <view class="card-head">
        <view>
          <text class="card-title">摄像头预览</text>
          <text class="card-subtitle">{{ cameraTip }}</text>
        </view>
        <text class="badge" :class="{ danger: recordingState.isRecording }">{{ recordingBadgeText }}</text>
      </view>

      <view class="camera-box">
        <!-- #ifdef H5 -->
        <video
          v-if="recordingState.previewReady"
          ref="previewRef"
          class="camera-view"
          autoplay
          playsinline
          muted
        />
        <!-- #endif -->
        <!-- #ifdef MP-WEIXIN -->
        <camera v-if="recordingState.previewReady" class="camera-view" device-position="front" flash="off" />
        <!-- #endif -->
        <view v-if="!recordingState.previewReady" class="camera-empty">
          <text class="fa-solid fa-camera"></text>
          <text>摄像头暂未就绪</text>
        </view>
        <view v-if="recordingState.previewReady" class="chips">
          <text class="chip strong">{{ recordingBadgeText }}</text>
          <text class="chip">已回答 {{ answeredCount }} 题</text>
          <text class="chip">{{ isPaused ? '已暂停' : '进行中' }}</text>
        </view>
      </view>
    </view>

    <view class="grid">
      <view class="card">
        <view class="card-head">
          <view>
            <text class="card-title">面试对话</text>
            <text class="card-subtitle">按回合查看题目和作答。</text>
          </view>
          <text class="badge">已回答 {{ answeredCount }}</text>
        </view>
        <scroll-view class="history" scroll-y :scroll-top="scrollTop">
          <view v-if="messages.length === 0 && !isLoading" class="empty">
            <text>正在准备第一道题</text>
          </view>
          <view v-for="(msg, index) in messages" :key="index" class="msg" :class="msg.role">
            <text class="msg-tag">{{ msg.role === 'ai' ? '题目' : '我的回答' }}</text>
            <text class="msg-text">{{ msg.content }}</text>
          </view>
          <view v-if="isLoading" class="msg ai">
            <text class="msg-tag">AI 正在生成下一步</text>
            <text class="msg-text">...</text>
          </view>
        </scroll-view>
      </view>

      <view class="side">
        <view class="card">
          <view class="card-head">
            <view>
              <text class="card-title">本轮作答</text>
              <text class="card-subtitle">整理完成后再提交。</text>
            </view>
            <text class="badge">{{ textInput.length }}/500</text>
          </view>
          <view v-if="latestPrompt" class="prompt">
            <text class="prompt-label">当前题目</text>
            <text class="prompt-text">{{ latestPrompt }}</text>
          </view>
          <textarea
            v-model="textInput"
            class="answer"
            maxlength="500"
            :disabled="!canSubmit"
            placeholder="请整理你的答案，再点击提交。"
          ></textarea>
          <view class="footer">
            <text class="tip">{{ isPaused ? '当前已暂停，恢复后才可继续提交。' : '结束面试后会自动执行录像上传与视频评估。' }}</text>
            <button class="primary" :disabled="!canSubmit" @click="sendText">提交本轮回答</button>
          </view>
        </view>

        <view class="card">
          <view class="card-head">
            <view>
              <text class="card-title">面试信息</text>
              <text class="card-subtitle">只保留一种结束流程：停录制、上传、分析、写报告。</text>
            </view>
          </view>
          <view class="info">
            <view class="row"><text>连接状态</text><text>{{ statusText }}</text></view>
            <view class="row"><text>视频状态</text><text>{{ recordingBadgeText }}</text></view>
            <view class="row"><text>交互模式</text><text>非实时文本作答</text></view>
          </view>
          <view class="controls">
            <button class="ghost icon" v-if="!isPaused" @click="handlePause">暂停</button>
            <button class="ghost icon" v-else @click="handleResume">继续</button>
            <button class="danger-btn" :disabled="isEnding || isFinishingVideo" @click="handleEnd">
              {{ isFinishingVideo ? '正在生成评估' : isEnding ? '正在结束面试' : '结束面试' }}
            </button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, nextTick, onUnmounted, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';

import { useInterviewBase } from '@/composables/interview/useInterviewBase';
import { useInterviewWebSocket } from '@/composables/interview/useInterviewWebSocket';
import { ENDPOINTS } from '@/stores/api.js';
import { http } from '@/stores/request.js';
import { useUserStore } from '@/stores/user.js';

const userStore = useUserStore();
const { getWebSocketUrl, showError } = useInterviewBase();

const sessionId = ref('');
const token = ref('');
const messages = ref([]);
const isLoading = ref(false);
const isPaused = ref(false);
const textInput = ref('');
const scrollTop = ref(0);
const isEnding = ref(false);
const isFinishingVideo = ref(false);
const previewRef = ref(null);

const recordingState = ref({
  previewReady: false,
  isRecording: false,
  supported: true,
  issue: '',
  uploadReady: false,
  mimeType: 'video/webm',
  extension: 'webm'
});

let wsUrl = '';
let hasEnded = false;
let browserStream = null;
let browserRecorder = null;
let browserChunks = [];
let recordedBlob = null;
let stopRecordingResolver = null;
let miniProgramCameraContext = null;
let recordedFilePath = '';
let currentAudio = null;
const audioQueue = ref([]);
const isAudioPlaying = ref(false);

const { status: wsStatus, connect, disconnect, send } = useInterviewWebSocket({
  url: () => wsUrl,
  onMessage: handleWebSocketMessage,
  onConnect: () => {
    send({ type: 'start_interview' });
  },
  onError: (err) => {
    console.error('[Classic] WebSocket error:', err);
    showError('面试连接异常，请稍后重试');
  }
});

const connectionStatus = computed(() => {
  if (wsStatus.value === 'connected') return 'connected';
  if (wsStatus.value === 'connecting') return 'connecting';
  return 'disconnected';
});

const statusText = computed(() => {
  if (wsStatus.value === 'connected') return '已连接';
  if (wsStatus.value === 'connecting') return '连接中';
  return '未连接';
});

const answeredCount = computed(() => messages.value.filter((item) => item.role === 'user').length);
const latestPrompt = computed(() => [...messages.value].reverse().find((item) => item.role === 'ai')?.content || '');
const canSubmit = computed(() => wsStatus.value === 'connected' && !isPaused.value && textInput.value.trim().length > 0 && !isFinishingVideo.value);
const recordingBadgeText = computed(() => {
  if (recordingState.value.isRecording) return '录制中';
  if (recordingState.value.uploadReady) return '已完成录制';
  if (!recordingState.value.supported) return '无法录制';
  return '准备中';
});
const cameraTip = computed(() => {
  if (recordingState.value.issue) return recordingState.value.issue;
  if (recordingState.value.isRecording) return '镜头与录制已开启，结束时会自动上传并分析。';
  if (recordingState.value.previewReady) return '摄像头预览已开启。';
  return '正在初始化摄像头与录制。';
});

onLoad((options) => {
  const id = options?.id;
  if (!id) {
    showError('缺少会话 ID');
    uni.navigateBack();
    return;
  }

  sessionId.value = id;
  token.value = uni.getStorageSync('access_token');

  if (!token.value) {
    showError('请先登录');
    uni.redirectTo({ url: '/pages/login/login' });
    return;
  }

  void init();
});

async function init() {
  await prepareInterviewMedia();
  wsUrl = getWebSocketUrl({ sessionId: sessionId.value, token: token.value, mode: 'classic' });
  connect();
}

function handleWebSocketMessage(msg) {
  switch (msg.type) {
    case 'question':
      isLoading.value = false;
      addMessage('ai', msg.question || msg.text || '请开始作答');
      break;
    case 'stream_chunk': {
      if (isLoading.value) {
        isLoading.value = false;
        addMessage('ai', msg.chunk || '');
      } else {
        const last = messages.value[messages.value.length - 1];
        if (last && last.role === 'ai') last.content += msg.chunk || '';
      }
      scrollToBottom();
      break;
    }
    case 'stream_end':
      isLoading.value = false;
      break;
    case 'audio_delta':
      if (msg.audio) {
        audioQueue.value.push(msg.audio);
        void playNextAudio();
      }
      break;
    case 'info':
      uni.showToast({ title: msg.message || '操作已完成', icon: 'none' });
      break;
    case 'error':
      isLoading.value = false;
      showError(msg.error || '服务异常');
      break;
    case 'end':
      void finalizeInterview(msg.summary);
      break;
  }
}

function addMessage(role, content) {
  messages.value.push({ role, content, timestamp: Date.now() });
  scrollToBottom();
}

function scrollToBottom() {
  nextTick(() => {
    scrollTop.value = messages.value.length * 220;
  });
}

function sendText() {
  const text = textInput.value.trim();
  if (!text || !canSubmit.value) return;
  send({ type: 'text', text });
  addMessage('user', text);
  textInput.value = '';
  isLoading.value = true;
}

function handlePause() {
  isPaused.value = true;
  send({ type: 'pause_interview' });
  pauseLocalRecording();
}

function handleResume() {
  isPaused.value = false;
  send({ type: 'resume_interview' });
  resumeLocalRecording();
}

function handleEnd() {
  if (isEnding.value || isFinishingVideo.value) return;
  uni.showModal({
    title: '确认结束',
    content: '确定结束当前非实时面试吗？系统会立即上传录像并生成视频评估。',
    success: (res) => {
      if (res.confirm) {
        isEnding.value = true;
        send({ type: 'end_interview' });
      }
    }
  });
}

async function finalizeInterview(summary) {
  if (hasEnded) return;
  hasEnded = true;
  isFinishingVideo.value = true;
  disconnect();
  stopAudioPlayback();

  uni.showLoading({ title: '正在上传视频并生成评估', mask: true });
  let content = summary?.overall_evaluation || '本次面试已结束。';

  try {
    const result = await finalizeRecordedVideoAndReport();
    content += `\n\n${result}`;
  } catch (error) {
    content += `\n\n视频评估未完成：${getErrorMessage(error)}`;
  } finally {
    uni.hideLoading();
    stopInterviewMedia();
    isFinishingVideo.value = false;
    isEnding.value = false;
  }

  uni.showModal({
    title: '面试结束',
    content,
    showCancel: false,
    success: () => {
      uni.redirectTo({ url: `/pages/report/report?sessionId=${sessionId.value}` });
    }
  });
}

async function finalizeRecordedVideoAndReport() {
  await stopLocalRecording();
  if (!recordingState.value.uploadReady) return '未采集到可分析的视频，已直接结束面试。';

  await uploadRecordedVideo();
  const analysisResponse = await http.post(ENDPOINTS.interview.sessionAnalyzeVideo(sessionId.value), {});
  const analysisData = analysisResponse?.data || analysisResponse;
  await ensureEvaluationReport(analysisData);
  return '视频评估已完成，可在面试反馈页查看结果。';
}

async function ensureEvaluationReport(analysisData) {
  try {
    await http.get(ENDPOINTS.evaluation.reportDetail(sessionId.value));
    return;
  } catch (error) {
    // Continue to create the report if it does not exist yet.
  }

  if (!userStore.userId) {
    throw new Error('未获取到用户信息，无法保存评估报告');
  }

  const overallScore = normalizeScore(analysisData?.overall_score);
  const strengths = Array.isArray(analysisData?.strengths) ? analysisData.strengths.join('；') : '暂无';
  const weaknesses = Array.isArray(analysisData?.weaknesses) ? analysisData.weaknesses.join('；') : '暂无';

  await http.post(ENDPOINTS.evaluation.reports, {
    session_id: Number(sessionId.value),
    user_id: Number(userStore.userId),
    overall_evaluation: analysisData?.overall_impression || '视频评估已完成。',
    help: analysisData?.suggestions || '建议继续通过模拟面试强化表达与结构化回答。',
    recommendation: `优点：${strengths}\n待改进：${weaknesses}`,
    overall_score: overallScore,
    professional_knowledge: overallScore,
    skill_match: overallScore,
    language_expression: overallScore,
    logical_thinking: overallScore,
    stress_response: overallScore,
    personality: overallScore,
    motivation: overallScore,
    value: overallScore
  });
}

function normalizeScore(score) {
  const value = Number(score);
  if (Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(100, Math.round(value)));
}

async function prepareInterviewMedia() {
  // #ifdef H5
  await prepareBrowserMedia();
  return;
  // #endif
  // #ifdef MP-WEIXIN
  await prepareMiniProgramMedia();
  return;
  // #endif
  recordingState.value.supported = false;
  recordingState.value.issue = '当前平台暂不支持自动视频采集。';
}

async function prepareBrowserMedia() {
  if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
    recordingState.value.supported = false;
    recordingState.value.issue = '当前浏览器不支持摄像头预览或录制。';
    return;
  }

  try {
    browserStream = await requestBrowserStream();
    recordingState.value.previewReady = !!browserStream.getVideoTracks().length;
    await nextTick();
    if (previewRef.value) {
      previewRef.value.srcObject = browserStream;
      await previewRef.value.play().catch(() => undefined);
    }
    if (typeof MediaRecorder === 'undefined') {
      recordingState.value.supported = false;
      recordingState.value.issue = '当前浏览器支持预览，但不支持录制。';
      return;
    }
    startBrowserRecording();
  } catch (error) {
    recordingState.value.supported = false;
    recordingState.value.issue = '摄像头或麦克风权限被拒绝，无法生成视频评估。';
  }
}

async function requestBrowserStream() {
  try {
    return await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: true
    });
  } catch (error) {
    return await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false
    });
  }
}

function startBrowserRecording() {
  if (!browserStream) return;
  browserChunks = [];
  recordedBlob = null;
  recordingState.value.uploadReady = false;
  const mimeType = pickSupportedMimeType();
  recordingState.value.mimeType = mimeType || 'video/webm';
  recordingState.value.extension = recordingState.value.mimeType.includes('mp4') ? 'mp4' : 'webm';
  browserRecorder = mimeType ? new MediaRecorder(browserStream, { mimeType }) : new MediaRecorder(browserStream);
  browserRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) browserChunks.push(event.data);
  };
  browserRecorder.onstop = () => {
    recordedBlob = browserChunks.length ? new Blob(browserChunks, { type: recordingState.value.mimeType }) : null;
    recordingState.value.isRecording = false;
    recordingState.value.uploadReady = !!recordedBlob;
    if (stopRecordingResolver) {
      stopRecordingResolver();
      stopRecordingResolver = null;
    }
  };
  browserRecorder.start(1000);
  recordingState.value.isRecording = true;
}

function pickSupportedMimeType() {
  const candidates = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm', 'video/mp4'];
  for (const candidate of candidates) {
    if (MediaRecorder.isTypeSupported?.(candidate)) return candidate;
  }
  return '';
}

async function prepareMiniProgramMedia() {
  const cameraOk = await authorizeScope('scope.camera');
  const recordOk = await authorizeScope('scope.record');
  if (!cameraOk || !recordOk) {
    recordingState.value.supported = false;
    recordingState.value.issue = '需要摄像头和麦克风权限，才能生成视频评估。';
    return;
  }
  recordingState.value.previewReady = true;
  await nextTick();
  await new Promise((resolve) => setTimeout(resolve, 200));
  miniProgramCameraContext = uni.createCameraContext();
  await startMiniProgramRecording();
}

function authorizeScope(scope) {
  return new Promise((resolve) => {
    uni.authorize({ scope, success: () => resolve(true), fail: () => resolve(false) });
  });
}

function startMiniProgramRecording() {
  return new Promise((resolve) => {
    if (!miniProgramCameraContext) {
      resolve(false);
      return;
    }
    miniProgramCameraContext.startRecord({
      success: () => {
        recordingState.value.isRecording = true;
        resolve(true);
      },
      fail: () => {
        recordingState.value.issue = '已打开预览，但录像启动失败。';
        resolve(false);
      }
    });
  });
}

function pauseLocalRecording() {
  // #ifdef H5
  if (browserRecorder && browserRecorder.state === 'recording' && typeof browserRecorder.pause === 'function') browserRecorder.pause();
  // #endif
}

function resumeLocalRecording() {
  // #ifdef H5
  if (browserRecorder && browserRecorder.state === 'paused' && typeof browserRecorder.resume === 'function') browserRecorder.resume();
  // #endif
}

async function stopLocalRecording() {
  // #ifdef H5
  await stopBrowserRecording();
  return;
  // #endif
  // #ifdef MP-WEIXIN
  await stopMiniProgramRecording();
  return;
  // #endif
}

function stopBrowserRecording() {
  return new Promise((resolve) => {
    if (!browserRecorder || browserRecorder.state === 'inactive') {
      resolve();
      return;
    }
    stopRecordingResolver = resolve;
    browserRecorder.stop();
  });
}

function stopMiniProgramRecording() {
  return new Promise((resolve) => {
    if (!miniProgramCameraContext || !recordingState.value.isRecording) {
      resolve();
      return;
    }
    miniProgramCameraContext.stopRecord({
      success: (res) => {
        recordedFilePath = res.tempVideoPath || '';
        recordingState.value.isRecording = false;
        recordingState.value.uploadReady = !!recordedFilePath;
        resolve();
      },
      fail: () => {
        recordingState.value.isRecording = false;
        resolve();
      }
    });
  });
}

async function uploadRecordedVideo() {
  // #ifdef H5
  if (!recordedBlob) throw new Error('未获取到浏览器录制视频');
  const formData = new FormData();
  const file = new File([recordedBlob], `classic-interview-${sessionId.value}.${recordingState.value.extension}`, {
    type: recordingState.value.mimeType || 'video/webm'
  });
  formData.append('file', file);
  const response = await fetch(ENDPOINTS.interview.sessionVideoUpload(sessionId.value), {
    method: 'POST',
    headers: { Authorization: `Bearer ${token.value}` },
    body: formData
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.detail || payload?.message || '上传视频失败');
  return payload;
  // #endif
  // #ifdef MP-WEIXIN
  if (!recordedFilePath) throw new Error('未获取到小程序录制视频');
  return await http.upload({
    url: ENDPOINTS.interview.sessionVideoUpload(sessionId.value),
    filePath: recordedFilePath,
    name: 'file'
  });
  // #endif
  throw new Error('当前平台暂不支持视频上传');
}

async function playNextAudio() {
  if (isAudioPlaying.value || audioQueue.value.length === 0) return;
  const base64Audio = audioQueue.value.shift();
  if (!base64Audio) return;
  isAudioPlaying.value = true;
  try {
    const bytes = Uint8Array.from(atob(base64Audio), (char) => char.charCodeAt(0));
    const blob = new Blob([bytes], { type: 'audio/wav' });
    const audioUrl = URL.createObjectURL(blob);
    currentAudio = new Audio(audioUrl);
    currentAudio.onended = () => {
      URL.revokeObjectURL(audioUrl);
      currentAudio = null;
      isAudioPlaying.value = false;
      void playNextAudio();
    };
    currentAudio.onerror = currentAudio.onended;
    await currentAudio.play();
  } catch (error) {
    isAudioPlaying.value = false;
  }
}

function stopAudioPlayback() {
  if (currentAudio) currentAudio.pause();
  currentAudio = null;
  isAudioPlaying.value = false;
  audioQueue.value = [];
}

function stopInterviewMedia() {
  // #ifdef H5
  if (browserRecorder && browserRecorder.state !== 'inactive') browserRecorder.stop();
  browserRecorder = null;
  if (browserStream) browserStream.getTracks().forEach((track) => track.stop());
  browserStream = null;
  if (previewRef.value) {
    previewRef.value.pause();
    previewRef.value.srcObject = null;
  }
  // #endif
  recordedFilePath = '';
  recordingState.value.previewReady = false;
  recordingState.value.isRecording = false;
}

function getErrorMessage(error) {
  return error?.message || error?.detail || '请稍后重试';
}

onUnmounted(() => {
  disconnect();
  stopAudioPlayback();
  stopInterviewMedia();
});
</script>

<style scoped>
.classic-page { min-height: 100vh; padding: 28rpx; background: linear-gradient(180deg, #f4f7fb 0%, #edf2f9 100%); }
.topbar, .card { background: rgba(255,255,255,.95); border-radius: 24rpx; box-shadow: 0 16rpx 40rpx rgba(22,34,66,.08); }
.topbar { display:flex; justify-content:space-between; gap:24rpx; padding:32rpx; margin-bottom:24rpx; }
.title { display:block; font-size:40rpx; font-weight:700; color:#1f2a44; }
.subtitle, .card-subtitle, .tip { display:block; margin-top:8rpx; font-size:24rpx; line-height:1.6; color:#667085; }
.status, .badge, .chip { display:inline-flex; align-items:center; justify-content:center; border-radius:999rpx; font-size:22rpx; }
.status { min-width:128rpx; padding:12rpx 24rpx; background:#edf2f7; color:#475467; }
.status.connected { background:#e8f7ef; color:#067647; }
.status.connecting { background:#fff3e0; color:#b54708; }
.card-head { display:flex; justify-content:space-between; gap:20rpx; padding:24rpx 28rpx; border-bottom:1rpx solid #e7ecf3; }
.card-title { display:block; font-size:30rpx; font-weight:700; color:#1f2a44; }
.badge { padding:10rpx 20rpx; background:#eef4ff; color:#335cff; }
.badge.danger { background:#fee4e2; color:#b42318; }
.stage { margin-bottom:24rpx; overflow:hidden; }
.camera-box { position:relative; min-height:400rpx; background:#0f172a; }
.camera-view { width:100%; height:400rpx; object-fit:cover; }
.camera-empty { min-height:400rpx; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:16rpx; color:rgba(255,255,255,.82); }
.chips { position:absolute; left:24rpx; right:24rpx; bottom:24rpx; display:flex; flex-wrap:wrap; gap:12rpx; }
.chip { min-height:60rpx; padding:0 20rpx; background:rgba(15,23,42,.55); color:#fff; }
.chip.strong { background:rgba(180,35,24,.88); }
.grid { display:grid; grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr); gap:24rpx; }
.side { display:flex; flex-direction:column; gap:24rpx; }
.history { height:760rpx; padding:24rpx 28rpx; box-sizing:border-box; }
.empty { min-height:100%; display:flex; align-items:center; justify-content:center; color:#667085; }
.msg { margin-bottom:18rpx; padding:22rpx 24rpx; border-radius:20rpx; background:#fff; border:1rpx solid #e7ecf3; }
.msg.user { background:linear-gradient(135deg,#3964fe,#4b6bff); color:#fff; border:none; }
.msg-tag { display:block; font-size:22rpx; opacity:.76; }
.msg-text { display:block; margin-top:8rpx; font-size:28rpx; line-height:1.7; }
.prompt { margin:24rpx 28rpx 0; padding:22rpx; border-radius:20rpx; background:linear-gradient(135deg,#eef4ff,#f7f9ff); border:1rpx solid #d9e4ff; }
.prompt-label { display:block; font-size:22rpx; color:#335cff; }
.prompt-text { display:block; margin-top:8rpx; font-size:26rpx; line-height:1.6; color:#1f2a44; }
.answer { width:auto; min-height:320rpx; margin:24rpx 28rpx 0; padding:22rpx; border-radius:20rpx; background:#f8fafc; border:1rpx solid #dbe4ee; box-sizing:border-box; font-size:28rpx; line-height:1.7; color:#1f2a44; }
.footer { padding:24rpx 28rpx 28rpx; }
.info { padding:12rpx 28rpx 0; }
.row { display:flex; justify-content:space-between; gap:20rpx; padding:18rpx 0; border-bottom:1rpx solid #eef2f6; font-size:24rpx; color:#475467; }
.controls { display:flex; gap:16rpx; padding:24rpx 28rpx 28rpx; }
.primary, .ghost, .danger-btn { display:inline-flex; align-items:center; justify-content:center; border:none; border-radius:999rpx; font-size:26rpx; }
.primary { width:100%; height:84rpx; background:linear-gradient(135deg,#3964fe,#4f7bff); color:#fff; }
.primary[disabled] { background:#c7d2e1; }
.ghost.icon { width:92rpx; height:84rpx; background:#edf2f7; color:#475467; }
.danger-btn { flex:1; height:84rpx; background:#ef4444; color:#fff; }
@media (max-width: 1024px) { .grid { grid-template-columns:1fr; } .history { height:620rpx; } }
</style>
