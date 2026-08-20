<template>
  <div class="image-compare" ref="containerRef">
    <!-- 原始图片 -->
    <div class="compare-image original">
      <el-image :src="originalImage" fit="contain" class="compare-img">
        <template #error>
          <div class="image-placeholder">
            <el-icon><Picture /></el-icon>
            <span>原图加载失败</span>
          </div>
        </template>
      </el-image>
      <div class="compare-label">原图</div>
    </div>
    <!-- 对比滑块 -->
    <div class="compare-divider" @mousedown="startDrag" @touchstart="startDrag">
      <div class="divider-line"></div>
      <div class="divider-handle">
        <el-icon><DArrowRight /></el-icon>
        <el-icon><DArrowLeft /></el-icon>
      </div>
    </div>
    <!-- 生成图片 -->
    <div class="compare-image generated">
      <el-image :src="generatedImage" fit="contain" class="compare-img">
        <template #error>
          <div class="image-placeholder">
            <el-icon><Picture /></el-icon>
            <span>生成图加载失败</span>
          </div>
        </template>
      </el-image>
      <div class="compare-label">生成图</div>
    </div>
    <!-- 滑动覆盖层 (实现对比效果) -->
    <div class="compare-overlay" :style="{ width: slidePosition + '%' }">
      <el-image :src="generatedImage" fit="contain" class="compare-img" />
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Picture, DArrowRight, DArrowLeft } from '@element-plus/icons-vue'

const props = defineProps({
  originalImage: {
    type: String,
    required: true
  },
  generatedImage: {
    type: String,
    required: true
  }
})

const containerRef = ref(null)
const slidePosition = ref(50)
const isDragging = ref(false)

// 开始拖拽
const startDrag = (event) => {
  isDragging.value = true
  event.preventDefault()
}

// 拖拽移动
const onDrag = (event) => {
  if (!isDragging.value || !containerRef.value) return

  const rect = containerRef.value.getBoundingClientRect()
  const clientX = event.clientX || event.touches?.[0]?.clientX || 0
  const x = (clientX - rect.left) / rect.width
  const position = Math.max(0, Math.min(100, x * 100))
  slidePosition.value = position
}

// 结束拖拽
const stopDrag = () => {
  isDragging.value = false
}

// 键盘控制
const onKeyDown = (event) => {
  if (event.key === 'ArrowLeft') {
    slidePosition.value = Math.max(0, slidePosition.value - 5)
  } else if (event.key === 'ArrowRight') {
    slidePosition.value = Math.min(100, slidePosition.value + 5)
  }
}

onMounted(() => {
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag, { passive: true })
  document.addEventListener('touchend', stopDrag)
  document.addEventListener('keydown', onKeyDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
  document.removeEventListener('keydown', onKeyDown)
})
</script>
<style scoped>
.image-compare {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 300px;
  overflow: hidden;
  border-radius: 8px;
  background: var(--bg-color);
  user-select: none;
}

.compare-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.compare-image .compare-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.compare-image .compare-img :deep(.el-image__inner) {
  object-fit: contain;
  width: 100%;
  height: 100%;
}

.compare-label {
  position: absolute;
  bottom: 16px;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(0, 0, 0, 0.6);
  color: white;
}

.original .compare-label {
  left: 16px;
}

.generated .compare-label {
  right: 16px;
}

/* 图片占位 */
.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--text-secondary);
  background: var(--bg-color);
}

.image-placeholder .el-icon {
  font-size: 40px;
  margin-bottom: 8px;
  color: var(--text-placeholder);
}

.image-placeholder span {
  font-size: 13px;
}

/* 对比滑块 */
.compare-divider {
  position: absolute;
  top: 0;
  left: 50%;
  width: 4px;
  height: 100%;
  transform: translateX(-50%);
  cursor: ew-resize;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
}

.divider-line {
  position: absolute;
  top: 0;
  left: 50%;
  width: 2px;
  height: 100%;
  background: white;
  transform: translateX(-50%);
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.3);
}

.divider-handle {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 6px 4px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
  z-index: 11;
  color: var(--text-regular);
}

.divider-handle .el-icon {
  font-size: 16px;
}

/* 覆盖层 (显示生成图的部分) */
.compare-overlay {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  overflow: hidden;
  border-right: 2px solid white;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
  z-index: 5;
}

.compare-overlay .compare-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.compare-overlay .compare-img :deep(.el-image__inner) {
  object-fit: contain;
  width: 100%;
  height: 100%;
}

/* 暗色主题 */
.dark .compare-divider .divider-line {
  background: rgba(255, 255, 255, 0.8);
}

.dark .divider-handle {
  background: #2d2d2d;
  color: var(--text-primary);
}

/* 响应式 */
@media (max-width: 768px) {
  .image-compare {
    min-height: 200px;
  }

  .compare-label {
    font-size: 10px;
    padding: 2px 10px;
    bottom: 8px;
  }

  .divider-handle {
    padding: 4px 2px;
  }

  .divider-handle .el-icon {
    font-size: 12px;
  }
}
</style>
