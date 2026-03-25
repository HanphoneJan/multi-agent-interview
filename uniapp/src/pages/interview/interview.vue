<template>
  <!-- 模板部分保持不变 -->
  <view class="interview-container">
    <!-- 顶部信息栏 -->
    <view class="header-bar">
      <text class="title">AI面试助手</text>

      <!-- 状态和控制按钮组 -->
      <view class="control-group">
        <!-- 连接状态 -->
        <view class="status-item">
          <uni-icons
            :type="wsConnected ? 'link' : 'unlink'"
            size="16"
            :color="wsConnected ? 'var(--color-primary)' : 'var(--text-tertiary)'"
          ></uni-icons>
          <text :class="wsConnected ? 'success' : 'default'"
            >{{ wsConnected ? '已连接' : '未连接' }}</text
          >
        </view>

        <!-- 面试状态 -->
        <view class="status-item" v-if="sessionStatus">
          <uni-icons type="info-filled" size="16" color="var(--text-secondary)"></uni-icons>
          <text>{{ sessionStatusText }}</text>
        </view>

        <!-- 计时器 -->
        <view class="status-item timer">
          <uni-icons type="clock" size="16" color="var(--text-secondary)"></uni-icons>
          <text>{{ formattedTime }}</text>
        </view>
      </view>

      <!-- 操作按钮组 -->
      <view class="action-buttons">
        <!-- 暂停/恢复按钮 (仅面试中显示) -->
        <button
          v-if="wsConnected && sessionStatus === 'in_progress'"
          class="control-btn warning"
          @click="handlePause"
        >
          <uni-icons type="pause" size="14" color="var(--text-inverse)"></uni-icons>
          <text>暂停</text>
        </button>

        <button
          v-if="wsConnected && sessionStatus === 'paused'"
          class="control-btn primary"
          @click="handleResume"
        >
          <uni-icons type="play" size="14" color="var(--text-inverse)"></uni-icons>
          <text>恢复</text>
        </button>

        <!-- 结束按钮 -->
        <button v-if="wsConnected" class="control-btn danger" @click="handleEnd" :disabled="endingInterview">
          <uni-icons type="checkmarkempty" size="14" color="var(--text-inverse)"></uni-icons>
          <text>{{ endingInterview ? '结束中...' : '结束面试' }}</text>
        </button>

        <!-- TTS 语音播报开关 (仅面试中显示) -->
        <button
          v-if="wsConnected"
          class="control-btn"
          :class="ttsEnabled ? 'primary' : 'secondary'"
          @click="ttsEnabled = !ttsEnabled"
          :title="ttsEnabled ? '关闭语音播报' : '开启语音播报'"
        >
          <uni-icons :type="ttsEnabled ? 'volume-up' : 'volume-off'" size="14" color="var(--text-inverse)"></uni-icons>
          <text>{{ ttsEnabled ? '语音开' : '语音关' }}</text>
        </button>

        <!-- 取消按钮 (未连接但有sessionId时显示) -->
        <button
          v-if="!wsConnected && userStore.sessionId"
          class="control-btn danger"
          @click="handleCancel"
        >
          <uni-icons type="close" size="14" color="var(--text-inverse)"></uni-icons>
          <text>取消</text>
        </button>

        <!-- 开始按钮 -->
        <button v-if="!wsConnected" class="control-btn primary" @click="toggleInterview">
          <uni-icons type="play" size="14" color="var(--text-inverse)"></uni-icons>
          <text>开始面试</text>
        </button>
      </view>
    </view>

    <!-- 主要内容区域 -->
    <view class="main-content">
      <!-- 对话区域 -->
      <view class="conversation-section">
        <view class="conversation-header">
          <text class="section-title">面试对话</text>
          <view class="interviewer-info">
            <image class="avatar" src="https://hanphone.top/images/zhuxun.jpg" mode="aspectFill"></image>
            <text class="interviewer-name">AI面试官</text>
          </view>
        </view>
        
        <scroll-view class="conversation-container" scroll-y :scroll-top="scrollTop">
          <view v-if="!currentQuestion && conversationHistory.length === 0" class="empty-state">
            <uni-icons type="chat" size="48" color="var(--text-tertiary)"></uni-icons>
            <text class="empty-text">正在准备问题...</text>
          </view>

          <view v-for="(item, index) in conversationHistory" :key="index" class="message" :class="item.type">
            <view class="message-content" :class="item.type">
              <text class="message-text">{{ item.content }}</text>
            </view>
            <text class="message-time">{{ formatTime(item.timestamp) }}</text>
          </view>

          <view v-if="currentQuestion" class="message question fade-in">
            <view class="message-content question">
              <text class="message-text">{{ currentQuestion.content }}</text>
            </view>
            <text class="message-time">{{ formatTime(currentQuestion.timestamp) }}</text>
          </view>
        </scroll-view>
      </view>

      <!-- 回答输入区 -->
      <view class="answer-section">
        <view class="answer-header">
          <text class="section-title">我的回答</text>
          <text class="answer-count">{{ textAnswer.length }}/500</text>
        </view>
        
        <textarea 
          v-model="textAnswer" 
          class="answer-input" 
          placeholder="请输入您的回答..." 
          maxlength="500" 
          :disabled="!wsConnected"
        ></textarea>
        
        <view class="answer-controls">
          <view class="device-controls">
            <button class="control-btn small" :class="{ active: isCameraOn }" @click="toggleCamera">
              <uni-icons :type="isCameraOn ? 'videocam-filled' : 'videocam'" size="16" color="var(--text-inverse)"></uni-icons>
            </button>
            <button class="control-btn small" :class="{ active: isMicOn }" @click="toggleMic">
              <uni-icons :type="isMicOn ? 'mic-filled' : 'mic'" size="16" color="var(--text-inverse)"></uni-icons>
            </button>
          </view>
          
          <button 
            class="send-btn" 
            @click="sendTextAnswer" 
            :disabled="!textAnswer.trim() || !wsConnected"
            :class="{ disabled: !textAnswer.trim() || !wsConnected }"
          >
            <text>发送</text>
            <uni-icons type="paperplane" size="16" color="var(--text-inverse)"></uni-icons>
          </button>
        </view>
      </view>

      <!-- 视频预览区 -->
      <view class="video-section">
        <text class="section-title">视频预览</text>
        <view class="video-container">
          <camera
            v-if="isCameraOn"
            class="camera-preview"
            device-position="front"
            flash="off"
            @error="handleCameraError"
            ref="cameraRef"
          ></camera>
          <view v-else class="camera-placeholder">
            <uni-icons type="videocam" size="48" color="var(--text-tertiary)"></uni-icons>
            <text>摄像头已关闭</text>
          </view>
        </view>
      </view>

      <!-- 信息面板 -->
      <view class="info-section">
        <view class="info-panel">
          <text class="panel-title">面试信息</text>
          <view class="info-item">
            <text class="info-label">面试状态</text>
            <text class="info-value" :class="{
              'success': wsConnected,
              'warning': wsConnecting,
              'default': !wsConnected && !wsConnecting
            }">
              {{ endingInterview ? '结束中...' : wsConnected ? '进行中' : wsConnecting ? '连接中...' : '未开始' }}
            </text>
          </view>
          <view class="info-item">
            <text class="info-label">已回答问题</text>
            <text class="info-value">{{ answeredCount }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">当前问题</text>
            <text class="info-value">{{ currentQuestion ? '1个待回答' : '暂无' }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">摄像头权限</text>
            <text class="info-value" :class="cameraPermission === 'granted' ? 'success' : cameraPermission === 'denied' ? 'danger' : 'warning'">
              {{ permissionTextMap[cameraPermission] }}
            </text>
          </view>
          <view class="info-item">
            <text class="info-label">麦克风权限</text>
            <text class="info-value" :class="micPermission === 'granted' ? 'success' : micPermission === 'denied' ? 'danger' : 'warning'">
              {{ permissionTextMap[micPermission] }}
            </text>
          </view>
        </view>

        <view class="info-panel">
          <text class="panel-title">个人信息</text>
          <view class="info-item">
            <text class="info-label">姓名</text>
            <text class="info-value">{{ userStore.name || '未设置' }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">性别</text>
            <text class="info-value">{{ genderMap[userStore.gender] || '未填写' }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">学校</text>
            <text class="info-value">{{ userStore.university || '未设置' }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">专业</text>
            <text class="info-value">{{ userStore.major || '未设置' }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">现阶段</text>
            <text class="info-value">{{ learningStageMap[userStore.learningStage] || '未设置' }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 错误提示 -->
    <view v-if="errorMessage" class="error-toast">
      <uni-icons type="info" size="16" color="#fff"></uni-icons>
      <text>{{ errorMessage }}</text>
    </view>
  </view>
</template>


<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useUserStore } from '@/stores/user.js'
import { onShow } from '@dcloudio/uni-app';
import { WS_URL } from '@/config/index.js';
import http from '@/stores/request.js'
import { ENDPOINTS } from '@/stores/api.js'
import { ttsService } from '@/stores/tts.js'
// WebSocket 连接 - FastAPI后端
const wsUrl = WS_URL
let websocket = null
const wsConnected = ref(false)
const wsConnecting = ref(false)
const endingInterview = ref(false)
let reconnectTimer = null
const maxReconnectAttempts = 5
let reconnectAttempts = 0

// 面试状态
const interviewStatus = ref('面试未开启')
const interviewTimer = ref(0)
let timerInterval = null
const errorMessage = ref('')

// 设备状态和权限
const isCameraOn = ref(false)  // 默认关闭，获取权限后再开启
const isMicOn = ref(false)     // 默认关闭，获取权限后再开启
const cameraPermission = ref('unknown')  // unknown, granted, denied
const micPermission = ref('unknown')     // unknown, granted, denied

// 对话相关
const currentQuestion = ref(null)
const conversationHistory = ref([])
const textAnswer = ref('')
const scrollTop = ref(0)

// 摄像头相关
const cameraRef = ref(null)
let captureInterval = null
// 音频录制相关
const isRecording = ref(false)
let audioChunks = []

// TTS 语音播报
const ttsEnabled = ref(false) // 默认关闭

// 用户信息
const userStore = useUserStore()

// 当前会话信息
const currentSession = ref(null)
const sessionStatus = ref(null)
const sessionStatusText = computed(() => {
  const statusMap = {
    'in_progress': '进行中',
    'paused': '已暂停',
    'completed': '已完成',
    'cancelled': '已取消',
    'pending': '待开始'
  }
  return statusMap[sessionStatus.value] || '未开始'
})
const genderMap = {
  M: "男",
  F: "女",
  O: "其他"
}
// 定义学习阶段映射关系
const learningStageMap = {
  'FRESHMAN_1': '大一上',
  'FRESHMAN_2': '大一下',
  'SOPHOMORE_1': '大二上',
  'SOPHOMORE_2': '大二下',
  'JUNIOR_1': '大三上',
  'JUNIOR_2': '大三下',
  'SENIOR_1': '大四上',
  'SENIOR_2': '大四下',
  'GRADUATE_STUDENT': '研究生',
  'JOB_SEEKER': '应届生',
  'EMPLOYED': '社会人士',
  'OTHER': '其他'
}
// 权限文本映射
const permissionTextMap = {
  unknown: '未知',
  granted: '已授权',
  denied: '未授权'
}

// 计算属性
const formattedTime = computed(() => {
  const minutes = Math.floor(interviewTimer.value / 60)
  const seconds = interviewTimer.value % 60
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
})

const answeredCount = computed(() => {
  return conversationHistory.value.filter(item => item.type === 'answer').length
})

// 格式化时间戳
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 显示错误信息
const showError = (message) => {
  errorMessage.value = message
  setTimeout(() => {
    errorMessage.value = ''
  }, 5000)
}

// 新增：获取面试官设置
const getInterviewerSettings = () => {
  try {
    const settings = uni.getStorageSync('interviewerSettings')
    return settings ? settings : {
      gender: '',
      speed: '',
      voice: '',
      style: ''
    }
  } catch (err) {
    console.error('获取面试官设置失败:', err)
    return {
      gender: '',
      speed: '',
      voice: '',
      style: ''
    }
  }
}

// 检查并请求摄像头权限
const checkAndRequestCameraPermission = async () => {
  try {
    // 先检查是否已经授权
    const setting = await uni.getSetting()
    
    if (setting.authSetting['scope.camera']) {
      cameraPermission.value = 'granted'
      return true
    }
    
    // 未授权，调用uni.authorize请求授权
    const authResult = await uni.authorize({ 
      scope: 'scope.camera',
      fail: async (err) => {
        console.log('用户拒绝摄像头权限11')
        // 授权失败，询问用户是否前往设置
        const confirmResult = await uni.showModal({
          title: '权限申请',
          content: '需要摄像头权限才能正常使用，请前往设置开启',
          confirmText: '去设置',
          cancelText: '取消'
        })
        console.log('用户摄像头权限22')
        // 如果用户确认，则打开设置页面
        if (confirmResult.confirm) {
            uni.openSetting({
            success() {
              console.log('开启权限成功');
            },
            fail() {
              console.log('开启权限失败');
            }
          });
        }
      }
    })
    
    // 授权成功
    if (authResult.errMsg === 'authorize:ok') {
      cameraPermission.value = 'granted'
      return true
    } else {
      // 授权失败（非拒绝）
      cameraPermission.value = 'denied'
      showError('摄像头授权失败，请重试')
      return false
    }
  } catch (error) {
    // 捕获用户明确拒绝的情况
    if (error.errMsg.includes('auth deny')) {
      cameraPermission.value = 'denied'
      // 询问用户是否前往设置
      console.log('用户拒绝摄像头权限')
      const confirmResult = await uni.showModal({
        title: '权限申请',
        content: '需要摄像头权限才能正常使用，请前往设置开启',
        confirmText: '去设置',
        cancelText: '取消'
      })
      
      // 如果用户确认，则打开设置页面
      if (confirmResult.confirm) {
        console.log('用户同意前往设置')
          uni.openSetting({
          success() {
            console.log('开启权限成功');
          },
          fail() {
            console.log('开启权限失败');
          }
        });
      }
    } else {
      cameraPermission.value = 'denied'
      showError('获取摄像头权限失败: ' + error.errMsg)
    }
    return false
  }
}

// 检查并请求麦克风权限
const checkAndRequestMicPermission = async () => {
  try {
    // 先检查是否已经授权
    const setting = await uni.getSetting()
    
    if (setting.authSetting['scope.record']) {
      micPermission.value = 'granted'
      return true
    }
    
    // 未授权，调用uni.authorize请求授权
    const authResult = await uni.authorize({ 
      scope: 'scope.record',
      fail: async (err) => {
        // 授权失败，询问用户是否前往设置
        const confirmResult = await uni.showModal({
          title: '权限申请',
          content: '需要麦克风权限才能正常使用，请前往设置开启',
          confirmText: '去设置',
          cancelText: '取消'
        })
        
        // 如果用户确认，则打开设置页面
        if (confirmResult.confirm) {
             uni.openSetting({
            success() {
              console.log('开启权限成功');
            },
            fail() {
              console.log('开启权限失败');
            }
          });
        }
      }
    })
    
    // 授权成功
    if (authResult.errMsg === 'authorize:ok') {
      micPermission.value = 'granted'
      return true
    } else {
      // 授权失败（非拒绝）
      micPermission.value = 'denied'
      showError('麦克风授权失败，请重试')
      return false
    }
  } catch (error) {
    // 捕获用户明确拒绝的情况
    if (error.errMsg.includes('auth deny')) {
      micPermission.value = 'denied'
      // 询问用户是否前往设置
      const confirmResult = await uni.showModal({
        title: '权限申请',
        content: '需要麦克风权限才能正常使用，请前往设置开启',
        confirmText: '去设置',
        cancelText: '取消'
      })
      
      // 如果用户确认，则打开设置页面
      if (confirmResult.confirm) {

            uni.openSetting({
              success() {
                console.log('开启权限成功');
              },
              fail() {
                console.log('开启权限失败');
              }
            });
      }
    } else {
      micPermission.value = 'denied'
      showError('获取麦克风权限失败: ' + error.errMsg)
    }
    return false
  }
}


// 检查摄像头权限状态
const checkCameraPermissionStatus = async () => {
  const setting = await uni.getSetting()
  if (setting.authSetting['scope.camera']) {
    cameraPermission.value = 'granted'
  } else {
    cameraPermission.value = 'denied'
  }
}

// 检查麦克风权限状态
const checkMicPermissionStatus = async () => {
  const setting = await uni.getSetting()
  if (setting.authSetting['scope.record']) {
    micPermission.value = 'granted'
  } else {
    micPermission.value = 'denied'
  }
}

// WebSocket 连接管理
const connectWebSocket = async () => {
  // 连接前检查必要的权限
  if (!wsConnected.value) {
    // 至少需要一种输入方式
    const hasCamera = await checkAndRequestCameraPermission()
    const hasMic = await checkAndRequestMicPermission()
    
    if (!hasCamera && !hasMic) {
      showError('至少需要摄像头或麦克风权限才能开始面试')
      return
    }
    
    // 如果有权限，默认开启设备
    if (hasCamera) isCameraOn.value = true
    if (hasMic) isMicOn.value = false
  }
  
  try {
    wsConnecting.value = true
    wsConnected.value = false
    
    // FastAPI WebSocket: /api/v1/ws/interview/{session_id}?token={token}
    const token = userStore.access || '';
    const sessionId = userStore.sessionId || '';
    const wsFullUrl = `${wsUrl}/${sessionId}?token=${encodeURIComponent(token)}`;
    console.log('WebSocket连接URL:', wsFullUrl.replace(token, '***TOKEN***'));

    websocket = uni.connectSocket({
      url: wsFullUrl,
      fail: (err) => {
        console.error('WebSocket连接失败:', err)
        wsConnecting.value = false
        showError('连接失败，请重试')
        scheduleReconnect()
      }
    })

    websocket.onOpen(() => {
      console.log('WebSocket连接成功')
      wsConnecting.value = false
      wsConnected.value = true
      interviewStatus.value = '面试进行中'
      sessionStatus.value = 'in_progress'
      startTimer()
      reconnectAttempts = 0
        // 开始定时拍摄
      startPeriodicCapture()
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }

      // 设置当前会话信息
      currentSession.value = {
        id: userStore.sessionId,
        status: 'in_progress'
      }

      // 发送开始面试消息，触发AI面试官发送第一个问题
      sendMessage({
        type: 'start_interview',
        timestamp: Date.now(),
        session_id: userStore.sessionId
      })
    })

    websocket.onMessage((res) => {
      try {
        const data = JSON.parse(res.data)
        handleWebSocketMessage(data)
      } catch (error) {
        console.error('解析WebSocket消息失败:', error)
        showError('解析消息失败，请重试')
      }
    })

    websocket.onError((err) => {
      console.error('WebSocket错误:', err)
      wsConnected.value = false
      wsConnecting.value = false
      interviewStatus.value = '连接异常'
      showError('网络连接错误')
      scheduleReconnect()
    })

    websocket.onClose(() => {
      console.log('WebSocket连接关闭')
      wsConnected.value = false
      wsConnecting.value = false
      interviewStatus.value = '连接已断开'
      stopTimer()
      if (endingInterview.value) {
        endingInterview.value = false
        showError('面试已结束')
      }
    })
  } catch (error) {
    console.error('创建WebSocket连接失败:', error)
    showError('创建连接失败')
    scheduleReconnect()
  }
}

// 开始定时拍摄（立即拍摄一次，然后每分钟拍摄一次）
const startPeriodicCapture = () => {
  // 立即拍摄一次
  if (isCameraOn.value && wsConnected.value) {
      setTimeout(() => {
        captureAndSendImage()
      }, 3000)
  }
  
  // 每分钟拍摄一次 (60000毫秒)
  captureInterval = setInterval(() => {
    if (isCameraOn.value && wsConnected.value) {
      captureAndSendImage()
    }
  }, 60000)
}
// 停止定时拍摄
const stopPeriodicCapture = () => {
  if (captureInterval) {
    clearInterval(captureInterval)
    captureInterval = null
  }
}

// 拍摄并发送图片
const captureAndSendImage = async () => {
  try {
    // 小程序中使用camera组件的takePhoto方法
    const cameraCtx = uni.createCameraContext()
    cameraCtx.takePhoto({
      quality: 'high',
      success: (res) => {
        // 获取临时文件路径
        const tempFilePath = res.tempImagePath
        
        // 读取文件并转换为base64
        uni.getFileSystemManager().readFile({
          filePath: tempFilePath,
          encoding: 'base64',
          success: (fileRes) => {
            const base64Data = fileRes.data
            
            // 发送图片数据
            sendMessage({
              type: 'image',
              data: base64Data,
              timestamp: interviewTimer.value
            })
          },
          fail: (err) => {
            console.error('读取图片文件失败:', err)
          }
        })
      },
      fail: (err) => {
        console.error('拍摄照片失败:', err)
      }
    })
  } catch (error) {
    console.error('拍摄图片出错:', error)
  }
}

// 安排重连
const scheduleReconnect = () => {
  if (reconnectAttempts >= maxReconnectAttempts) {
    console.error('达到最大重连次数，停止重连')
    showError('连接失败，请刷新页面重试')
    return
  }

  reconnectAttempts++
  const delay = 2 ** reconnectAttempts * 1000 // 指数退避算法
  console.log(`尝试重连 ${reconnectAttempts}/${maxReconnectAttempts}，${delay/1000}秒后`)

  reconnectTimer = setTimeout(() => {
    console.log('尝试重连WebSocket...')
    connectWebSocket()
  }, delay)
}

// 关闭WebSocket连接
const closeWebSocket = (userInitiated = false) => {
    // 停止定时拍摄
  stopPeriodicCapture()
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  // 如果是用户主动结束面试，发送结束消息
  if (websocket) {
    if (userInitiated && wsConnected.value) {
      endingInterview.value = true
      console.log('用户请求结束面试，发送结束消息')
      sendMessage({
        type: 'end',
        timestamp: Date.now(),
        reason: 'user_requested'
      })
      return
    }else{
        console.log('关闭WebSocket连接')
        websocket.close()
        websocket = null
    }
  }
  wsConnected.value = false
  wsConnecting.value = false
  endingInterview.value = false
  interviewStatus.value = '面试未开启'
  stopTimer()

}

// 处理WebSocket消息
const handleWebSocketMessage = (data) => {
  console.log('收到WebSocket消息:', data)
  switch (data.type) {
    case 'question':
      // 将当前问题添加到历史记录
      if (currentQuestion.value) {
        conversationHistory.value.push({
          ...currentQuestion.value,
          type: 'question'
        })
      }

      // 更新当前问题
      currentQuestion.value = {
        content: data.question_text,
        timestamp: interviewTimer.value,
        audioData: data.audio_data 
      }

            // 处理音频数据
      if (data.audio_data) {
        try {
          // 尝试直接播放base64音频
          playBase64Audio(data.audio_data);
        } catch (error) {
          console.error('播放音频失败:', error);
          showError('音频播放失败，请点击重试');
        }
      } else {
        console.warn('收到问题但缺少音频数据');
      }

      // 如果启用了 TTS，语音播报问题文本
      if (ttsEnabled.value && data.question_text) {
        ttsService.speak(data.question_text).catch(err => {
          console.error('TTS播放失败:', err)
        })
      }

      scrollToBottom()
      break

    case 'feedback':
      // 处理面试官反馈
      console.log('收到面试反馈:', data.content)
      break

    case 'end':
      // 面试结束
      uni.hideLoading() // 先隐藏加载提示
      closeWebSocket() // 不用传true，关闭WebSocket连接
      interviewStatus.value = '面试已结束'
      stopTimer()
      uni.showModal({
        title: '面试结束',
        content: `面试结果: ${data.summary.overall_evaluation}`,
        showCancel: false,
        success: () => {
          userStore.sessionId = null // 清除session_id
          setTimeout(() => {
              uni.switchTab({
            url: '/pages/report/report'
            })
          }, 1500)
        }
      })
      userStore.sessionId=null // 清除session_id
      break

    case 'audio_ack':
      // 处理语音回答确认
      if (data.answer) {
        if (currentQuestion.value) {
          conversationHistory.value.push(
            {
              ...currentQuestion.value,
              type: 'question'
            },
            {
              type: 'answer',
              content: data.answer,
              timestamp: interviewTimer.value
            }
          )
          currentQuestion.value = null
        } else {
          conversationHistory.value.push({
            type: 'answer',
            content: data.answer,
            timestamp: interviewTimer.value
          })
        }
        scrollToBottom()
      }
      break
  }
}



function playBase64Audio(base64Data) {
  try {

      console.log('小程序环境，尝试直接播放base64音频');
      const innerAudioContext = uni.createInnerAudioContext();
      
      // 直接使用base64数据作为音频源（格式：data:audio/mp3;base64,xxx）
      innerAudioContext.src = `data:audio/mp3;base64,${base64Data}`;
      
      // 监听可以播放事件
      innerAudioContext.onCanplay(() => {
        console.log('音频可以播放，开始播放');
        try {
          // 不使用Promise链式调用，避免catch报错
          innerAudioContext.play();
        } catch (error) {
          console.error('小程序直接播放失败:', error);
          showError('音频播放失败，请重试');
          innerAudioContext.destroy();
        }
      });
      
      // 监听播放结束事件
      innerAudioContext.onEnded(() => {
        console.log('音频播放结束');
        innerAudioContext.destroy(); // 释放资源
      });
      
      // 监听错误事件
      innerAudioContext.onError((error) => {
        console.error('小程序音频播放错误:', error);
        showError(`音频错误: ${error.errMsg}`);
        innerAudioContext.destroy();
      });
      
      return; // 小程序环境下已处理，直接返回

     
  } catch (error) {
    console.error('音频播放初始化失败:', error);
    showError('音频播放初始化失败');
  }
}


// 发送WebSocket消息
const sendMessage = (message) => {
  if (websocket && wsConnected.value) {
    websocket.send({
      data: JSON.stringify(message)
    })
  } else {
    console.error('WebSocket未连接，无法发送消息')
    showError('网络连接断开，无法发送回答')
  }
}

// 计时器管理
const startTimer = () => {
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => {
    interviewTimer.value++
  }, 1000)
}

const stopTimer = () => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

// 摄像头控制
const toggleCamera = async () => {
  if (isCameraOn.value) {
    // 关闭摄像头
    isCameraOn.value = false
    uni.showToast({
      title: '摄像头已关闭',
      icon: 'none'
    })
    return
  }
  
  // 开启摄像头前检查权限
  const hasPermission = await checkAndRequestCameraPermission()
  if (hasPermission) {
    isCameraOn.value = true
    uni.showToast({
      title: '摄像头已开启',
      icon: 'none'
    })
  }
}

const handleCameraError = (e) => {
  console.error('摄像头错误:', e)
  isCameraOn.value = false
  showError('摄像头访问失败，请检查权限')
  checkCameraPermissionStatus()
}

// 麦克风控制
// 麦克风控制
const toggleMic = async () => {
  if (isMicOn.value) {
    // 关闭麦克风
    isMicOn.value = false
    await stopRecording() // 停止录音并发送
    uni.showToast({
      title: '麦克风已关闭',
      icon: 'none'
    })
    return
  }
  
  // 开启麦克风前检查权限
  const hasPermission = await checkAndRequestMicPermission()
  if (hasPermission) {
    isMicOn.value = true
    await startRecording() // 开始录音
    uni.showToast({
      title: '麦克风已开启',
      icon: 'none'
    })
  }
}

// 转换音频数据格式
const convertFloat32To16BitPCM = (input) => {
  const output = new Int16Array(input.length)
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]))
    output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
  }
  return output
}

// 开始录音
const startRecording = async () => {
  if (!wsConnected.value || isRecording.value) return

  try {
    isRecording.value = true
    audioChunks = []

    // 小程序中使用uni.getRecorderManager
    const recorderManager = uni.getRecorderManager()
    
    recorderManager.onStart(() => {
      console.log('录音开始')
    })
    
    recorderManager.onStop((res) => {
      console.log('录音结束', res.tempFilePath)
      // 录音结束后会自动触发onStop，我们在这里处理录音文件
      handleRecordedAudio(res.tempFilePath)
    })
    
    recorderManager.onError((err) => {
      console.error('录音错误:', err)
      isRecording.value = false
      showError('录音失败: ' + err.errMsg)
    })

    // 开始录音
    recorderManager.start({
      format: 'PCM',
      sampleRate: 16000,
      numberOfChannels: 1,
      encodeBitRate: 48000
    })

  } catch (error) {
    console.error('开始录音失败:', error)
    isRecording.value = false
    showError('无法开始录音')
  }
}

// 停止录音并发送
const stopRecording = async () => {
  if (!isRecording.value) return
  
  try {
    const recorderManager = uni.getRecorderManager()
    recorderManager.stop()
  } catch (error) {
    console.error('停止录音失败:', error)
    showError('停止录音失败')
  } finally {
    isRecording.value = false
  }
}

// 处理录音文件
const handleRecordedAudio = (tempFilePath) => {
  if (!tempFilePath) return
  
  // 读取录音文件并转换为base64
  uni.getFileSystemManager().readFile({
    filePath: tempFilePath,
    encoding: 'base64',
    success: (res) => {
      const base64Data = res.data
      
      // 发送音频数据
      sendMessage({
        type: 'audio',
        data: base64Data,
        timestamp: interviewTimer.value
      })
      
    },
    fail: (err) => {
      console.error('读取录音文件失败:', err)
      showError('处理录音失败')
    }
  })
}


// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value = scrollTop.value + 1000
  })
}

// 发送文本回答
const sendTextAnswer = () => {
  if (!textAnswer.value.trim() || !wsConnected.value) return

  const answer = {
    type: 'text',
    data: textAnswer.value,
    timestamp: interviewTimer.value
  }
  sendMessage(answer)

  // 更新对话历史
  if (currentQuestion.value) {
    conversationHistory.value.push(
      {
        ...currentQuestion.value,
        type: 'question'
      },
      {
        type: 'answer',
        content: textAnswer.value,
        timestamp: interviewTimer.value
      }
    )
    currentQuestion.value = null
  } else {
    conversationHistory.value.push({
      type: 'answer',
      content: textAnswer.value,
      timestamp: interviewTimer.value
    })
  }

  textAnswer.value = ''
  scrollToBottom()
}

// 会话控制方法
const sessionControls = {
  // 暂停面试
  async pauseSession(sessionId) {
    try {
      const response = await http.put(ENDPOINTS.interview.sessionPause(sessionId))
      return response
    } catch (error) {
      console.error('暂停面试失败:', error)
      throw error
    }
  },

  // 恢复面试
  async resumeSession(sessionId) {
    try {
      const response = await http.put(ENDPOINTS.interview.sessionResume(sessionId))
      return response
    } catch (error) {
      console.error('恢复面试失败:', error)
      throw error
    }
  },

  // 结束面试
  async endSession(sessionId) {
    try {
      const response = await http.post(ENDPOINTS.interview.sessionEnd(sessionId))
      return response
    } catch (error) {
      console.error('结束面试失败:', error)
      throw error
    }
  },

  // 取消面试
  async cancelSession(sessionId) {
    try {
      const response = await http.post(ENDPOINTS.interview.sessionCancel(sessionId))
      return response
    } catch (error) {
      console.error('取消面试失败:', error)
      throw error
    }
  }
}

// 暂停面试
async function handlePause() {
  if (!currentSession.value?.id && !userStore.sessionId) return

  const sessionId = currentSession.value?.id || userStore.sessionId

  try {
    uni.showLoading({ title: '暂停中...' })
    const response = await sessionControls.pauseSession(sessionId)
    sessionStatus.value = 'paused'

    // 暂停计时器
    if (timerInterval) {
      clearInterval(timerInterval)
      timerInterval = null
    }

    uni.showToast({ title: '已暂停', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: '暂停失败', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

// 恢复面试
async function handleResume() {
  if (!currentSession.value?.id && !userStore.sessionId) return

  const sessionId = currentSession.value?.id || userStore.sessionId

  try {
    uni.showLoading({ title: '恢复中...' })
    const response = await sessionControls.resumeSession(sessionId)
    sessionStatus.value = 'in_progress'

    // 恢复计时器
    startTimer()

    uni.showToast({ title: '已恢复', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: '恢复失败', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

// 结束面试
async function handleEnd() {
  if (!currentSession.value?.id && !userStore.sessionId) return

  const sessionId = currentSession.value?.id || userStore.sessionId

  uni.showModal({
    title: '确认结束',
    content: '确定要结束当前面试吗？结束后将生成评估报告。',
    success: async (res) => {
      if (res.confirm) {
        try {
          endingInterview.value = true
          uni.showLoading({ title: '正在结束面试...' })

          // 1. 调用结束API
          await sessionControls.endSession(sessionId)
          sessionStatus.value = 'completed'

          // 2. 关闭 WebSocket
          closeWebSocket()

          // 3. 跳转到报告页面
          uni.redirectTo({
            url: `/pages/report/report?sessionId=${sessionId}`
          })
        } catch (error) {
          uni.showToast({ title: '结束失败', icon: 'none' })
          endingInterview.value = false
        } finally {
          uni.hideLoading()
        }
      }
    }
  })
}

// 取消面试
async function handleCancel() {
  if (!currentSession.value?.id && !userStore.sessionId) return

  const sessionId = currentSession.value?.id || userStore.sessionId

  uni.showModal({
    title: '确认取消',
    content: '确定要取消当前面试吗？取消后无法恢复。',
    success: async (res) => {
      if (res.confirm) {
        try {
          uni.showLoading({ title: '取消中...' })
          await sessionControls.cancelSession(sessionId)
          sessionStatus.value = 'cancelled'

          // 清理状态
          currentSession.value = null
          userStore.sessionId = null
          uni.navigateBack()
        } catch (error) {
          uni.showToast({ title: '取消失败', icon: 'none' })
        } finally {
          uni.hideLoading()
        }
      }
    }
  })
}

// 切换面试状态
const toggleInterview = () => {
  if (!wsConnected.value) {
    // 开始面试
    connectWebSocket()
  } else {
    // 结束面试
    uni.showModal({
      title: '确认结束面试',
      content: '确定要结束本次面试吗？结束后将无法继续回答',
      confirmText: '结束面试',
      confirmColor: 'var(--color-error)',
      success: (res) => {
        if (res.confirm) {
          // 用户确认结束，显示等待提示
          uni.showLoading({
            title: '正在结束面试，评估中...',
            mask: true
          })
          closeWebSocket(true) // 传true表示用户主动结束面试，发送结束消息
          // 设置超时自动隐藏loading（防止网络问题导致一直显示）
          setTimeout(() => {
            uni.hideLoading()
          }, 15000)
        }
      }
    })
  }
}

onShow(async () => {
  await checkAndRequestCameraPermission()
  await checkAndRequestMicPermission()

})

onUnmounted(() => {
  closeWebSocket()
  stopPeriodicCapture()
  stopRecording()
})
</script>

<style>
/* 基础样式 - 移动优先 */
.interview-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-page);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  box-sizing: border-box;
}

/* 顶部信息栏 */
.header-bar {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 12px 16px;
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-default);
  position: sticky;
  top: 0;
  z-index: 10;
  width: 100%;
  box-sizing: border-box;
  gap:18px;
}

.header-bar .title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-left:14px;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 18px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.status-item.timer {
  min-width: 40px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  justify-content: center;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 16px;
  gap: 16px;
  width: 100%;
  box-sizing: border-box;
}

/* 通用区块样式 */
.conversation-section,
.answer-section,
.video-section,
.info-section {
  width: 100%;
  box-sizing: border-box;
  background-color: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

/* 区块标题通用样式 */
.section-title, .panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 对话区域 */
.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-default);
}

.interviewer-info {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.interviewer-name {
  font-size: 14px;
  color: var(--text-secondary);
}

.speaking-indicator {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--color-error);
  display: flex;
  align-items: center;
  justify-content: center;
}

.pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--color-error-light);
  animation: pulse 1.5s infinite;
}

.conversation-container {
  height: 220px;
  padding: 16px;
  overflow-y: auto;
  width: 100%;
  box-sizing: border-box;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  text-align: center;
}

.empty-text {
  font-size: 14px;
  margin-top: 8px;
}

.message {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  max-width: 100%;
}

.message:last-child {
  margin-bottom: 0;
}

.message-content {
  max-width: 85%;
  padding: 10px 12px;
  border-radius: 12px;
  margin-bottom: 4px;
  font-size: 14px;
  line-height: 1.4;
  word-break: break-word;
}

.message-content.question {
  background-color: var(--bg-subtle);
  border-bottom-left-radius: 4px;
  align-self: flex-start;
}

.message-content.answer {
  background-color: var(--color-primary);
  color: var(--text-inverse);
  border-bottom-right-radius: 4px;
  align-self: flex-end;
}

.message-time {
  font-size: 10px;
  color: var(--text-tertiary);
  display: block;
  margin-top: 2px;
}

.message.question .message-time {
  text-align: left;
  padding-left: 12px;
}

.message.answer .message-time {
  text-align: right;
  padding-right: 12px;
}

/* 回答区域 */
.answer-section {
  padding: 16px;
}

.answer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.answer-count {
  font-size: 12px;
  color: var(--text-tertiary);
}

.answer-input {
  width: 100%;
  min-height: 70px;
  padding: 12px;
  max-height: 100px;
  background-color: var(--bg-input);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.5;
  margin-bottom: 12px;
  resize: none;
  box-sizing: border-box;
}

.answer-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.device-controls {
  display: flex;
  gap: 8px;
}

.control-btn {
  padding: 6px 12px;
  border-radius: 16px;
  border: none;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  background-color: var(--color-neutral-400);
  color: var(--text-inverse);
  cursor: pointer;
  white-space: nowrap;
}

.control-btn.active {
  background: var(--color-primary);
  border: 1px solid var(--color-primary-light);
} 

.control-btn.primary {
  color: var(--text-inverse) !important;
  font-size: 14px;
  min-width:60px;
  justify-content: center;
  align-items: center;
  background-color: var(--color-primary);
  margin:auto 20px ;
}

.control-btn.danger {
  color: var(--text-inverse) !important;
  font-size: 14px;
  min-width:60px;
  justify-content: center;
  align-items: center;
  background-color: var(--color-error);
}

.control-btn.warning {
  color: var(--text-inverse) !important;
  font-size: 14px;
  min-width:60px;
  justify-content: center;
  align-items: center;
  background-color: var(--color-warning);
}

.control-btn.secondary {
  color: var(--text-secondary) !important;
  font-size: 14px;
  min-width:60px;
  justify-content: center;
  align-items: center;
  background-color: var(--bg-tertiary);
}

.control-btn.small {
  padding: 2px;
  border-radius: 30%;
  width: 36px;
  height: 36px;
  justify-content: center;
}


.send-btn {
  padding: 8px 16px;
  border-radius: 16px;
  color: var(--text-inverse) !important;
  background-color: var(--color-primary);
  border: none;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  cursor: pointer;
  justify-content: center;
  margin-right:4px
}

.send-btn.disabled {
  background-color: var(--color-neutral-400) !important;
  color: var(--text-inverse) !important;
  cursor: not-allowed;
}

/* 视频区域 */
.video-section {
  overflow: hidden;
}

.video-section .section-title {
  padding: 12px 16px;
  display: block;
  border-bottom: 1px solid var(--border-default);
}

.video-container {
  width: 100%;
  height: 200px;
  background-color: var(--color-neutral-900);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.camera-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.camera-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  width: 100%;
  height: 100%;
}

.camera-placeholder text {
  font-size: 14px;
  margin-top: 8px;
}

/* 信息面板区域 */
.info-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: none;
  box-shadow: none;
  padding: 0;
}

.info-panel {
  padding: 16px;
  width: 100%;
  box-sizing: border-box;
}

.panel-title {
  margin-bottom: 12px;
  display: block;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
  width: 100%;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-light);
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: var(--text-secondary);
}

.info-value {
  font-weight: 500;
  text-align: right;
}

.info-value.success {
  color: var(--color-success);
}

.info-value.warning {
  color: var(--color-warning);
}

/* 错误提示 */
.error-toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background-color: var(--color-error);
  color: var(--text-inverse);
  padding: 10px 16px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  z-index: 100;
  animation: fadeIn 0.3s ease-in-out;
  max-width: 90%;
  text-align: center;
}

/* 动画 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px) translateX(-50%); }
  to { opacity: 1; transform: translateY(0) translateX(-50%); }
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1.2); opacity: 0; }
}

/* 平板及以上设备响应式设计 */
@media (min-width: 768px) {
  .interview-container {
    padding: 0;
  }
  
  .header-bar {
    padding: 16px 24px;
  }
  
  .header-bar .title {
    font-size: 20px;
    text-align: left;
    flex: none;
  }
  
  .status-item {
    font-size: 14px;
  }
  
  .control-btn {
    padding: 8px 16px;
    font-size: 14px;
  }
  
  .main-content {
    padding: 24px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto auto;
    grid-template-areas:
      "conversation video"
      "conversation info"
      "answer info";
    gap: 20px;
  }
  
  .conversation-section {
    grid-area: conversation;
    height: calc(100vh - 180px);
  }
  
  .conversation-container {
    height: calc(100% - 56px);
  }
  
  .answer-section {
    grid-area: answer;
  }
  
  .video-section {
    grid-area: video;
  }
  
  .info-section {
    grid-area: info;
  }
  
  .avatar {
    width: 40px;
    height: 40px;
  }
  
  .video-container {
    height: 240px;
  }
}

/* 桌面设备响应式设计 */
@media (min-width: 1024px) {
  .main-content {
    grid-template-columns: 2fr 1fr;
  }
  
  .video-container {
    height: 280px;
  }
}

/* #ifdef MP-WEIXIN */
@media (max-width: 568px) {
  .interview-container{
    margin-top:80px;
  }
}
/* #endif */
</style>