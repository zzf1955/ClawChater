<script setup>
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import BrowserView from './views/BrowserView.vue'
import ConfigView from './views/ConfigView.vue'

const currentView = ref('browser')
</script>

<template>
  <div class="flex h-screen bg-white">
    <!-- 侧边栏 -->
    <Sidebar v-model:current="currentView" />

    <!-- 主内容区 -->
    <main class="flex-1 overflow-hidden">
      <BrowserView v-if="currentView === 'browser'" />
      <ConfigView v-else-if="currentView === 'config'" />
    </main>
  </div>
</template>
