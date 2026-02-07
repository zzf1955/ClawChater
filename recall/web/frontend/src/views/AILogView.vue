<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getAILogs } from '../api'

const logs = ref([])
let pollTimer = null

async function loadLogs() {
  try {
    const result = await getAILogs(100)
    if (result.logs) {
      logs.value = result.logs
    }
  } catch (e) {
    console.error('获取日志失败:', e)
  }
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour12: false })
}

function getActionLabel(action) {
  const labels = {
    'start': '启动',
    'stop': '停止',
    'explore': '探索',
    'user_message': '用户消息',
    'tool_call': '工具调用',
    'llm_error': 'LLM 错误',
    'error': '错误'
  }
  return labels[action] || action
}

function getActionClass(action) {
  if (action === 'error' || action === 'llm_error') {
    return 'bg-red-100 text-red-700'
  }
  if (action === 'user_message') {
    return 'bg-blue-100 text-blue-700'
  }
  if (action === 'tool_call') {
    return 'bg-purple-100 text-purple-700'
  }
  if (action === 'explore') {
    return 'bg-green-100 text-green-700'
  }
  return 'bg-gray-100 text-gray-700'
}

onMounted(() => {
  loadLogs()
  pollTimer = setInterval(loadLogs, 3000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="h-full overflow-auto">
    <div class="max-w-4xl mx-auto p-6">
      <h2 class="text-xl font-semibold text-gray-800 mb-6">AI 后台日志</h2>

      <div v-if="logs.length === 0" class="text-center text-gray-400 mt-20">
        <div class="text-4xl mb-4">📋</div>
        <div>暂无日志</div>
        <div class="text-sm mt-2">AI 的后台活动会显示在这里</div>
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="log in logs"
          :key="log.id"
          class="bg-white rounded-lg border border-gray-200 p-3 flex items-start gap-3"
        >
          <span class="text-xs text-gray-400 whitespace-nowrap mt-0.5">
            {{ formatTime(log.timestamp) }}
          </span>
          <span
            :class="[
              'px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap',
              getActionClass(log.action)
            ]"
          >
            {{ getActionLabel(log.action) }}
          </span>
          <span class="text-sm text-gray-600 break-all">
            {{ log.detail || '-' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
