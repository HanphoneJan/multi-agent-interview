/**
 * H5 浏览器原生 WebSocket 封装
 * 用于实时面试的 WebSocket 连接管理
 */

import { ref, onUnmounted } from 'vue'

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export interface UseBrowserWebSocketOptions {
  url: string | (() => string)
  onMessage?: (msg: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
  heartbeatInterval?: number
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export function useBrowserWebSocket(options: UseBrowserWebSocketOptions) {
  const status = ref<WebSocketStatus>('disconnected')
  const ws = ref<WebSocket | null>(null)
  const reconnectAttempts = ref(0)
  const isManuallyClosed = ref(false)

  const {
    url,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    heartbeatInterval = 30000,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
  } = options

  let heartbeatTimer: number | null = null
  let reconnectTimer: number | null = null

  const getUrl = (): string => {
    return typeof url === 'function' ? url() : url
  }

  const clearHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  const startHeartbeat = () => {
    clearHeartbeat()
    heartbeatTimer = window.setInterval(() => {
      send({ type: 'ping' })
    }, heartbeatInterval)
  }

  const connect = (): void => {
    if (status.value === 'connecting' || status.value === 'connected') {
      return
    }
    // 重置手动关闭标志
    isManuallyClosed.value = false

    const actualUrl = getUrl()
    if (!actualUrl) {
      console.warn('[WebSocket] URL 为空，无法连接')
      return
    }

    status.value = 'connecting'
    console.log('[WebSocket] 正在连接:', actualUrl)

    try {
      ws.value = new WebSocket(actualUrl)

      ws.value.onopen = () => {
        console.log('[WebSocket] 连接成功')
        status.value = 'connected'
        reconnectAttempts.value = 0
        startHeartbeat()
        onConnect?.()
      }

      ws.value.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          // 忽略 ping/pong
          if (msg.type === 'pong') return
          onMessage?.(msg)
        } catch (err) {
          console.error('[WebSocket] 消息解析失败:', err)
        }
      }

      ws.value.onclose = () => {
        console.log('[WebSocket] 连接关闭, 手动关闭:', isManuallyClosed.value)
        status.value = 'disconnected'
        clearHeartbeat()
        onDisconnect?.()
        // 只有非手动关闭时才重连
        if (!isManuallyClosed.value) {
          attemptReconnect()
        }
        isManuallyClosed.value = false
      }

      ws.value.onerror = (err) => {
        console.error('[WebSocket] 错误:', err)
        status.value = 'error'
        onError?.(err)
      }
    } catch (err) {
      console.error('[WebSocket] 创建连接失败:', err)
      status.value = 'error'
      attemptReconnect()
    }
  }

  const send = (data: object): boolean => {
    if (status.value !== 'connected' || !ws.value) {
      console.warn('[WebSocket] 未连接，无法发送消息')
      return false
    }

    try {
      ws.value.send(JSON.stringify(data))
      return true
    } catch (err) {
      console.error('[WebSocket] 发送失败:', err)
      return false
    }
  }

  const attemptReconnect = () => {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      console.log('[WebSocket] 达到最大重连次数，停止重连')
      return
    }

    reconnectAttempts.value++
    console.log(`[WebSocket] ${reconnectInterval}ms 后尝试第 ${reconnectAttempts.value} 次重连`)

    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
    }

    reconnectTimer = window.setTimeout(() => {
      connect()
    }, reconnectInterval)
  }

  const disconnect = (manual: boolean = true): void => {
    // 设置手动关闭标志，防止重连
    isManuallyClosed.value = manual
    clearHeartbeat()
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws.value?.close()
    status.value = 'disconnected'
    ws.value = null
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    status,
    connect,
    disconnect,
    send
  }
}
