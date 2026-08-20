<template>
  <div class="preview-panel">
    <!-- 头部 -->
    <div class="preview-header">
      <span class="preview-title">生成的图片将在这里显示</span>
      <div class="preview-actions">
        <el-button
          v-if="hasImages"
          size="small"
          text
          @click="onDownloadAll"
        >
          <el-icon><Download /></el-icon> 下载全部
        </el-button>
        <el-button
          v-if="hasImages"
          size="small"
          text
          type="danger"
          @click="onClearAll"
        >
          <el-icon><Delete /></el-icon> 清空
        </el-button>
      </div>
    </div>

    <!-- 主预览区 -->
    <div class="preview-main">
      <!-- 空状态 -->
      <div v-if="!hasImages && !isGenerating" class="empty-state">
        <el-icon size="64"><Picture /></el-icon>
        <p>生成的图片将在这里显示</p>
        <span>左侧输入提示词，点击生成开始创作</span>
      </div>

      <!-- ✅ 生成中 - 显示加载动画 -->
      <div v-else-if="isGenerating" class="generating-state">
        <div class="loading-spinner">
          <el-icon class="is-loading" size="48"><Loading /></el-icon>
        </div>
        <p>正在生成图片...</p>
        <span>请稍候，这可能需要几秒钟</span>
        <div class="progress-bar">
          <el-progress
            :percentage="progress"
            :stroke-width="4"
            :show-text="false"
            style="width: 200px; margin-top: 16px"
          />
        </div>
      </div>

      <!-- 图片展示 -->
      <div v-else-if="hasImages" class="image-display" @click="onImageClick">
        <el-image
          :src="currentImageUrl"
          fit="contain"
          class="main-image"
          loading="lazy"
        >
          <template #error>
            <div class="image-error">
              <el-icon><Picture /></el-icon>
              <span>加载失败</span>
              <el-button size="small" @click="onRetry">重试</el-button>
            </div>
          </template>
        </el-image>
      </div>
    </div>

    <!-- 缩略图列表 -->
    <div v-if="hasImages" class="thumbnail-section">
      <div class="thumbnail-list">
        <div
          v-for="(img, index) in images"
          :key="index"
          class="thumbnail-item"
          :class="{ active: currentIndex === index }"
          @click="selectImage(index)"
        >
          <!-- ✅ 使用后端返回的 URL 或路径 -->
          <el-image 
            :src="getImageUrl(img)" 
            fit="cover" 
            loading="lazy"
          >
            <template #error>
              <div class="thumb-error">
                <el-icon><Picture /></el-icon>
              </div>
            </template>
          </el-image>
          <span class="thumbnail-index">{{ index + 1 }}</span>
          <el-icon class="thumbnail-delete" @click.stop="removeImage(index)">
            <Close />
          </el-icon>
        </div>
      </div>

      <!-- 图片信息 -->
      <div class="image-info">
        <span>共 {{ images.length }} 张图片</span>
        <span class="divider">|</span>
        <span>尺寸: {{ imageSize || '1K' }}</span>
        <span class="divider">|</span>
        <span>宽高比: {{ aspectRatio || '1:1' }}</span>
        <span class="divider">|</span>
        <span>模型: {{ modelName || '未知' }}</span>
      </div>
    </div>

    <!-- 图片预览弹窗 -->
    <el-image-viewer
      v-if="showViewer"
      :url-list="imageUrls"
      :initial-index="currentIndex"
      @close="showViewer = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Picture, Loading, Download, Delete, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  images: {
    type: Array,
    default: () => []
  },
  isGenerating: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  },
  imageSize: {
    type: String,
    default: '1K'
  },
  aspectRatio: {
    type: String,
    default: '1:1'
  },
  modelName: {
    type: String,
    default: ''
  },
  currentImage: {
    type: Object,
    default: null
  }
})

const emit = defineEmits([
  'select-image',
  'remove-image',
  'clear-all',
  'download-all',
  'download-image',
  'retry'
])

const previewRef = ref(null)
const showViewer = ref(false)
const currentIndex = ref(0)

// ✅ 获取图片 URL（支持多种格式）
const getImageUrl = (img) => {
  if (!img) return ''
  // 优先使用 url，然后 path
  if (img.url) return img.url
  if (img.path) {
    // 如果是相对路径，加上 /output 前缀
    if (img.path.startsWith('data/output/') || img.path.includes('output')) {
      return '/' + img.path.replace(/\\/g, '/')
    }
    return img.path
  }
  return ''
}

const hasImages = computed(() => props.images && props.images.length > 0)

const currentImageUrl = computed(() => {
  if (props.currentImage) {
    return getImageUrl(props.currentImage)
  }
  if (hasImages.value) {
    return getImageUrl(props.images[0])
  }
  return ''
})

const imageUrls = computed(() => {
  return props.images.map(img => getImageUrl(img)).filter(Boolean)
})

// 方法
const selectImage = (index) => {
  currentIndex.value = index
  emit('select-image', index)
}

const removeImage = (index) => {
  emit('remove-image', index)
  if (currentIndex.value >= props.images.length - 1) {
    currentIndex.value = Math.max(0, props.images.length - 2)
  }
}

const onImageClick = () => {
  if (hasImages.value) {
    showViewer.value = true
  }
}

const onDownloadAll = () => {
  if (hasImages.value) {
    emit('download-all', props.images)
  }
}

const onClearAll = () => {
  emit('clear-all')
}

const onRetry = () => {
  emit('retry')
}

// 更新当前索引
watch(() => props.images, (newVal) => {
  if (newVal && newVal.length > 0 && currentIndex.value >= newVal.length) {
    currentIndex.value = 0
  }
}, { immediate: true })

defineExpose({
  resetViewer: () => { showViewer.value = false }
})
</script>

<style scoped>
.preview-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-color);
  border-radius: 12px;
  overflow: hidden;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.preview-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-regular);
}

.preview-actions {
  display: flex;
  gap: 4px;
}

.preview-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: var(--bg-color);
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.image-display {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-image {
  width: 100%;
  height: 100%;
  max-height: 100%;
  object-fit: contain;
}

.main-image :deep(.el-image__inner) {
  max-height: 100%;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  padding: 40px;
}

.empty-state .el-icon {
  color: var(--text-placeholder);
  margin-bottom: 16px;
}

.empty-state p {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-regular);
  margin: 0 0 8px 0;
}

.empty-state span {
  font-size: 13px;
  color: var(--text-secondary);
}

/* ✅ 生成中 - 加载动画 */
.generating-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  padding: 40px;
}

.loading-spinner {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.loading-spinner .el-icon {
  color: var(--primary-color);
  font-size: 48px;
}

.generating-state p {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-regular);
  margin: 0 0 4px 0;
}

.generating-state span {
  font-size: 13px;
  color: var(--text-secondary);
}

.progress-bar {
  width: 200px;
}

/* 缩略图 */
.thumbnail-section {
  flex-shrink: 0;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
  padding: 12px 16px;
}

.thumbnail-list {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.thumbnail-item {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  flex-shrink: 0;
  transition: all 0.2s;
}

.thumbnail-item:hover {
  border-color: var(--primary-color);
  transform: scale(1.05);
}

.thumbnail-item.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.3);
}

.thumbnail-item .el-image {
  width: 100%;
  height: 100%;
}

.thumbnail-item .el-image :deep(.el-image__inner) {
  object-fit: cover;
}

.thumb-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: var(--bg-color);
  color: var(--text-placeholder);
}

.thumb-error .el-icon {
  font-size: 24px;
}

.thumbnail-index {
  position: absolute;
  bottom: 2px;
  left: 2px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 10px;
  padding: 0 6px;
  border-radius: 8px;
  line-height: 18px;
}

.thumbnail-delete {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 16px;
  height: 16px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 50%;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
}

.thumbnail-item:hover .thumbnail-delete {
  opacity: 1;
}

.thumbnail-delete:hover {
  background: var(--danger-color);
}

.image-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
  flex-wrap: wrap;
}

.divider {
  color: var(--border-color);
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
  padding: 40px;
}

.image-error .el-icon {
  font-size: 48px;
  color: var(--text-placeholder);
}

/* 暗色主题 */
.dark .preview-main {
  background: var(--bg-card);
}

.dark .thumbnail-section {
  background: var(--bg-card);
}

.dark .thumb-error {
  background: var(--bg-card);
}

/* 响应式 */
@media (max-width: 768px) {
  .preview-main {
    min-height: 200px;
  }

  .thumbnail-item {
    width: 56px;
    height: 56px;
  }

  .thumbnail-list {
    gap: 6px;
  }

  .image-info {
    font-size: 11px;
  }
}
</style>