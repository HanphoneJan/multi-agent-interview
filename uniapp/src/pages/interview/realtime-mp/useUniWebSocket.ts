/**
 * 小程序 WebSocket 封装
 * 用于实时面试的 WebSocket 连接管理
 */

import { ref, onUnmounted } from 'vue'

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export interface UseUniWebSocketOptions {
  url: string | (() => string)
  onMessage?: (msg: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: any) => void
  heartbeatInterval?: number
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export function useUniWebSocket(options: UseUniWebSocketOptions) {
  const status = ref<WebSocketStatus>('disconnected')
  const ws = ref<UniApp.SocketTask | null>(null)
  const reconnectAttempts = ref(0)

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
    heartbeatTimer = setInterval(() => {
      send({ type: 'ping' })
    }, heartbeatInterval) as unknown as number
  }

  const connect = (): void => {
    if (status.value === 'connecting' || status.value === 'connected') {
      return
    }

    const actualUrl = getUrl()
    if (!actualUrl) {
      console.warn('[WebSocket] URL 为空，无法连接')
      return
    }

    status.value = 'connecting'
    console.log('[WebSocket] 正在连接:', actualUrl)

    ws.value = uni.connectSocket({
      url: actualUrl,
      success: () => {
        console.log('[WebSocket] 连接请求已发送')
      },
      fail: (err) => {
        console.error('[WebSocket] 连接失败:', err)
        status.value = 'error'
        onError?.(err)
        attemptReconnect()
      }
    })

    // 监听打开
    ws.value?.onOpen(() => {
      console.log('[WebSocket] 连接成功')
      status.value = 'connected'
      reconnectAttempts.value = 0
      startHeartbeat()
      onConnect?.()
    })

    // 监听消息
    ws.value?.onMessage((res) => {
      try {
        const msg = JSON.parse(res.data as string)
        // 忽略 ping/pong
        if (msg.type === 'pong') return
        onMessage?.(msg)
      } catch (err) {
        console.error('[WebSocket] 消息解析失败:', err)
      }
    })

    // 监听关闭
    ws.value?.onClose(() => {
      console.log('[WebSocket] 连接关闭')
      status.value = 'disconnected'
      clearHeartbeat()
      onDisconnect?.()
      attemptReconnect()
    })

    // 监听错误
    ws.value?.onError((err) => {
      console.error('[WebSocket] 错误:', err)
      status.value = 'error'
      onError?.(err)
    })
  }

  const send = (data: object): boolean => {
    if (status.value !== 'connected' || !ws.value) {
      console.warn('[WebSocket] 未连接，无法发送消息')
      return false
    }

    try {
      ws.value.send({
        data: JSON.stringify(data)
      })
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

    reconnectTimer = setTimeout(() => {
      connect()
    }, reconnectInterval) as unknown as number
  }

  const disconnect = (): void => {
    clearHeartbeat()
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws.value?.close({})
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
