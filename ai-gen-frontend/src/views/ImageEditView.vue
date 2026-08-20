<template>
  <div class="image-edit-view">
    <!-- 左侧控制面板 -->
    <div class="control-panel-wrapper">
      <ControlPanel
        :provider="provider"
        :model="model"
        :prompt="prompt"
        :image-size="imageSize"
        :aspect-ratio="aspectRatio"
        :count="count"
        :optimize="optimize"
        :prompt-extend="promptExtend"
        :generating="isGenerating"
        :optimizing="isOptimizing"
        :show-upload="true"
        :show-count="true"
        :show-history="true"
        :max-upload="1"
        :history="history"
        @update:provider="provider = $event"
        @update:model="model = $event"
        @update:prompt="prompt = $event"
        @update:imageSize="imageSize = $event"
        @update:aspectRatio="aspectRatio = $event"
        @update:count="count = $event"
        @update:optimize="optimize = $event"
        @update:promptExtend="promptExtend = $event"
        @generate="handleGenerate"
        @optimize="handleOptimize"
        @loadHistory="loadHistory"
        @clearHistory="clearHistory"
      >
        <template #upload>
          <ImageUpload
            ref="uploadRef"
            v-model="uploadedImages"
            label="参考图片"
            hint="支持 JPG、PNG 格式，单图最大 20M"
            :limit="1"
            :multiple="false"
            @change="onUploadChange"
          />
          <div v-if="uploadedImages.length > 0" class="upload-preview">
            <img :src="getImageUrl(uploadedImages[0])" class="preview-thumb" />
            <span class="file-name">{{ uploadedImages[0]?.name }}</span>
            <el-tag size="small" type="success" v-if="uploadedImages[0]?.path">
              ✅ 已上传
            </el-tag>
          </div>
        </template>
      </ControlPanel>
    </div>

    <!-- 右侧预览面板 -->
    <div class="preview-panel-wrapper">
      <div class="preview-container">
        <div class="preview-header">
          <span class="preview-title">
            {{ hasResult ? '对比预览' : '等待生成' }}
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
          <div v-if="uploadedImages.length === 0 && !isGenerating" class="empty-state">
            <el-icon size="64"><Upload /></el-icon>
            <p>请先上传参考图片</p>
            <span>支持 JPG、PNG 格式，单图最大 20M</span>
          </div>

          <!-- 已上传但未生成 -->
          <div v-else-if="!hasResult && !isGenerating" class="empty-state">
            <img :src="getImageUrl(uploadedImages[0])" class="upload-preview-large" />
            <p>参考图片已上传</p>
            <span>左侧输入提示词，点击生成</span>
          </div>

          <!-- 生成中 -->
          <div v-else-if="isGenerating" class="generating-state">
            <el-icon class="is-loading" size="48"><Loading /></el-icon>
            <p>正在生成图片...</p>
            <span>请稍候，这可能需要几秒钟</span>
          </div>

          <!-- 对比展示 -->
          <div v-else class="compare-wrapper">
            <ImageCompare
              :key="compareKey"
              :original-image="getOriginalImageUrl()"
              :generated-image="getGeneratedImageUrl()"
            />
          </div>
        </div>

        <!-- 缩略图 -->
        <div v-if="hasResult" class="thumbnail-bar">
          <div class="thumbnail-item original-thumb">
            <img :src="getOriginalImageUrl()" />
            <span>原图</span>
          </div>
          <el-icon><Right /></el-icon>
          <div class="thumbnail-item result-thumb">
            <img :src="getGeneratedImageUrl()" />
            <span>生成图</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, onDeactivated } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Download, Delete, Loading, Right } from '@element-plus/icons-vue'
import ControlPanel from '@/components/image/ControlPanel.vue'
import ImageUpload from '@/components/image/ImageUpload.vue'
import ImageCompare from '@/components/image/ImageCompare.vue'
import { useImageStore } from '@/stores/image'
import { useModelsStore } from '@/stores/models'
import { useSettingsStore } from '@/stores/settings'

const imageStore = useImageStore()
const modelsStore = useModelsStore()
const settingsStore = useSettingsStore()
const uploadRef = ref(null)

// ===== 状态 =====
const provider = ref(settingsStore.defaultProvider || 'yi')
const model = ref(settingsStore.defaultImageModel || 'gemini-3.1-flash-lite-image')
const prompt = ref('')
const imageSize = ref('1K')
const aspectRatio = ref('1:1')
const count = ref(1)
const optimize = ref(true)
const promptExtend = ref(false)
const isOptimizing = ref(false)
const uploadedImages = ref([])
const refreshKey = ref(0)
const compareKey = ref(0)

// ===== 计算属性 =====
const isGenerating = computed(() => imageStore.isGenerating)
const generatedImages = computed(() => imageStore.generatedImages)
const history = computed(() => imageStore.history)
const hasResult = computed(() => generatedImages.value.length > 0)

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
  return url
}

// ✅ 获取原图 URL (上传的图片)
const getOriginalImageUrl = () => {
  if (uploadedImages.value.length === 0) return ''
  const img = uploadedImages.value[0]
  return getImageUrl(img)
}

// ✅ 获取生成图 URL
const getGeneratedImageUrl = () => {
  if (generatedImages.value.length === 0) return ''
  const img = generatedImages.value[0]
  return getImageUrl(img)
}

// ===== 方法 =====

const onUploadChange = (files) => {
  uploadedImages.value = files
  if (files.length === 0) {
    imageStore.clearImages()
  }
  console.log('📸 上传的图片:', files)
}

const handleGenerate = async (params) => {
  if (uploadedImages.value.length === 0) {
    ElMessage.warning('请先上传参考图片')
    return
  }

  const file = uploadedImages.value[0]
  console.log('📸 原始文件数据:', file)
  
  let sourceImage = file.path || ''
  if (!sourceImage) {
    sourceImage = file.url || ''
  }
  
  if (sourceImage && sourceImage.includes(':\\')) {
    sourceImage = sourceImage.replace(/\\/g, '/')
    if (sourceImage.includes('data/input/')) {
      const filename = sourceImage.split('data/input/').pop()
      sourceImage = '/data/input/' + filename
    }
  }
  
  if (sourceImage && !sourceImage.startsWith('http') && !sourceImage.startsWith('/')) {
    sourceImage = '/' + sourceImage
  }

  console.log('📸 最终源图片路径:', sourceImage)
  
  if (!sourceImage) {
    ElMessage.error('无法获取图片路径，请重新上传')
    return
  }

  refreshKey.value++
  try {
    const result = await imageStore.imageToImage({
      ...params,
      source_image: sourceImage
    })
    
    if (result.success) {
      ElMessage.success('图片生成成功')
      setTimeout(() => {
        compareKey.value++
        refreshKey.value++
      }, 500)
    } else {
      ElMessage.error(result.error || '生成失败')
    }
  } catch (error) {
    ElMessage.error(error.message || '生成失败')
  }
}

const handleOptimize = async (text) => {
  isOptimizing.value = true
  await new Promise(resolve => setTimeout(resolve, 1500))
  prompt.value = `${text}，保持原图构图，风格转换，高质量细节`
  isOptimizing.value = false
  ElMessage.success('提示词优化完成')
}

const downloadResult = () => {
  const url = getGeneratedImageUrl()
  if (url) {
    const link = document.createElement('a')
    link.href = url
    link.download = `edited_${Date.now()}.png`
    link.click()
    ElMessage.success('开始下载')
  }
}

const clearResult = () => {
  imageStore.clearImages()
  ElMessage.success('已清空结果')
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
  console.log('🔄 图生图页面激活')
  // 清空旧图片，避免显示其他页面的图片
  imageStore.clearImages()
  imageStore.error = null
})

// ✅ keep-alive 停用时
onDeactivated(() => {
  console.log('🔄 图生图页面停用')
})

onMounted(() => {
  modelsStore.loadModels()
  // 首次加载时清空旧图片
  imageStore.clearImages()
  imageStore.error = null
})
</script>

<style scoped>
.image-edit-view {
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
}

.upload-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--bg-color);
  border-radius: 8px;
  margin-top: 8px;
}

.preview-thumb {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  object-fit: cover;
}

.file-name {
  font-size: 13px;
  color: var(--text-regular);
}

.upload-preview-large {
  max-height: 300px;
  max-width: 100%;
  object-fit: contain;
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

.compare-wrapper {
  width: 100%;
  height: 100%;
  min-height: 350px;
}

.thumbnail-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
  background: var(--bg-card);
}

.thumbnail-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.thumbnail-item img {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  border: 2px solid var(--border-color);
  object-fit: cover;
}

.thumbnail-item.original-thumb img {
  border-color: var(--primary-color);
}

.thumbnail-item.result-thumb img {
  border-color: var(--success-color);
}

.dark .control-panel-wrapper,
.dark .preview-panel-wrapper {
  border-color: var(--border-color);
}

.dark .preview-body {
  background: var(--bg-card);
}

.dark .upload-preview {
  background: var(--bg-card);
}

@media (max-width: 1024px) {
  .image-edit-view {
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

  .compare-wrapper {
    min-height: 250px;
  }
}

@media (max-width: 768px) {
  .control-panel-wrapper {
    max-height: 45vh;
    padding: 16px;
  }

  .preview-body {
    min-height: 200px;
  }

  .thumbnail-item img {
    width: 36px;
    height: 36px;
  }

  .upload-preview-large {
    max-height: 200px;
  }
}
</style>