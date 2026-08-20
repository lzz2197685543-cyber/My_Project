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

      <!-- 生成中 -->
      <div v-else-if="isGenerating" class="generating-state">
        <div class="loading-spinner">
          <el-icon class="is-loading" size="48"><Loading /></el-icon>
        </div>
        <p>正在生成图片...</p>
        <span>请稍候，这可能需要几秒钟</span>
      </div>

      <!-- 图片展示 - 使用 img 标签 -->
      <div v-else-if="hasImages" class="image-display" @click="onImageClick">
        <img
          :key="currentImageUrl"
          :src="currentImageUrl"
          class="main-image"
          alt="生成的图片"
          @error="handleImageError"
          @load="handleImageLoad"
          crossorigin="anonymous"
        />
        <div v-if="imageLoadError" class="image-error-overlay">
          <el-icon><Warning /></el-icon>
          <span>图片加载失败</span>
          <el-button size="small" @click="retryLoad">重试</el-button>
        </div>
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
          <img
            :src="getImageUrl(img)"
            class="thumbnail-img"
            :alt="`图片 ${index + 1}`"
            @error="handleThumbError"
          />
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
import { ref, computed, watch, nextTick } from 'vue'
import { Picture, Loading, Download, Delete, Close, Warning } from '@element-plus/icons-vue'

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
  'retry'
])

const showViewer = ref(false)
const currentIndex = ref(0)
const imageLoadError = ref(false)
const retryCount = ref(0)

// ✅ 获取图片 URL - 确保以 / 开头
const getImageUrl = (img) => {
  if (!img) {
    console.warn('⚠️ 图片对象为空')
    return ''
  }
  
  console.log('🔍 原始图片对象:', img)
  
  let url = img.url || img.path || ''
  
  if (!url) {
    console.warn('⚠️ 图片没有 url 或 path')
    return ''
  }
  
  // ✅ 确保以 / 开头
  if (!url.startsWith('http') && !url.startsWith('/')) {
    url = '/' + url
  }
  
  // ✅ 处理 Windows 路径
  if (url.includes(':\\')) {
    url = url.replace(/\\/g, '/')
    // 提取 output 部分
    if (url.includes('data/output/')) {
      const relative = url.split('data/output/').pop()
      url = '/output/' + relative
    } else if (url.includes('output/')) {
      const relative = url.split('output/').pop()
      url = '/output/' + relative
    }
  }
  
  console.log('✅ 最终图片URL:', url)
  return url
}
// 计算属性
const hasImages = computed(() => props.images && props.images.length > 0)

// ✅ 当前显示图片的 URL
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
  imageLoadError.value = false
  emit('select-image', index)
}

const removeImage = (index) => {
  emit('remove-image', index)
  if (currentIndex.value >= props.images.length - 1) {
    currentIndex.value = Math.max(0, props.images.length - 2)
  }
}

const onImageClick = () => {
  if (hasImages.value && !imageLoadError.value) {
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

// ✅ 图片加载成功
const handleImageLoad = (e) => {
  console.log('✅ 图片加载成功:', e.target.src)
  imageLoadError.value = false
}

// ✅ 图片加载失败
const handleImageError = (e) => {
  console.error('❌ 图片加载失败:', e.target.src)
  imageLoadError.value = true
  // 尝试添加时间戳重新加载
  const img = e.target
  if (!img.src.includes('?t=')) {
    setTimeout(() => {
      img.src = img.src + '?t=' + Date.now()
    }, 500)
  }
}

// ✅ 重试加载
const retryLoad = () => {
  retryCount.value++
  imageLoadError.value = false
  const img = document.querySelector('.main-image')
  if (img) {
    const baseUrl = currentImageUrl.value.split('?')[0]
    img.src = baseUrl + '?t=' + Date.now() + retryCount.value
  }
  emit('retry')
}


const handleThumbError = (e) => {
  // 缩略图加载失败，使用默认占位
  e.target.style.display = 'none'
}


// 监听图片变化
watch(() => props.images, (newVal) => {
  if (newVal && newVal.length > 0) {
    if (currentIndex.value >= newVal.length) {
      currentIndex.value = 0
    }
    imageLoadError.value = false
    // 延迟一下确保 DOM 更新
    nextTick(() => {
      const img = document.querySelector('.main-image')
      if (img) {
        img.src = currentImageUrl.value + '?t=' + Date.now()
      }
    })
  }
}, { immediate: true, deep: true })

// 监听当前图片变化
watch(() => props.currentImage, () => {
  imageLoadError.value = false
  nextTick(() => {
    const img = document.querySelector('.main-image')
    if (img) {
      img.src = currentImageUrl.value + '?t=' + Date.now()
    }
  })
}, { deep: true })

defineExpose({
  resetViewer: () => { showViewer.value = false },
  reload: () => {
    const img = document.querySelector('.main-image')
    if (img) {
      img.src = currentImageUrl.value + '?t=' + Date.now()
    }
  }
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
}

.image-display {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
}

.main-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.image-error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-secondary);
  gap: 12px;
}

.image-error-overlay .el-icon {
  font-size: 48px;
  color: var(--warning-color);
}

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
  background: var(--bg-color);
}

.thumbnail-item:hover {
  border-color: var(--primary-color);
  transform: scale(1.05);
}

.thumbnail-item.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.3);
}

.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
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

/* 暗色主题 */
.dark .preview-main {
  background: var(--bg-card);
}

.dark .thumbnail-section {
  background: var(--bg-card);
}

.dark .thumbnail-item {
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