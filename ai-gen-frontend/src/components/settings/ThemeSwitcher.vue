<template>
  <div class="theme-switcher">
    <span class="theme-label">主题</span>
    <div class="theme-options">
      <div
        class="theme-option"
        :class="{ active: theme === 'light' }"
        @click="setTheme('light')"
      >
        <div class="theme-preview light-preview">
          <div class="preview-header"></div>
          <div class="preview-body">
            <div class="preview-line"></div>
            <div class="preview-line short"></div>
          </div>
        </div>
        <span>☀️ 亮色</span>
      </div>
      <div
        class="theme-option"
        :class="{ active: theme === 'dark' }"
        @click="setTheme('dark')"
      >
        <div class="theme-preview dark-preview">
          <div class="preview-header"></div>
          <div class="preview-body">
            <div class="preview-line"></div>
            <div class="preview-line short"></div>
          </div>
        </div>
        <span>🌙 暗色</span>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

const settingsStore = useSettingsStore()
const theme = computed(() => settingsStore.theme)

const setTheme = (value) => {
  settingsStore.setTheme(value)
}
</script>
<style scoped>
.theme-switcher {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 0;
}

.theme-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-regular);
}

.theme-options {
  display: flex;
  gap: 16px;
}

.theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  border: 2px solid transparent;
  transition: all 0.3s;
  background: var(--bg-color);
}

.theme-option:hover {
  border-color: var(--border-color);
  transform: translateY(-2px);
}

.theme-option.active {
  border-color: var(--primary-color);
  background: rgba(64, 158, 255, 0.06);
}

.theme-option span {
  font-size: 13px;
  color: var(--text-regular);
  user-select: none;
}

/* 主题预览 */
.theme-preview {
  width: 80px;
  height: 56px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.preview-header {
  height: 12px;
  padding: 0 8px;
}

.preview-body {
  padding: 4px 8px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.preview-line {
  height: 4px;
  border-radius: 2px;
}

.preview-line.short {
  width: 60%;
}

/* 亮色预览 */
.light-preview {
  background: #f5f7fa;
}

.light-preview .preview-header {
  background: #ffffff;
  border-bottom: 1px solid #e4e7ed;
}

.light-preview .preview-line {
  background: #d0d0d0;
}

.light-preview .preview-line.short {
  background: #c0c0c0;
}

/* 暗色预览 */
.dark-preview {
  background: #1d1d1d;
}

.dark-preview .preview-header {
  background: #2d2d2d;
  border-bottom: 1px solid #3a3a3a;
}

.dark-preview .preview-line {
  background: #4a4a4a;
}

.dark-preview .preview-line.short {
  background: #3a3a3a;
}

/* 暗色主题 */
.dark .theme-option {
  background: var(--bg-card);
}

.dark .theme-option.active {
  background: rgba(64, 158, 255, 0.15);
}

/* 响应式 */
@media (max-width: 768px) {
  .theme-switcher {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .theme-options {
    width: 100%;
    justify-content: center;
  }

  .theme-preview {
    width: 64px;
    height: 44px;
  }
}
</style>
