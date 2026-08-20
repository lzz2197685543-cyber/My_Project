<template>
  <header class="app-header">
    <div class="header-left">
      <div class="logo" @click="router.push('/')">
        <span class="logo-icon">🎨</span>
        <span class="logo-text">AI Studio</span>
      </div>
    </div>
    <div class="header-center">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>{{ currentRoute.meta?.title || '页面' }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="header-right">
      <!-- 模型状态 -->
      <el-tag size="small" type="info" class="model-tag">
        <el-icon><Cpu /></el-icon>
        {{ settingsStore.defaultProvider === 'yi' ? 'API易' : '百炼' }}
      </el-tag>
      <!-- 主题切换 -->
      <el-button 
        :icon="settingsStore.isDark ? Sunny : Moon" 
        circle 
        size="small"
        @click="settingsStore.toggleTheme()"
        class="theme-btn"
      />

      <!-- 设置入口 -->
      <el-button 
        icon="Setting" 
        circle 
        size="small"
        @click="router.push('/settings')"
        class="settings-btn"
      />
    </div>
  </header>
</template>
<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Sunny, Moon, Cpu } from '@element-plus/icons-vue'
import { useSettingsStore } from '@/stores/settings'

const router = useRouter()
const route = useRoute()
const settingsStore = useSettingsStore()

const currentRoute = computed(() => route)
</script>
<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  transition: background 0.3s, border-color 0.3s;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  transition: color 0.3s;
}

.header-center {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 24px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  font-size: 12px;
}

.theme-btn,
.settings-btn {
  color: var(--text-secondary);
  transition: color 0.3s;
}

.theme-btn:hover,
.settings-btn:hover {
  color: var(--primary-color);
}

/* 暗色主题 */
.dark .logo-text {
  color: var(--text-primary);
}

/* 响应式 */
@media (max-width: 768px) {
  .app-header {
    padding: 0 12px;
  }

  .header-center {
    display: none;
  }

  .logo-text {
    font-size: 16px;
  }

  .model-tag {
    display: none;
  }
}
</style>
