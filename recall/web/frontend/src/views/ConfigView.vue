<script setup>
import { ref, onMounted } from 'vue'
import { getConfig, setConfig } from '../api'

const config = ref({
  CHANGE_THRESHOLD: 0.8,
  FORCE_CAPTURE_INTERVAL: 300,
  MIN_CAPTURE_INTERVAL: 10,
  JPEG_QUALITY: 85,
  GPU_USAGE_THRESHOLD: 30,
  OCR_BATCH_SIZE: 10,
})

const saving = ref(false)
const message = ref('')

async function loadConfig() {
  const data = await getConfig()
  if (data && Object.keys(data).length > 0) {
    config.value = { ...config.value, ...data }
  }
}

async function saveConfig() {
  saving.value = true
  message.value = ''
  const result = await setConfig(config.value)
  saving.value = false
  if (result.success) {
    message.value = '配置已保存'
    setTimeout(() => message.value = '', 3000)
  } else {
    message.value = '保存失败: ' + (result.message || '未知错误')
  }
}

function resetConfig() {
  config.value = {
    CHANGE_THRESHOLD: 0.8,
    FORCE_CAPTURE_INTERVAL: 300,
    MIN_CAPTURE_INTERVAL: 10,
    JPEG_QUALITY: 85,
    GPU_USAGE_THRESHOLD: 30,
    OCR_BATCH_SIZE: 10,
  }
}

onMounted(loadConfig)
</script>

<template>
  <div class="h-full overflow-auto">
    <div class="max-w-2xl mx-auto p-6">
      <h2 class="text-xl font-semibold text-gray-800 mb-6">配置</h2>

      <!-- 截图设置 -->
      <div class="bg-white rounded-lg border border-gray-200 p-5 mb-6">
        <h3 class="text-base font-medium text-gray-700 mb-4">截图设置</h3>

        <div class="space-y-5">
          <!-- 变化阈值 -->
          <div>
            <label class="block text-sm text-gray-600 mb-2">
              变化阈值 (0-1): <span class="font-medium">{{ config.CHANGE_THRESHOLD.toFixed(2) }}</span>
            </label>
            <input
              type="range"
              v-model.number="config.CHANGE_THRESHOLD"
              min="0"
              max="1"
              step="0.01"
              class="w-64 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
            />
          </div>

          <!-- 强制截图间隔 -->
          <div>
            <label class="block text-sm text-gray-600 mb-2">强制截图间隔 (秒)</label>
            <input
              type="number"
              v-model.number="config.FORCE_CAPTURE_INTERVAL"
              min="60"
              max="3600"
              class="w-32 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <!-- 最小截图间隔 -->
          <div>
            <label class="block text-sm text-gray-600 mb-2">最小截图间隔 (秒)</label>
            <input
              type="number"
              v-model.number="config.MIN_CAPTURE_INTERVAL"
              min="1"
              max="300"
              class="w-32 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <!-- JPEG质量 -->
          <div>
            <label class="block text-sm text-gray-600 mb-2">
              JPEG质量 (1-100): <span class="font-medium">{{ config.JPEG_QUALITY }}</span>
            </label>
            <input
              type="range"
              v-model.number="config.JPEG_QUALITY"
              min="1"
              max="100"
              class="w-64 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
            />
          </div>
        </div>
      </div>

      <!-- OCR设置 -->
      <div class="bg-white rounded-lg border border-gray-200 p-5 mb-6">
        <h3 class="text-base font-medium text-gray-700 mb-4">OCR设置</h3>

        <div class="space-y-5">
          <!-- GPU使用率阈值 -->
          <div>
            <label class="block text-sm text-gray-600 mb-2">
              GPU使用率阈值: <span class="font-medium">{{ config.GPU_USAGE_THRESHOLD }}%</span>
            </label>
            <input
              type="range"
              v-model.number="config.GPU_USAGE_THRESHOLD"
              min="0"
              max="100"
              class="w-64 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
            />
          </div>

          <!-- 批量OCR数量 -->
          <div>
            <label class="block text-sm text-gray-600 mb-2">批量OCR数量</label>
            <input
              type="number"
              v-model.number="config.OCR_BATCH_SIZE"
              min="1"
              max="100"
              class="w-32 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>

      <!-- 按钮 -->
      <div class="flex items-center gap-3">
        <button
          @click="resetConfig"
          class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
        >
          恢复默认
        </button>
        <button
          @click="saveConfig"
          :disabled="saving"
          class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50"
        >
          {{ saving ? '保存中...' : '保存并应用' }}
        </button>
        <span v-if="message" :class="message.includes('失败') ? 'text-red-500' : 'text-green-500'" class="text-sm">
          {{ message }}
        </span>
      </div>
    </div>
  </div>
</template>
