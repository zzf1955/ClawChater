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
const messageType = ref('success')

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
    messageType.value = 'success'
    message.value = '配置已保存'
    setTimeout(() => message.value = '', 3000)
  } else {
    messageType.value = 'error'
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
  <div class="h-full overflow-auto bg-white">
    <div class="max-w-2xl mx-auto px-8 py-8">
      <!-- 页面标题 -->
      <div class="mb-8">
        <h2 class="text-xl font-semibold text-gray-900">系统配置</h2>
        <p class="text-sm text-gray-400 mt-1">调整截图和 OCR 的行为参数</p>
      </div>

      <!-- 截图设置 -->
      <div class="mb-8">
        <h3 class="text-sm font-medium text-gray-900 mb-4">截图设置</h3>
        <div class="border border-gray-200 rounded-lg divide-y divide-gray-100">
          <!-- 变化阈值 -->
          <div class="px-5 py-4">
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm text-gray-600">变化阈值</label>
              <span class="text-sm font-mono text-gray-900">{{ config.CHANGE_THRESHOLD.toFixed(2) }}</span>
            </div>
            <input
              type="range"
              v-model.number="config.CHANGE_THRESHOLD"
              min="0" max="1" step="0.01"
              class="w-full h-1.5 bg-gray-200 rounded-full appearance-none cursor-pointer"
            />
            <p class="text-xs text-gray-400 mt-1.5">屏幕变化超过此阈值时才会保存截图，值越小越敏感</p>
          </div>

          <!-- 强制截图间隔 -->
          <div class="px-5 py-4">
            <label class="text-sm text-gray-600 block mb-2">强制截图间隔</label>
            <div class="flex items-center gap-2">
              <input
                type="number"
                v-model.number="config.FORCE_CAPTURE_INTERVAL"
                min="60" max="3600"
                class="w-28 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-gray-300 focus:border-gray-300"
              />
              <span class="text-sm text-gray-400">秒</span>
            </div>
            <p class="text-xs text-gray-400 mt-1.5">无论屏幕是否变化，每隔此时间强制保存一张截图</p>
          </div>

          <!-- 最小截图间隔 -->
          <div class="px-5 py-4">
            <label class="text-sm text-gray-600 block mb-2">最小截图间隔</label>
            <div class="flex items-center gap-2">
              <input
                type="number"
                v-model.number="config.MIN_CAPTURE_INTERVAL"
                min="1" max="300"
                class="w-28 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-gray-300 focus:border-gray-300"
              />
              <span class="text-sm text-gray-400">秒</span>
            </div>
            <p class="text-xs text-gray-400 mt-1.5">两次截图之间的最小间隔时间</p>
          </div>

          <!-- JPEG质量 -->
          <div class="px-5 py-4">
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm text-gray-600">JPEG 质量</label>
              <span class="text-sm font-mono text-gray-900">{{ config.JPEG_QUALITY }}%</span>
            </div>
            <input
              type="range"
              v-model.number="config.JPEG_QUALITY"
              min="1" max="100"
              class="w-full h-1.5 bg-gray-200 rounded-full appearance-none cursor-pointer"
            />
            <p class="text-xs text-gray-400 mt-1.5">截图的压缩质量，值越高画质越好但文件越大</p>
          </div>
        </div>
      </div>

      <!-- OCR设置 -->
      <div class="mb-8">
        <h3 class="text-sm font-medium text-gray-900 mb-4">OCR 设置</h3>
        <div class="border border-gray-200 rounded-lg divide-y divide-gray-100">
          <!-- GPU使用率阈值 -->
          <div class="px-5 py-4">
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm text-gray-600">GPU 使用率阈值</label>
              <span class="text-sm font-mono text-gray-900">{{ config.GPU_USAGE_THRESHOLD }}%</span>
            </div>
            <input
              type="range"
              v-model.number="config.GPU_USAGE_THRESHOLD"
              min="0" max="100"
              class="w-full h-1.5 bg-gray-200 rounded-full appearance-none cursor-pointer"
            />
            <p class="text-xs text-gray-400 mt-1.5">GPU 使用率超过此阈值时暂停 OCR 处理</p>
          </div>

          <!-- 批量OCR数量 -->
          <div class="px-5 py-4">
            <label class="text-sm text-gray-600 block mb-2">批量 OCR 数量</label>
            <div class="flex items-center gap-2">
              <input
                type="number"
                v-model.number="config.OCR_BATCH_SIZE"
                min="1" max="100"
                class="w-28 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-gray-300 focus:border-gray-300"
              />
              <span class="text-sm text-gray-400">张/批</span>
            </div>
            <p class="text-xs text-gray-400 mt-1.5">每批处理的截图数量，较大的值可以提高效率但会增加内存占用</p>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex items-center gap-3">
        <button
          @click="saveConfig"
          :disabled="saving"
          class="px-5 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors disabled:opacity-50"
        >
          {{ saving ? '保存中...' : '保存' }}
        </button>
        <button
          @click="resetConfig"
          class="px-5 py-2 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          恢复默认
        </button>

        <Transition
          enter-active-class="transition-opacity duration-200"
          enter-from-class="opacity-0"
          enter-to-class="opacity-100"
          leave-active-class="transition-opacity duration-150"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <span
            v-if="message"
            :class="[
              'text-sm',
              messageType === 'success' ? 'text-gray-500' : 'text-red-500'
            ]"
          >
            {{ message }}
          </span>
        </Transition>
      </div>
    </div>
  </div>
</template>
