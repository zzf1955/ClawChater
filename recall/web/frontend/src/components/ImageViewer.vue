<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { getScreenshotUrl } from '../api'

const props = defineProps({
  screenshots: Array,
  index: Number
})

const emit = defineEmits(['close', 'update:index'])

const currentItem = computed(() => props.screenshots[props.index])
const containerRef = ref(null)
const imageLoaded = ref(false)

function prev() {
  if (props.index > 0) {
    imageLoaded.value = false
    emit('update:index', props.index - 1)
  }
}

function next() {
  if (props.index < props.screenshots.length - 1) {
    imageLoaded.value = false
    emit('update:index', props.index + 1)
  }
}

function onKeydown(e) {
  if (e.key === 'Escape') emit('close')
  if (e.key === 'ArrowLeft') prev()
  if (e.key === 'ArrowRight') next()
}

function onImageLoad() {
  imageLoaded.value = true
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  document.body.style.overflow = 'hidden'
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})

watch(() => props.index, () => {
  imageLoaded.value = false
})
</script>

<template>
  <Teleport to="body">
    <div
      ref="containerRef"
      class="fixed inset-0 z-50 flex items-center justify-center"
      @click.self="emit('close')"
    >
      <!-- 背景遮罩 -->
      <div class="absolute inset-0 bg-black/95 backdrop-blur-xl"></div>
      
      <!-- 关闭按钮 -->
      <button
        @click="emit('close')"
        class="absolute top-6 right-6 z-20 w-12 h-12 flex items-center justify-center text-white/60 hover:text-white bg-white/10 hover:bg-white/20 rounded-full transition-all duration-200 group"
      >
        <svg class="w-6 h-6 transition-transform group-hover:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- 上一张按钮 -->
      <button
        @click="prev"
        :disabled="index <= 0"
        class="absolute left-6 top-1/2 -translate-y-1/2 z-20 w-14 h-14 flex items-center justify-center text-white/60 hover:text-white bg-white/10 hover:bg-white/20 rounded-full transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-white/10 group"
      >
        <svg class="w-7 h-7 transition-transform group-hover:-translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <!-- 图片容器 -->
      <div class="relative z-10 max-w-[92vw] max-h-[88vh] flex flex-col items-center">
        <!-- 加载动画 -->
        <div 
          v-if="!imageLoaded"
          class="absolute inset-0 flex items-center justify-center"
        >
          <div class="w-12 h-12 border-4 border-white/20 border-t-white rounded-full animate-spin"></div>
        </div>
        
        <!-- 图片 -->
        <Transition
          enter-active-class="transition-all duration-300 ease-out"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition-all duration-200 ease-in"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <img
            v-show="imageLoaded"
            :key="currentItem?.id"
            :src="currentItem ? getScreenshotUrl(currentItem.path) : ''"
            @load="onImageLoad"
            class="max-w-full max-h-[75vh] object-contain rounded-lg shadow-2xl"
          />
        </Transition>
        
        <!-- 信息面板 -->
        <Transition
          enter-active-class="transition-all duration-300 delay-100 ease-out"
          enter-from-class="opacity-0 translate-y-4"
          enter-to-class="opacity-100 translate-y-0"
        >
          <div v-if="currentItem && imageLoaded" class="mt-6 text-center">
            <div class="inline-flex items-center gap-3 px-5 py-3 bg-white/10 backdrop-blur rounded-xl">
              <div class="w-2 h-2 rounded-full bg-white/60"></div>
              <span class="text-white font-medium">{{ currentItem.timestamp }}</span>
              <span class="text-white/40">|</span>
              <span class="text-white/70 max-w-md truncate">
                {{ currentItem.window_title || currentItem.process_name || '未知窗口' }}
              </span>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 下一张按钮 -->
      <button
        @click="next"
        :disabled="index >= screenshots.length - 1"
        class="absolute right-6 top-1/2 -translate-y-1/2 z-20 w-14 h-14 flex items-center justify-center text-white/60 hover:text-white bg-white/10 hover:bg-white/20 rounded-full transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-white/10 group"
      >
        <svg class="w-7 h-7 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>

      <!-- 底部信息栏 -->
      <div class="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex items-center gap-4">
        <!-- 计数器 -->
        <div class="flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur rounded-full">
          <span class="text-white/60 text-sm">
            <span class="text-white font-semibold">{{ index + 1 }}</span>
            <span class="mx-1">/</span>
            <span>{{ screenshots.length }}</span>
          </span>
        </div>
        
        <!-- 快捷键提示 -->
        <div class="hidden md:flex items-center gap-3 text-white/40 text-xs">
          <span class="flex items-center gap-1">
            <kbd class="px-2 py-1 bg-white/10 rounded">←</kbd>
            <kbd class="px-2 py-1 bg-white/10 rounded">→</kbd>
            切换
          </span>
          <span class="flex items-center gap-1">
            <kbd class="px-2 py-1 bg-white/10 rounded">ESC</kbd>
            关闭
          </span>
        </div>
      </div>
      
      <!-- 缩略图导航 -->
      <div class="absolute bottom-20 left-1/2 -translate-x-1/2 z-20 max-w-[80vw] overflow-hidden">
        <div class="flex items-center gap-2 px-4 py-2 bg-white/5 backdrop-blur rounded-xl">
          <div 
            v-for="(item, i) in screenshots.slice(Math.max(0, index - 4), Math.min(screenshots.length, index + 5))"
            :key="item.id"
            @click="emit('update:index', Math.max(0, index - 4) + i)"
            :class="[
              'w-12 h-8 rounded cursor-pointer transition-all duration-200 overflow-hidden',
              Math.max(0, index - 4) + i === index 
                ? 'ring-2 ring-white scale-110'
                : 'opacity-50 hover:opacity-80'
            ]"
          >
            <img
              :src="getScreenshotUrl(item.path)"
              class="w-full h-full object-cover"
              loading="lazy"
            />
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
