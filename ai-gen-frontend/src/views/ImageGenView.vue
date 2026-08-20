<template>
  <div class="image-gen-view">
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
        :show-upload="false"
        :show-count="true"
        :show-history="true"
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
      />
    </div>

    <!-- 右侧预览面板 -->
    <div class="preview-panel-wrapper">
      <PreviewPanel
        :key="refreshKey"
        :images="displayImages"
        :is-generating="isGenerating"
        :progress="progress"
        :image-size="imageSize"
        :aspect-ratio="aspectRatio"
        :model-name="model"
        :current-image="currentDisplayImage"
        @select-image="selectImage"
        @remove-image="removeImage"
        @clear-all="clearAll"
        @download-all="downloadAll"
        @retry="handleRetry"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import ControlPanel from '@/components/image/ControlPanel.vue'
import PreviewPanel from '@/components/image/PreviewPanel.vue'
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
const aspectRatio = ref('1:1')
const count = ref(1)
const optimize = ref(true)
const promptExtend = ref(false)
const isOptimizing = ref(false)
const progress = ref(0)
const refreshKey = ref(0)

// ===== 计算属性 =====
const isGenerating = computed(() => imageStore.isGenerating)
const generatedImages = computed(() => imageStore.generatedImages)
const currentImage = computed(() => imageStore.currentImage)
const history = computed(() => imageStore.history)

// ✅ 处理图片显示 - 确保 URL 正确
const displayImages = computed(() => {
  return generatedImages.value.map(img => {
    // 确保 url 以 / 开头
    let url = img.url || img.path || ''
    if (url && !url.startsWith('http') && !url.startsWith('/')) {
      url = '/' + url
    }
    // 处理 Windows 路径
    if (url && url.includes(':\\')) {
      url = url.replace(/\\/g, '/')
      if (url.includes('data/output/')) {
        url = '/' + url.split('data/output/').pop()
      } else if (url.includes('output/')) {
        url = '/' + url.split('output/').pop()
      }
    }
    console.log('🖼️ displayImages URL:', url)
    return { ...img, url }
  })
})

const currentDisplayImage = computed(() => {
  if (currentImage.value) {
    const found = displayImages.value.find(i => 
      i.path === currentImage.value.path || 
      i.url === currentImage.value.url
    )
    return found || displayImages.value[0] || null
  }
  return displayImages.value[0] || null
})

// ===== 方法 =====

// 生成图片
const handleGenerate = async (params) => {
  try {
    refreshKey.value++
    const result = await imageStore.textToImage(params)
    console.log('📦 生成结果:', result)
    
    if (result.success) {
      ElMessage.success(`成功生成 ${result.images?.length || 0} 张图片`)
      // 延迟刷新预览
      setTimeout(() => {
        refreshKey.value++
        nextTick(() => {
          console.log('🔄 预览刷新完成')
        })
      }, 800)
    } else {
      ElMessage.error(result.error || '生成失败')
    }
  } catch (error) {
    console.error('❌ 生成错误:', error)
    ElMessage.error(error.message || '生成失败')
  }
}

// 优化提示词
const handleOptimize = async (text) => {
  isOptimizing.value = true
  await new Promise(resolve => setTimeout(resolve, 1500))
  prompt.value = `${text}，高清细节，电影级布光，专业摄影构图`
  isOptimizing.value = false
  ElMessage.success('提示词优化完成')
}

// 加载历史
const loadHistory = (item) => {
  prompt.value = item.prompt
  ElMessage.success('已加载历史提示词')
}

// 清空历史
const clearHistory = () => {
  imageStore.clearHistory()
  ElMessage.success('已清空历史记录')
}

// 选择图片
const selectImage = (index) => {
  imageStore.selectImage(index)
}

// 删除图片
const removeImage = (index) => {
  imageStore.removeImage(index)
}

// 清空所有
const clearAll = () => {
  imageStore.clearImages()
  ElMessage.success('已清空所有图片')
}

// 下载全部
const downloadAll = (images) => {
  images.forEach((img, index) => {
    setTimeout(() => {
      const url = img.url || img.path
      if (url) {
        const link = document.createElement('a')
        link.href = url
        link.download = `generated_${index + 1}.png`
        link.click()
      }
    }, index * 200)
  })
  ElMessage.success(`开始下载 ${images.length} 张图片`)
}

// 重试
const handleRetry = () => {
  if (prompt.value) {
    refreshKey.value++
    handleGenerate({
      prompt: prompt.value,
      model: model.value,
      provider: provider.value,
      imageSize: imageSize.value,
      aspectRatio: aspectRatio.value,
      count: count.value,
      optimize: optimize.value,
      promptExtend: promptExtend.value
    })
  }
}

// ===== 生命周期 =====
onMounted(() => {
  modelsStore.loadModels()
})

// 监听生成完成，刷新预览
watch(() => imageStore.isGenerating, (newVal) => {
  if (!newVal && imageStore.generatedImages.length > 0) {
    setTimeout(() => {
      refreshKey.value++
      console.log('🔄 生成完成，刷新预览')
    }, 500)
  }
})
</script>

<style scoped>
.image-gen-view {
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

/* 暗色主题 */
.dark .control-panel-wrapper,
.dark .preview-panel-wrapper {
  border-color: var(--border-color);
}

/* 响应式 */
@media (max-width: 1024px) {
  .image-gen-view {
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
}

@media (max-width: 768px) {
  .control-panel-wrapper {
    max-height: 45vh;
    padding: 16px;
  }
}
</style>