import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { modelsApi } from '@/api/models'
import { ALL_MODELS, DEFAULT_PROVIDER, DEFAULT_CHAT_MODEL, DEFAULT_IMAGE_MODEL } from '@/constants/models'

export const useModelsStore = defineStore('models', () => {
  // ===== State =====
  const models = ref({})
  const providers = ref([])
  const selectedProvider = ref(DEFAULT_PROVIDER)
  const selectedChatModel = ref(DEFAULT_CHAT_MODEL)
  const selectedImageModel = ref(DEFAULT_IMAGE_MODEL)
  const isLoading = ref(false)
  const error = ref(null)

  // ===== Getters =====
  const chatModels = computed(() => {
    return models.value[selectedProvider.value]?.chat || []
  })

  const imageModels = computed(() => {
    return models.value[selectedProvider.value]?.image || []
  })

  const allModels = computed(() => {
    const result = []
    for (const provider of Object.keys(models.value)) {
      const providerModels = models.value[provider]
      if (providerModels) {
        result.push(...(providerModels.chat || []))
        result.push(...(providerModels.image || []))
      }
    }
    return result
  })

  // ===== Actions =====

  // 加载模型
  async function loadModels() {
    isLoading.value = true
    error.value = null

    try {
      // 使用本地常量，避免API调用失败
      models.value = ALL_MODELS
      providers.value = Object.keys(ALL_MODELS)

      // 尝试从API获取最新数据
      try {
        const result = await modelsApi.listModels()
        if (result && result.models) {
          // 合并API数据
          const apiModels = result.models
          const merged = { yi: { image: [], chat: [] }, bailian: { image: [], chat: [] } }

          for (const model of apiModels) {
            if (merged[model.provider] && merged[model.provider][model.type]) {
              merged[model.provider][model.type].push(model)
            }
          }

          // 如果有数据，使用API数据
          if (merged.yi.image.length > 0 || merged.yi.chat.length > 0) {
            models.value = merged
          }
        }
      } catch (apiErr) {
        console.warn('API模型加载失败，使用本地常量:', apiErr.message)
        // 继续使用本地常量
      }

    } catch (err) {
      error.value = err.message
      // 出错时使用本地常量
      models.value = ALL_MODELS
      providers.value = Object.keys(ALL_MODELS)
    } finally {
      isLoading.value = false
    }
  }

  // 获取指定提供商的模型
  function getModelsByProvider(provider, type) {
    if (type) {
      return models.value[provider]?.[type] || []
    }
    return models.value[provider] || { image: [], chat: [] }
  }

  // 切换提供商
  function setProvider(provider) {
    if (providers.value.includes(provider)) {
      selectedProvider.value = provider
    }
  }

  // 切换聊天模型
  function setChatModel(model) {
    selectedChatModel.value = model
  }

  // 切换图片模型
  function setImageModel(model) {
    selectedImageModel.value = model
  }

  return {
    // State
    models,
    providers,
    selectedProvider,
    selectedChatModel,
    selectedImageModel,
    isLoading,
    error,

    // Getters
    chatModels,
    imageModels,
    allModels,

    // Actions
    loadModels,
    getModelsByProvider,
    setProvider,
    setChatModel,
    setImageModel
  }
})