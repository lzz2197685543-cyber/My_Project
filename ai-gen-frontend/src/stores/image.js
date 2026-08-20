// src/stores/image.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { imageApi } from '@/api/image'

// ✅ 创建独立的图片 Store（每个页面实例独立）
export const useImageStore = defineStore('image', () => {
  const isGenerating = ref(false)
  const generatedImages = ref([])
  const currentImage = ref(null)
  const history = ref([])
  const error = ref(null)

  const hasImages = computed(() => generatedImages.value.length > 0)
  const imageCount = computed(() => generatedImages.value.length)

  // ✅ 统一处理图片URL
  const processImageUrl = (img) => {
    if (!img) return null
    
    let url = img.url || img.path || ''
    
    if (!url) {
      return { ...img, url: '' }
    }
    
    if (!url.startsWith('http') && !url.startsWith('/')) {
      url = '/' + url
    }
    
    if (url.includes(':\\')) {
      url = url.replace(/\\/g, '/')
      if (url.includes('data/output/')) {
        const relative = url.split('data/output/').pop()
        url = '/output/' + relative
      } else if (url.includes('output/')) {
        const relative = url.split('output/').pop()
        url = '/output/' + relative
      }
    }
    
    console.log('🖼️ 处理后的图片URL:', url)
    return { ...img, url }
  }

  // 文生图
  async function textToImage(params) {
    error.value = null
    isGenerating.value = true
    generatedImages.value = []
    currentImage.value = null

    try {
      const result = await imageApi.textToImage(params)
      console.log('📦 文生图结果:', result)
      
      if (result && result.success !== false) {
        const rawImages = result.images || []
        const processedImages = rawImages.map(img => processImageUrl(img)).filter(Boolean)
        
        console.log('🖼️ 处理后的图片列表:', processedImages)
        
        generatedImages.value = processedImages
        if (processedImages.length > 0) {
          currentImage.value = processedImages[0]
        }
        
        addHistory({
          type: 'text-to-image',
          prompt: params.prompt,
          images: processedImages,
          params: params
        })
        return { success: true, images: processedImages }
      } else {
        error.value = result?.error || '生成失败'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = err.message || '生成失败'
      return { success: false, error: error.value }
    } finally {
      isGenerating.value = false
    }
  }

  // 图生图
  async function imageToImage(params) {
    error.value = null
    isGenerating.value = true
    generatedImages.value = []
    currentImage.value = null

    try {
      const result = await imageApi.imageToImage(params)
      console.log('📦 图生图结果:', result)
      
      if (result && result.success !== false) {
        const rawImages = result.images || []
        const processedImages = rawImages.map(img => processImageUrl(img)).filter(Boolean)
        
        generatedImages.value = processedImages
        if (processedImages.length > 0) {
          currentImage.value = processedImages[0]
        }
        
        addHistory({
          type: 'image-to-image',
          prompt: params.prompt,
          images: processedImages,
          params: params
        })
        return { success: true, images: processedImages }
      } else {
        error.value = result?.error || '生成失败'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = err.message || '生成失败'
      return { success: false, error: error.value }
    } finally {
      isGenerating.value = false
    }
  }

  // 多图融合
  async function fuseImages(params) {
    error.value = null
    isGenerating.value = true
    generatedImages.value = []
    currentImage.value = null

    try {
      const result = await imageApi.fuse(params)
      console.log('📦 融合结果:', result)
      
      if (result && result.success !== false) {
        const rawImages = result.images || []
        const processedImages = rawImages.map(img => processImageUrl(img)).filter(Boolean)
        
        generatedImages.value = processedImages
        if (processedImages.length > 0) {
          currentImage.value = processedImages[0]
        }
        
        addHistory({
          type: 'fuse',
          prompt: params.fusion_prompt,
          images: processedImages,
          params: params
        })
        return { success: true, images: processedImages }
      } else {
        error.value = result?.error || '融合失败'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = err.message || '融合失败'
      return { success: false, error: error.value }
    } finally {
      isGenerating.value = false
    }
  }

  function addHistory(item) {
    history.value.unshift({
      id: Date.now(),
      ...item,
      timestamp: new Date().toISOString()
    })
    if (history.value.length > 50) {
      history.value = history.value.slice(0, 50)
    }
  }

  function clearImages() {
    generatedImages.value = []
    currentImage.value = null
  }

  function selectImage(index) {
    if (generatedImages.value[index]) {
      currentImage.value = generatedImages.value[index]
    }
  }

  function removeImage(index) {
    generatedImages.value.splice(index, 1)
    if (generatedImages.value.length === 0) {
      currentImage.value = null
    } else if (currentImage.value === generatedImages.value[index]) {
      currentImage.value = generatedImages.value[0]
    }
  }

  function clearHistory() {
    history.value = []
  }

  // ✅ 重置所有状态（页面离开时调用）
  function reset() {
    isGenerating.value = false
    generatedImages.value = []
    currentImage.value = null
    error.value = null
    console.log('🔄 图片 Store 已重置')
  }

  return {
    isGenerating,
    generatedImages,
    currentImage,
    history,
    error,
    hasImages,
    imageCount,
    textToImage,
    imageToImage,
    fuseImages,
    clearImages,
    selectImage,
    removeImage,
    clearHistory,
    reset
  }
})