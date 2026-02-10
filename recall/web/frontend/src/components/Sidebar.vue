<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getStatus } from '../api'

const props = defineProps(['current'])
const emit = defineEmits(['update:current'])

const status = ref({ running: false, total_screenshots: 0, pending_ocr: 0 })
let timer = null

const navItems = [
  { id: 'browser', label: '截图浏览', icon: 'photo' },
  { id: 'config', label: '系统配置', icon: 'settings' }
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
  <aside class="w-56 bg-white border-r border-gray-200 flex flex-col">
    <!-- Logo区域 -->
    <div class="px-5 py-6 border-b border-gray-100">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        <h1 class="text-lg font-semibold text-gray-900 tracking-tight">Recall</h1>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="flex-1 px-3 py-4">
      <button
        v-for="item in navItems"
        :key="item.id"
        @click="emit('update:current', item.id)"
        :class="[
          'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors duration-150 mb-1',
          current === item.id
            ? 'bg-gray-100 text-gray-900 font-medium'
            : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
        ]"
      >
        <!-- 图片图标 -->
        <svg v-if="item.icon === 'photo'" class="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <!-- 设置图标 -->
        <svg v-if="item.icon === 'settings'" class="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <!-- 状态面板 -->
    <div class="px-4 py-4 border-t border-gray-100">
      <div class="flex items-center gap-2 mb-3">
        <div
          :class="[
            'w-2 h-2 rounded-full',
            status.running
              ? 'bg-emerald-500'
              : 'bg-gray-300'
          ]"
        ></div>
        <span class="text-xs text-gray-500">
          {{ status.running ? '运行中' : '已停止' }}
        </span>
      </div>
      <div class="flex gap-4">
        <div>
          <div class="text-lg font-semibold text-gray-900">{{ status.total_screenshots }}</div>
          <div class="text-xs text-gray-400">截图</div>
        </div>
        <div>
          <div class="text-lg font-semibold text-gray-900">{{ status.pending_ocr }}</div>
          <div class="text-xs text-gray-400">待处理</div>
        </div>
      </div>
    </div>
  </aside>
</template>
