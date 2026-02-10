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

function clearSearch() {
  searchQuery.value = ''
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
    return dt.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return timestamp.slice(11, 16)
  }
}

function getDateLabel(timestamp) {
  if (!timestamp) return ''
  const dt = new Date(timestamp)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 86400000)
  const target = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate())

  if (target.getTime() === today.getTime()) return '今天'
  if (target.getTime() === yesterday.getTime()) return '昨天'
  return dt.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

const groupedScreenshots = computed(() => {
  const groups = []
  let currentLabel = null
  for (const item of screenshots.value) {
    const label = getDateLabel(item.timestamp)
    if (label !== currentLabel) {
      groups.push({ label, items: [] })
      currentLabel = label
    }
    groups[groups.length - 1].items.push(item)
  }
  return groups
})

function getGlobalIndex(groupIdx, itemIdx) {
  let idx = 0
  for (let g = 0; g < groupIdx; g++) {
    idx += groupedScreenshots.value[g].items.length
  }
  return idx + itemIdx
}

onMounted(loadData)
</script>

<template>
  <div class="h-full flex flex-col bg-white">
    <!-- 工具栏 -->
    <div class="border-b border-gray-200 px-6 py-3 flex items-center gap-3">
      <div class="flex-1 max-w-md relative">
        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <input
          v-model="searchQuery"
          @keyup.enter="onSearch"
          type="text"
          placeholder="搜索内容或窗口标题..."
          class="w-full pl-9 pr-9 py-2 bg-gray-100 rounded-lg text-sm text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-300 focus:bg-white border border-transparent focus:border-gray-300"
        />
        <button
          v-if="searchQuery"
          @click="clearSearch"
          class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <button
        @click="onSearch"
        class="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors"
      >
        搜索
      </button>

      <button
        @click="loadData"
        :disabled="loading"
        class="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
        title="刷新"
      >
        <svg :class="['w-4 h-4', loading && 'animate-spin']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>

    <!-- 时间线内容 -->
    <div class="flex-1 overflow-auto">
      <div v-if="loading" class="flex items-center justify-center h-full">
        <div class="w-8 h-8 border-2 border-gray-200 border-t-gray-600 rounded-full animate-spin"></div>
      </div>

      <div
        v-else-if="screenshots.length === 0"
        class="flex flex-col items-center justify-center h-full text-gray-400"
      >
        <svg class="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <p class="text-sm">暂无截图</p>
      </div>

      <div v-else class="max-w-4xl mx-auto px-6 py-4">
        <div
          v-for="(group, groupIdx) in groupedScreenshots"
          :key="group.label"
          class="mb-6"
        >
          <div class="flex items-center gap-3 mb-3">
            <span class="text-xs font-medium text-gray-400 uppercase tracking-wide whitespace-nowrap">{{ group.label }}</span>
            <div class="flex-1 h-px bg-gray-100"></div>
          </div>

          <div class="space-y-1">
            <div
              v-for="(item, itemIdx) in group.items"
              :key="item.id"
              @click="selectItem(item, getGlobalIndex(groupIdx, itemIdx))"
              @dblclick="openViewer(item, getGlobalIndex(groupIdx, itemIdx))"
              :class="[
                'flex items-center gap-4 px-3 py-2.5 rounded-lg cursor-pointer transition-colors duration-100',
                selectedItem?.id === item.id
                  ? 'bg-gray-100'
                  : 'hover:bg-gray-50'
              ]"
            >
              <span class="text-xs text-gray-400 font-mono w-12 flex-shrink-0">
                {{ formatTime(item.timestamp) }}
              </span>

              <div class="w-28 h-16 flex-shrink-0 rounded overflow-hidden bg-gray-100">
                <img
                  :src="getScreenshotUrl(item.path)"
                  :alt="item.window_title"
                  class="w-full h-full object-cover"
                  loading="lazy"
                />
              </div>

              <div class="flex-1 min-w-0">
                <div class="text-sm text-gray-700 truncate">
                  {{ item.window_title || item.process_name || '未知窗口' }}
                </div>
                <div v-if="item.ocr_text" class="text-xs text-gray-400 truncate mt-0.5">
                  {{ item.ocr_text }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情面板 -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="translate-y-full opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition-all duration-150 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-full opacity-0"
    >
      <div v-if="selectedItem" class="border-t border-gray-200 px-6 py-3">
        <div class="max-w-4xl mx-auto flex items-center gap-4">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 text-sm">
              <span class="text-gray-700 font-medium">
                {{ selectedItem.window_title || selectedItem.process_name || '-' }}
              </span>
              <span class="text-gray-300">·</span>
              <span class="text-gray-400 text-xs">
                {{ selectedItem.timestamp }}
              </span>
            </div>
            <div v-if="selectedItem.ocr_text" class="text-xs text-gray-400 truncate mt-1">
              {{ selectedItem.ocr_text }}
            </div>
          </div>
          <button
            @click="openViewer(selectedItem, viewerIndex)"
            class="flex-shrink-0 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            查看大图
          </button>
        </div>
      </div>
    </Transition>

    <!-- 分页 -->
    <div class="border-t border-gray-200 px-6 py-2.5">
      <div class="flex items-center justify-between max-w-4xl mx-auto">
        <button
          @click="prevPage"
          :disabled="currentPage <= 1"
          class="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 rounded-lg disabled:opacity-30 hover:bg-gray-100 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          上一页
        </button>

        <span class="text-sm text-gray-400">
          第 <span class="text-gray-700 font-medium">{{ currentPage }}</span> 页
        </span>

        <button
          @click="nextPage"
          :disabled="screenshots.length < 50"
          class="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 rounded-lg disabled:opacity-30 hover:bg-gray-100 transition-colors"
        >
          下一页
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
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
