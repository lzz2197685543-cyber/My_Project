<template>
  <div class="fuse-view">
    <!-- 左侧控制面板 -->
    <div class="control-panel-wrapper">
      <ControlPanel
        :provider="provider"
        :model="model"
        :prompt="prompt"
        :image-size="imageSize"
        :aspect-ratio="aspectRatio"
        :count="1"
        :optimize="optimize"
        :generating="isGenerating"
        :optimizing="isOptimizing"
        :show-upload="true"
        :show-count="false"
        :show-history="true"
        :max-upload="14"
        :history="history"
        @update:provider="provider = $event"
        @update:model="model = $event"
        @update:prompt="prompt = $event"
        @update:imageSize="imageSize = $event"
        @update:aspectRatio="aspectRatio = $event"
        @update:optimize="optimize = $event"
        @generate="handleGenerate"
        @optimize="handleOptimize"
        @loadHistory="loadHistory"
        @clearHistory="clearHistory"
      >
        <template #upload>
          <MultiImageUpload
            ref="multiUploadRef"
            :limit="14"
            @change="onUploadChange"
          />
        </template>
      </ControlPanel>
    </div>

    <!-- 右侧预览面板 -->
    <div class="preview-panel-wrapper">
      <div class="preview-container">
        <div class="preview-header">
          <span class="preview-title">
            {{ hasResult ? '融合结果' : '等待融合' }}
          </span>
          <div class="preview-actions">
            <el-button
              v-if="hasResult"
              size="small"
              text
              @click="downloadResult"
            >
              <el-icon><Download /></el-icon> 下载
            </el-button>
            <el-button
              v-if="hasResult"
              size="small"
              text
              type="danger"
              @click="clearResult"
            >
              <el-icon><Delete /></el-icon> 清空
            </el-button>
          </div>
        </div>

        <div class="preview-body">
          <!-- 未上传图片 -->
          <div v-if="!hasEnoughImages && !isGenerating" class="empty-state">
            <el-icon size="64"><Files /></el-icon>
            <p>请上传至少 2 张图片</p>
            <span>支持 JPG、PNG 格式，最多 14 张图，单图最大 20M</span>
          </div>

          <!-- 已上传但未生成 -->
          <div v-else-if="!hasResult && !isGenerating" class="empty-state">
            <div class="uploaded-thumbs">
              <div
                v-for="(file, index) in uploadedImages"
                :key="index"
                class="thumb-item"
              >
                <img :src="getImageUrl(file)" />
                <span class="thumb-index">{{ index + 1 }}</span>
              </div>
            </div>
            <p>已上传 {{ uploadedImages.length }} 张图片</p>
            <span>左侧输入融合提示词，点击生成</span>
          </div>

          <!-- 生成中 -->
          <div v-else-if="isGenerating" class="generating-state">
            <el-icon class="is-loading" size="48"><Loading /></el-icon>
            <p>正在融合图片...</p>
            <span>请稍候，这可能需要几秒钟</span>
          </div>

          <!-- 融合结果 -->
          <div v-else class="result-display" @click="previewImage = true">
            <img
              :key="refreshKey"
              :src="getImageUrl(generatedImages[0])"
              class="result-image"
              alt="融合结果"
              @error="handleImageError"
            />
            <div v-if="imageLoadError" class="image-error-overlay">
              <el-icon><Warning /></el-icon>
              <span>图片加载失败</span>
              <el-button size="small" @click="retryLoad">重试</el-button>
            </div>
          </div>
        </div>

        <!-- 图片信息 -->
        <div v-if="hasResult" class="preview-footer">
          <div class="image-info">
            <span>融合成功</span>
            <span class="divider">|</span>
            <span>尺寸: {{ imageSize }}</span>
            <span class="divider">|</span>
            <span>宽高比: {{ aspectRatio }}</span>
            <span class="divider">|</span>
            <span>融合图片数: {{ uploadedImages.length }} 张</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片预览弹窗 -->
    <el-image-viewer
      v-if="previewImage && hasResult"
      :url-list="[getImageUrl(generatedImages[0])]"
      :initial-index="0"
      @close="previewImage = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, onDeactivated } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Delete, Loading, Files, Warning } from '@element-plus/icons-vue'
import ControlPanel from '@/components/image/ControlPanel.vue'
import MultiImageUpload from '@/components/image/MultiImageUpload.vue'
import { useImageStore } from '@/stores/image'
import { useModelsStore } from '@/stores/models'
import { useSettingsStore } from '@/stores/settings'

const imageStore = useImageStore()
const modelsStore = useModelsStore()
const settingsStore = useSettingsStore()

// ===== 状态 =====
const provider = ref(settingsStore.defaultProvider || 'yi')
const model = ref(settingsStore.defaultImageModel || 'gemini-3.1-flash-lite-image')
const prompt = ref('')
const imageSize = ref('1K')
const aspectRatio = ref('16:9')
const optimize = ref(true)
const isOptimizing = ref(false)
const uploadedImages = ref([])
const previewImage = ref(false)
const multiUploadRef = ref(null)
const refreshKey = ref(0)
const imageLoadError = ref(false)

// ===== 计算属性 =====
const isGenerating = computed(() => imageStore.isGenerating)
const generatedImages = computed(() => imageStore.generatedImages)
const history = computed(() => imageStore.history)
const hasResult = computed(() => generatedImages.value.length > 0)
const hasEnoughImages = computed(() => uploadedImages.value.length >= 2)

// ✅ 获取图片 URL
const getImageUrl = (img) => {
  if (!img) return ''
  let url = img.url || img.path || ''
  if (url && !url.startsWith('http') && !url.startsWith('/')) {
    url = '/' + url
  }
  if (url && url.includes('data/output/')) {
    url = '/' + url.split('data/output/').pop()
  }
  if (url && url.includes('data/input/')) {
    url = '/' + url.split('data/input/').pop()
  }
  return url
}

// ✅ 获取图片的完整路径（用于后端请求）
const getImagePath = (img) => {
  if (!img) return ''
  
  if (img.path) {
    let path = img.path.replace(/\\/g, '/')
    if (path.includes(':\\') || path.includes('data/input/')) {
      return path
    }
  }
  
  if (img.url) {
    let url = img.url
    if (url.includes('/data/input/')) {
      const filename = url.split('/data/input/').pop()
      return 'D:/sd14/AI_GEN/ai-gen-backend/data/input/' + filename
    }
    if (url.includes('/input/')) {
      const filename = url.split('/input/').pop()
      return 'D:/sd14/AI_GEN/ai-gen-backend/data/input/' + filename
    }
    return url
  }
  
  if (img.name) {
    return 'D:/sd14/AI_GEN/ai-gen-backend/data/input/' + img.name
  }
  
  return ''
}

// ===== 方法 =====

const onUploadChange = (files) => {
  uploadedImages.value = files.map(f => ({
    ...f,
    path: f.path || f.url || f.name || ''
  }))
  console.log('📸 上传的文件列表:', uploadedImages.value)
  if (files.length < 2) {
    imageStore.clearImages()
  }
}

const handleGenerate = async (params) => {
  if (uploadedImages.value.length < 2) {
    ElMessage.warning('请至少上传 2 张图片进行融合')
    return
  }

  const imagePaths = uploadedImages.value
    .map(f => getImagePath(f))
    .filter(path => path && path.length > 0)

  console.log('📸 融合图片路径:', imagePaths)

  if (imagePaths.length < 2) {
    ElMessage.error('无法获取图片路径，请重新上传')
    return
  }

  refreshKey.value++
  imageLoadError.value = false

  try {
    const result = await imageStore.fuseImages({
      ...params,
      image_paths: imagePaths,
      fusion_prompt: params.prompt || prompt.value
    })
    
    if (result.success) {
      ElMessage.success('图片融合成功')
      setTimeout(() => { refreshKey.value++ }, 500)
    } else {
      ElMessage.error(result.error || '融合失败')
    }
  } catch (error) {
    console.error('❌ 融合错误:', error)
    ElMessage.error(error.message || '融合失败')
  }
}

const handleOptimize = async (text) => {
  isOptimizing.value = true
  await new Promise(resolve => setTimeout(resolve, 1500))
  prompt.value = `${text}，保持风格统一，自然过渡，完整场景`
  isOptimizing.value = false
  ElMessage.success('提示词优化完成')
}

const downloadResult = () => {
  if (generatedImages.value.length > 0) {
    const url = getImageUrl(generatedImages.value[0])
    if (url) {
      const link = document.createElement('a')
      link.href = url
      link.download = `fused_${Date.now()}.png`
      link.click()
      ElMessage.success('开始下载')
    }
  }
}

const clearResult = () => {
  imageStore.clearImages()
  imageLoadError.value = false
  ElMessage.success('已清空结果')
}

const handleImageError = () => {
  console.error('❌ 融合图片加载失败')
  imageLoadError.value = true
}

const retryLoad = () => {
  imageLoadError.value = false
  refreshKey.value++
}

const loadHistory = (item) => {
  prompt.value = item.prompt
  ElMessage.success('已加载历史提示词')
}

const clearHistory = () => {
  imageStore.clearHistory()
  ElMessage.success('已清空历史记录')
}

// ✅ keep-alive 激活时 - 清空旧图片数据（进入页面时）
onActivated(() => {
  console.log('🔄 融合页面激活')
  // 清空旧图片，避免显示其他页面的图片
  imageStore.clearImages()
  imageStore.error = null
})

// ✅ keep-alive 停用时
onDeactivated(() => {
  console.log('🔄 融合页面停用')
})

onMounted(() => {
  modelsStore.loadModels()
  // 首次加载时清空旧图片
  imageStore.clearImages()
  imageStore.error = null
})
</script>

<style scoped>
.fuse-view {
  display: flex;
  gap: 20px;
  height: 100%;
  min-height: 500px;
}

.control-panel-wrapper {
  width: 38%;
  min-width: 320px;
  max-width: 480px;
  flex-shrink: 0;
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.preview-panel-wrapper {
  flex: 1;
  min-width: 0;
  background: var(--bg-card);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.preview-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
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

.preview-body {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: var(--bg-color);
  position: relative;
  padding: 20px;
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

.uploaded-thumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-width: 400px;
  justify-content: center;
  margin-bottom: 16px;
}

.thumb-item {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid var(--border-color);
}

.thumb-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-index {
  position: absolute;
  bottom: 2px;
  right: 2px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 10px;
  padding: 0 6px;
  border-radius: 8px;
  line-height: 16px;
}

.generating-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.generating-state .el-icon {
  color: var(--primary-color);
  margin-bottom: 12px;
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

.result-display {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
}

.result-image {
  width: 100%;
  max-height: 500px;
  object-fit: contain;
  border-radius: 8px;
  transition: transform 0.3s;
}

.result-image:hover {
  transform: scale(1.01);
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

.preview-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
  background: var(--bg-card);
}

.image-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  flex-wrap: wrap;
}

.divider {
  color: var(--border-color);
}

.dark .control-panel-wrapper,
.dark .preview-panel-wrapper {
  border-color: var(--border-color);
}

.dark .preview-body {
  background: var(--bg-card);
}

.dark .thumb-item {
  border-color: var(--border-color);
}

@media (max-width: 1024px) {
  .fuse-view {
    flex-direction: column;
    gap: 16px;
  }

  .control-panel-wrapper {
    width: 100%;
    max-width: 100%;
    min-width: 0;
    max-height: 50vh;
    overflow-y: auto;
  }

  .preview-panel-wrapper {
    flex: 1;
    min-height: 300px;
  }

  .result-image {
    max-height: 350px;
  }
}

@media (max-width: 768px) {
  .control-panel-wrapper {
    max-height: 45vh;
    padding: 16px;
  }

  .preview-body {
    min-height: 200px;
    padding: 12px;
  }

  .thumb-item {
    width: 48px;
    height: 48px;
  }

  .uploaded-thumbs {
    gap: 6px;
  }

  .result-image {
    max-height: 250px;
  }
}
</style>