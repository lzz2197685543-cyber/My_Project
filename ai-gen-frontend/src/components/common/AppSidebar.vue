<template>
  <aside class="app-sidebar" :class="{ collapsed: isCollapsed }">
    <nav class="sidebar-nav">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: route.path === item.path || route.path.startsWith(item.path + '/') }"
        @click="isMobile && toggleCollapse()"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>
    <!-- 折叠按钮 -->
    <div class="sidebar-footer" @click="toggleCollapse">
      <el-icon><DArrowLeft v-if="!isCollapsed" /><DArrowRight v-else /></el-icon>
      <span v-if="!isCollapsed" class="collapse-label">收起</span>
    </div>
  </aside>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { DArrowLeft, DArrowRight } from '@element-plus/icons-vue'

const route = useRoute()
const isCollapsed = ref(false)
const isMobile = ref(false)

const menuItems = [
  { path: '/chat', label: '聊天', icon: '💬' },
  { path: '/image-gen', label: '文生图', icon: '🖼️' },
  { path: '/image-edit', label: '图生图', icon: '🎨' },
  { path: '/fuse', label: '多图融合', icon: '🔀' },
  { path: '/settings', label: '设置', icon: '⚙️' }
]

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 检测移动端
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  if (isMobile.value) {
    isCollapsed.value = true
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>
<style scoped>
.app-sidebar {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 220px;
  min-height: 100%;
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  overflow: hidden;
  padding: 16px 0;
}

.app-sidebar.collapsed {
  width: 64px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-radius: 8px;
  color: var(--text-regular);
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
  white-space: nowrap;
  position: relative;
}

.nav-item:hover {
  background: rgba(64, 158, 255, 0.08);
  color: var(--primary-color);
}

.nav-item.active {
  background: rgba(64, 158, 255, 0.12);
  color: var(--primary-color);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: var(--primary-color);
  border-radius: 0 4px 4px 0;
}

.nav-icon {
  font-size: 20px;
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

/* 折叠状态 */
.collapsed .nav-label {
  display: none;
}

.collapsed .nav-item {
  padding: 10px 12px;
  justify-content: center;
}

.collapsed .nav-icon {
  font-size: 22px;
}

/* 底部折叠按钮 */
.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  margin: 0 12px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s;
  user-select: none;
}

.sidebar-footer:hover {
  background: rgba(64, 158, 255, 0.08);
  color: var(--primary-color);
}

.collapse-label {
  font-size: 13px;
  font-weight: 500;
}

.collapsed .sidebar-footer {
  justify-content: center;
  padding: 12px;
}

.collapsed .collapse-label {
  display: none;
}

/* 暗色主题 */
.dark .nav-item:hover {
  background: rgba(64, 158, 255, 0.15);
}

.dark .nav-item.active {
  background: rgba(64, 158, 255, 0.2);
}

.dark .sidebar-footer:hover {
  background: rgba(64, 158, 255, 0.15);
}

/* 响应式 */
@media (max-width: 768px) {
  .app-sidebar {
    position: fixed;
    top: 60px;
    left: 0;
    bottom: 0;
    z-index: 90;
    box-shadow: 2px 0 12px rgba(0, 0, 0, 0.08);
  }

  .app-sidebar.collapsed {
    width: 0;
    border-right: none;
    padding: 0;
  }

  .app-sidebar.collapsed .sidebar-nav,
  .app-sidebar.collapsed .sidebar-footer {
    display: none;
  }

  .sidebar-footer {
    display: none;
  }
}
</style>
