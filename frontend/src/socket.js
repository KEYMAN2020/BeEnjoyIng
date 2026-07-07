/**
 * Socket.IO 实时通信服务
 *
 * 使用方式：
 *   import { socketService } from '@/socket'
 *   await socketService.connect()              // App.vue onMounted
 *   socketService.joinPrivate(otherUserId)      // 进入私聊
 *   socketService.onPrivateMessage(callback)    // 监听新消息
 *   socketService.sendPrivate(receiverId, msg)  // 发送私信
 *   socketService.leavePrivate(otherUserId)     // 离开私聊
 *   socketService.disconnect()                  // App.vue onUnmounted
 */

import { io } from "socket.io-client"
import { ref } from "vue"

const SOCKET_URL = "/"   // 与 HTTP 同源，Socket.IO 自动 path

class SocketService {
  constructor() {
    this._socket = null
    this.connected = ref(false)
    this._listeners = new Map()
  }

  /** 建立连接 */
  async connect() {
    if (this._socket?.connected) return

    const token = localStorage.getItem("token")
    if (!token) return

    return new Promise((resolve) => {
      this._socket = io(SOCKET_URL, {
        auth: { token },
        query: { token },
        transports: ["websocket", "polling"],
        upgrade: true,
        rememberUpgrade: true,
        reconnection: true,
        reconnectionDelay: 500,
        reconnectionDelayMax: 3000,
        reconnectionAttempts: 20,
        timeout: 5000,
      })

      this._socket.on("connect", () => {
        this.connected.value = true
        resolve()
      })

      this._socket.on("disconnect", () => {
        this.connected.value = false
      })

      this._socket.on("connect_error", () => {
        this.connected.value = false
        resolve()  // 连接失败也不阻塞
      })
    })
  }

  /** 断开连接 */
  disconnect() {
    if (this._socket) {
      this._socket.disconnect()
      this._socket = null
      this.connected.value = false
    }
  }

  // ── 私聊 ──────────────────────────────────────

  joinPrivate(otherUserId) {
    this._socket?.emit("private_join", { other_id: otherUserId })
  }

  leavePrivate(otherUserId) {
    this._socket?.emit("private_leave", { other_id: otherUserId })
  }

  sendPrivate(receiverId, content) {
    this._socket?.emit("private_send", { receiver_id: receiverId, content })
  }

  onPrivateMessage(callback) {
    this._on("private_message", callback)
  }
  offPrivateMessage(callback) {
    this._off("private_message", callback)
  }

  onPrivateRead(callback) {
    this._on("private_read", callback)
  }
  offPrivateRead(callback) {
    this._off("private_read", callback)
  }

  // ── 群聊 ──────────────────────────────────────

  joinGroup(groupId) {
    this._socket?.emit("group_join", { group_id: groupId })
  }

  leaveGroup(groupId) {
    this._socket?.emit("group_leave", { group_id: groupId })
  }

  sendGroup(groupId, content) {
    this._socket?.emit("group_send", { group_id: groupId, content })
  }

  onGroupMessage(callback) {
    this._on("group_message", callback)
  }
  offGroupMessage(callback) {
    this._off("group_message", callback)
  }

  // ── 内部 ──────────────────────────────────────

  _on(event, callback) {
    this._socket?.on(event, callback)
    if (!this._listeners.has(event)) this._listeners.set(event, [])
    this._listeners.get(event).push(callback)
  }

  _off(event, callback) {
    this._socket?.off(event, callback)
    const list = this._listeners.get(event)
    if (list) {
      this._listeners.set(event, list.filter(cb => cb !== callback))
    }
  }
}

export const socketService = new SocketService()
