<script setup>
import { ref, onMounted, computed } from 'vue'
import { getScreenshots, getScreenshotUrl } from '../api'
import ImageViewer from '../components/ImageViewer.vue'

const screenshots = ref([])
const currentPage = ref(1)
const searchQuery = ref('')
const loading = ref(false)
const selectedItem = ref(null)
const viewerVisible = ref(false)
const viewerIndex = ref(0)

async function loadData() {
  loading.value = true
  screenshots.value = await getScreenshots(currentPage.value, 50, searchQuery.value)
  loading.value = false
}

function onSearch() {
  currentPage.value = 1
  loadData()
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    loadData()
  }
}

function nextPage() {
  currentPage.value++
  loadData()
}

function selectItem(item, index) {
  selectedItem.value = item
  viewerIndex.value = index
}

function openViewer(item, index) {
  viewerIndex.value = index
  viewerVisible.value = true
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  try {
    const dt = new Date(timestamp)
    return dt.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return timestamp.slice(11, 19)
  }
}

function formatDate(timestamp) {
  if (!timestamp) return ''
  try {
    const dt = new Date(timestamp)
    return dt.toLocaleDateString('zh-CN')
  } catch {
    return timestamp.slice(0, 10)
  }
}

onMounted(loadData)
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- 工具栏 -->
    <div class="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-4">
      <!-- 搜索框 -->
      <div class="flex gap-2">
        <input
          v-model="searchQuery"
          @keyup.enter="onSearch"
          type="text"
          placeholder="搜索OCR文本或窗口标题..."
          class="w-72 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        <button
          @click="onSearch"
          class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          搜索
        </button>
      </div>

      <div class="flex-1"></div>

      <!-- 快捷按钮 -->
      <button
        @click="loadData"
        class="px-3 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm hover:bg-gray-200 transition-colors"
      >
        刷新
      </button>
    </div>

    <!-- 缩略图网格 -->
    <div class="flex-1 overflow-auto p-4">
      <div v-if="loading" class="flex items-center justify-center h-full">
        <div class="text-gray-400">加载中...</div>
      </div>
      <div
        v-else-if="screenshots.length === 0"
        class="flex items-center justify-center h-full"
      >
        <div class="text-gray-400">暂无截图</div>
      </div>
      <div
        v-else
        class="grid gap-4"
        style="grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))"
      >
        <div
          v-for="(item, index) in screenshots"
          :key="item.id"
          @click="selectItem(item, index)"
          @dblclick="openViewer(item, index)"
          :class="[
            'bg-white rounded-lg border overflow-hidden cursor-pointer transition-all hover:shadow-md',
            selectedItem?.id === item.id ? 'ring-2 ring-primary-500 border-primary-500' : 'border-gray-200'
          ]"
        >
          <!-- 缩略图 -->
          <div class="aspect-video bg-gray-100 overflow-hidden">
            <img
              :src="getScreenshotUrl(item.path)"
              :alt="item.window_title"
              class="w-full h-full object-cover"
              loading="lazy"
            />
          </div>
          <!-- 信息 -->
          <div class="p-2">
            <div class="text-sm font-medium text-gray-800">
              {{ formatTime(item.timestamp) }}
            </div>
            <div class="text-xs text-gray-500 truncate" :title="item.window_title">
              {{ item.window_title || item.process_name || '-' }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情面板 -->
    <div v-if="selectedItem" class="bg-white border-t border-gray-200 px-4 py-3">
      <div class="text-sm text-gray-600">
        <span class="font-medium">{{ formatDate(selectedItem.timestamp) }} {{ formatTime(selectedItem.timestamp) }}</span>
        <span class="mx-2">|</span>
        <span>{{ selectedItem.window_title || selectedItem.process_name || '-' }}</span>
      </div>
      <div class="text-sm text-gray-500 mt-1 line-clamp-2">
        OCR: {{ selectedItem.ocr_text || '(无OCR文本)' }}
      </div>
    </div>

    <!-- 分页 -->
    <div class="bg-white border-t border-gray-200 px-4 py-2 flex items-center justify-between">
      <button
        @click="prevPage"
        :disabled="currentPage <= 1"
        class="px-3 py-1.5 text-sm rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
      >
        上一页
      </button>
      <span class="text-sm text-gray-500">第 {{ currentPage }} 页</span>
      <button
        @click="nextPage"
        :disabled="screenshots.length < 50"
        class="px-3 py-1.5 text-sm rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
      >
        下一页
      </button>
    </div>

    <!-- 大图预览 -->
    <ImageViewer
      v-if="viewerVisible"
      :screenshots="screenshots"
      :index="viewerIndex"
      @close="viewerVisible = false"
      @update:index="viewerIndex = $event"
    />
  </div>
</template>
