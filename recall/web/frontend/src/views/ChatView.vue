<script setup>
import { ref, nextTick, onMounted, onUnmounted, watch } from 'vue'
import {
  sendMessage,
  getAIMessages,
  getConversations,
  createConversation,
  deleteConversation,
  setActiveConversation,
  getConversationMessages
} from '../api'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

// 对话列表
const conversations = ref([])
const currentConversationId = ref(null)

// 消息列表
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const messagesContainer = ref(null)

let pollTimer = null
let lastMessageId = 0

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 加载对话列表
async function loadConversations() {
  const result = await getConversations()
  conversations.value = result.conversations || []

  // 如果有对话，选择第一个活跃的或最新的
  if (conversations.value.length > 0) {
    const active = conversations.value.find(c => c.is_active)
    if (active) {
      await selectConversation(active.id)
    } else {
      await selectConversation(conversations.value[0].id)
    }
  }
}

// 选择对话
async function selectConversation(convId) {
  if (currentConversationId.value === convId) return

  currentConversationId.value = convId
  lastMessageId = 0
  messages.value = []

  // 设置为活跃对话
  await setActiveConversation(convId)

  // 加载对话消息
  const result = await getConversationMessages(convId)
  if (result.messages && result.messages.length > 0) {
    messages.value = result.messages
    lastMessageId = result.messages[result.messages.length - 1].id
    scrollToBottom()
  }
}

// 创建新对话
async function handleNewConversation() {
  const result = await createConversation('新对话')
  if (result.success) {
    await loadConversations()
    await selectConversation(result.conversation_id)
  }
}

// 删除对话
async function handleDeleteConversation(convId, event) {
  event.stopPropagation()
  if (!confirm('确定要删除这个对话吗？')) return

  await deleteConversation(convId)
  await loadConversations()

  // 如果删除的是当前对话，切换到其他对话
  if (currentConversationId.value === convId) {
    if (conversations.value.length > 0) {
      await selectConversation(conversations.value[0].id)
    } else {
      currentConversationId.value = null
      messages.value = []
    }
  }
}

// 轮询消息
async function pollMessages() {
  if (!currentConversationId.value) return

  try {
    const result = await getAIMessages(lastMessageId, currentConversationId.value)
    if (result.messages && result.messages.length > 0) {
      let hasNewMessages = false
      for (const msg of result.messages) {
        // 查找是否已存在
        const existingIdx = messages.value.findIndex(m => m.id === msg.id)
        if (existingIdx !== -1) {
          // 更新已存在的消息（可能是 pending -> done）
          messages.value[existingIdx] = msg
        } else {
          // 新消息
          messages.value.push(msg)
          hasNewMessages = true
        }
      }
      lastMessageId = result.last_id
      if (hasNewMessages) scrollToBottom()
    }
  } catch (e) {
    console.error('轮询消息失败:', e)
  }
}

// 发送消息
async function handleSend() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  inputText.value = ''
  loading.value = true

  // 如果没有当前对话，先创建一个
  let convId = currentConversationId.value
  if (!convId) {
    const result = await createConversation('新对话')
    if (result.success) {
      convId = result.conversation_id
      currentConversationId.value = convId
      await loadConversations()
    } else {
      loading.value = false
      return
    }
  }

  // 发送消息
  const result = await sendMessage(text, convId)
  loading.value = false

  if (result.error) {
    messages.value.push({ role: 'system', content: `错误: ${result.error}` })
    scrollToBottom()
  } else {
    // 更新对话列表（标题可能已更新）
    await loadConversations()
  }
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadConversations()
  pollTimer = setInterval(pollMessages, 1000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="h-full flex">
    <!-- 侧边栏：对话列表 -->
    <div class="w-64 border-r border-gray-200 bg-gray-50 flex flex-col">
      <!-- 新建对话按钮 -->
      <div class="p-3 border-b border-gray-200">
        <button
          @click="handleNewConversation"
          class="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center justify-center gap-2"
        >
          <span>+</span>
          <span>新对话</span>
        </button>
      </div>

      <!-- 对话列表 -->
      <div class="flex-1 overflow-auto">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          @click="selectConversation(conv.id)"
          :class="[
            'px-4 py-3 cursor-pointer border-b border-gray-100 hover:bg-gray-100 group',
            currentConversationId === conv.id ? 'bg-primary-50 border-l-4 border-l-primary-600' : ''
          ]"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1 truncate">
              <div class="font-medium text-gray-800 truncate">{{ conv.title }}</div>
              <div class="text-xs text-gray-400 mt-1">{{ formatTime(conv.updated_at) }}</div>
            </div>
            <button
              @click="handleDeleteConversation(conv.id, $event)"
              class="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500"
              title="删除对话"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        <div v-if="conversations.length === 0" class="p-4 text-center text-gray-400">
          暂无对话
        </div>
      </div>
    </div>

    <!-- 主区域：聊天界面 -->
    <div class="flex-1 flex flex-col">
      <!-- 消息列表 -->
      <div ref="messagesContainer" class="flex-1 overflow-auto p-4 space-y-4">
        <div v-if="!currentConversationId" class="text-center text-gray-400 mt-20">
          <div class="text-4xl mb-4">💬</div>
          <div>点击左侧"新对话"开始聊天</div>
        </div>

        <div v-else-if="messages.length === 0" class="text-center text-gray-400 mt-20">
          <div class="text-4xl mb-4">💬</div>
          <div>开始与 AI 助手对话</div>
          <div class="text-sm mt-2">AI 会主动探索你的活动并提问</div>
        </div>

        <div
          v-for="(msg, idx) in messages"
          :key="msg.id || idx"
          :class="[
            'max-w-[80%] p-3 rounded-lg',
            msg.role === 'user'
              ? 'ml-auto bg-primary-600 text-white'
              : 'bg-white border border-gray-200'
          ]"
        >
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="whitespace-pre-wrap">{{ msg.content }}</div>

          <!-- AI 消息 -->
          <div v-else>
            <!-- pending 状态：显示回复中 -->
            <div v-if="msg.status === 'pending'" class="flex items-center gap-2 text-gray-400">
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
              <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              <span class="ml-2">回复中...</span>
            </div>
            <!-- done 状态：显示内容 -->
            <MarkdownRenderer v-else :content="msg.content" />
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="border-t border-gray-200 p-4 bg-white">
        <div class="flex gap-2">
          <textarea
            v-model="inputText"
            @keydown="handleKeydown"
            placeholder="输入消息..."
            rows="1"
            :disabled="!currentConversationId && conversations.length === 0"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100"
          ></textarea>
          <button
            @click="handleSend"
            :disabled="loading || !inputText.trim()"
            class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
