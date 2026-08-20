<template>
  <div class="app-layout" :class="{ dark: settingsStore.isDark }">
    <!-- 顶部导航 -->
    <AppHeader />
    
    <!-- 主体内容 -->
    <div class="app-body">
      <!-- 侧边栏 -->
      <AppSidebar />
      
      <!-- 主内容区 -->
      <main class="app-main">
        <div class="page-container">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>
<script setup>
import { onMounted } from 'vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()

onMounted(() => {
  settingsStore.init()
})
</script>
<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-color);
  color: var(--text-primary);
  transition: background 0.3s, color 0.3s;
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-main {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--bg-color);
  transition: background 0.3s;
}

.page-container {
  max-width: 1600px;
  margin: 0 auto;
  height: 100%;
}

/* 暗色主题 */
.dark .app-main {
  background: var(--bg-color);
}

/* 响应式 */
@media (max-width: 768px) {
  .app-main {
    padding: 12px;
  }
}
</style>
