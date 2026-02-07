<script setup>
import { computed } from 'vue'
import { getScreenshotUrl } from '../api'

const props = defineProps({
  screenshots: Array,
  index: Number
})

const emit = defineEmits(['close', 'update:index'])

const currentItem = computed(() => props.screenshots[props.index])

function prev() {
  if (props.index > 0) {
    emit('update:index', props.index - 1)
  }
}

function next() {
  if (props.index < props.screenshots.length - 1) {
    emit('update:index', props.index + 1)
  }
}

function onKeydown(e) {
  if (e.key === 'Escape') emit('close')
  if (e.key === 'ArrowLeft') prev()
  if (e.key === 'ArrowRight') next()
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
      @click.self="emit('close')"
      @keydown="onKeydown"
      tabindex="0"
      ref="container"
    >
      <!-- 关闭按钮 -->
      <button
        @click="emit('close')"
        class="absolute top-4 right-4 text-white/70 hover:text-white text-3xl"
      >
        ×
      </button>

      <!-- 上一张 -->
      <button
        @click="prev"
        :disabled="index <= 0"
        class="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 flex items-center justify-center text-white/70 hover:text-white text-3xl disabled:opacity-30"
      >
        ‹
      </button>

      <!-- 图片 -->
      <div class="max-w-[90vw] max-h-[85vh] flex flex-col items-center">
        <img
          v-if="currentItem"
          :src="getScreenshotUrl(currentItem.path)"
          class="max-w-full max-h-[75vh] object-contain"
        />
        <!-- 信息 -->
        <div v-if="currentItem" class="mt-4 text-center text-white/80 text-sm">
          <div>{{ currentItem.timestamp }}</div>
          <div class="text-white/60">{{ currentItem.window_title || currentItem.process_name }}</div>
        </div>
      </div>

      <!-- 下一张 -->
      <button
        @click="next"
        :disabled="index >= screenshots.length - 1"
        class="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 flex items-center justify-center text-white/70 hover:text-white text-3xl disabled:opacity-30"
      >
        ›
      </button>

      <!-- 计数 -->
      <div class="absolute bottom-4 left-1/2 -translate-x-1/2 text-white/60 text-sm">
        {{ index + 1 }} / {{ screenshots.length }}
      </div>
    </div>
  </Teleport>
</template>
