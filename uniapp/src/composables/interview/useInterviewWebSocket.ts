/**
 * WebSocket composable used by interview pages.
 * Handles connect / reconnect / heartbeat with a manual-close escape hatch.
 */

import { ref, onUnmounted } from 'vue';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface UseWebSocketOptions {
  url: string | (() => string);
  onMessage: (msg: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  heartbeatInterval?: number;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useInterviewWebSocket(options: UseWebSocketOptions) {
  const status = ref<WebSocketStatus>('disconnected');
  const ws = ref<UniApp.SocketTask | null>(null);
  const reconnectAttempts = ref(0);
  let manuallyDisconnected = false;
  let heartbeatTimer: number | null = null;
  let reconnectTimer: number | null = null;

  const {
    url,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    heartbeatInterval = 30000,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
  } = options;

  const clearHeartbeat = () => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
  };

  const startHeartbeat = () => {
    clearHeartbeat();
    heartbeatTimer = setInterval(() => {
      send({ type: 'ping' });
    }, heartbeatInterval) as unknown as number;
  };

  const getUrl = (): string => {
    return typeof url === 'function' ? url() : url;
  };

  const attemptReconnect = () => {
    if (manuallyDisconnected) {
      return;
    }

    if (reconnectAttempts.value >= maxReconnectAttempts) {
      console.log('[WebSocket] Maximum reconnect attempts reached');
      return;
    }

    reconnectAttempts.value += 1;
    console.log(`[WebSocket] Reconnecting in ${reconnectInterval}ms (${reconnectAttempts.value}/${maxReconnectAttempts})`);

    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
    }

    reconnectTimer = setTimeout(() => {
      connect();
    }, reconnectInterval) as unknown as number;
  };

  const connect = (): void => {
    if (status.value === 'connecting' || status.value === 'connected') {
      return;
    }

    const actualUrl = getUrl();
    if (!actualUrl) {
      console.warn('[WebSocket] Missing URL');
      return;
    }

    manuallyDisconnected = false;
    status.value = 'connecting';

    ws.value = uni.connectSocket({
      url: actualUrl,
      success: () => {
        console.log('[WebSocket] Connect request sent', actualUrl);
      },
      fail: (err) => {
        console.error('[WebSocket] Connect failed:', err);
        status.value = 'error';
        onError?.(err as unknown as Event);
        attemptReconnect();
      }
    });

    ws.value?.onOpen(() => {
      console.log('[WebSocket] Connected');
      status.value = 'connected';
      reconnectAttempts.value = 0;
      startHeartbeat();
      onConnect?.();
    });

    ws.value?.onMessage((res) => {
      try {
        const msg = JSON.parse(res.data as string);
        onMessage(msg);
      } catch (err) {
        console.error('[WebSocket] Failed to parse message:', err);
      }
    });

    ws.value?.onClose(() => {
      console.log('[WebSocket] Closed');
      status.value = 'disconnected';
      clearHeartbeat();
      onDisconnect?.();
      if (!manuallyDisconnected) {
        attemptReconnect();
      }
    });

    ws.value?.onError((err) => {
      console.error('[WebSocket] Error:', err);
      status.value = 'error';
      onError?.(err);
    });
  };

  const send = (data: object): boolean => {
    if (status.value !== 'connected' || !ws.value) {
      console.warn('[WebSocket] Cannot send before connection is ready');
      return false;
    }

    try {
      ws.value.send({
        data: JSON.stringify(data)
      });
      return true;
    } catch (err) {
      console.error('[WebSocket] Send failed:', err);
      return false;
    }
  };

  const disconnect = (): void => {
    manuallyDisconnected = true;
    clearHeartbeat();
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    ws.value?.close({});
    status.value = 'disconnected';
    ws.value = null;
  };

  onUnmounted(() => {
    disconnect();
  });

  return {
    status,
    connect,
    disconnect,
    send
  };
}
