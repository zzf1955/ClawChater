<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getStatus } from '../api'

const props = defineProps(['current'])
const emit = defineEmits(['update:current'])

const status = ref({ running: false, total_screenshots: 0, pending_ocr: 0 })
let timer = null

const navItems = [
  { id: 'browser', label: '截图浏览', icon: '📷' },
  { id: 'config', label: '配置', icon: '⚙️' }
]

async function refreshStatus() {
  status.value = await getStatus()
}

onMounted(() => {
  refreshStatus()
  timer = setInterval(refreshStatus, 5000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <aside class="w-52 bg-white border-r border-gray-200 flex flex-col">
    <!-- Logo -->
    <div class="px-4 py-5">
      <h1 class="text-xl font-bold text-primary-600">Recall</h1>
    </div>

    <!-- 导航 -->
    <nav class="flex-1 px-3">
      <button
        v-for="item in navItems"
        :key="item.id"
        @click="emit('update:current', item.id)"
        :class="[
          'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors mb-1',
          current === item.id
            ? 'bg-primary-600 text-white'
            : 'text-gray-600 hover:bg-gray-100'
        ]"
      >
        <span>{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <!-- 状态面板 -->
    <div class="p-3">
      <div class="bg-gray-50 rounded-lg p-3 text-sm">
        <div class="flex items-center gap-2 mb-2">
          <span
            :class="[
              'w-2 h-2 rounded-full',
              status.running ? 'bg-green-500' : 'bg-red-500'
            ]"
          ></span>
          <span class="text-gray-600">
            {{ status.running ? '运行中' : '已停止' }}
          </span>
        </div>
        <div class="text-gray-500 space-y-1">
          <div>总截图: {{ status.total_screenshots }}</div>
          <div>待OCR: {{ status.pending_ocr }}</div>
        </div>
      </div>
    </div>
  </aside>
</template>
