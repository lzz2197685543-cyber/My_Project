// src/stores/settings.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { DEFAULT_PROVIDER, DEFAULT_CHAT_MODEL, DEFAULT_IMAGE_MODEL } from '@/constants/models'

export const useSettingsStore = defineStore('settings', () => {
  // ===== State =====
  const theme = ref(localStorage.getItem('theme') || 'light')
  const apiKey = ref(localStorage.getItem('api_key') || '')
  const yiApiKey = ref(localStorage.getItem('yi_api_key') || '')
  const yiAccessToken = ref(localStorage.getItem('yi_access_token') || '')
  const bailianApiKey = ref(localStorage.getItem('bailian_api_key') || '')
  const defaultProvider = ref(localStorage.getItem('default_provider') || DEFAULT_PROVIDER)
  const defaultChatModel = ref(localStorage.getItem('default_chat_model') || DEFAULT_CHAT_MODEL)
  const defaultImageModel = ref(localStorage.getItem('default_image_model') || DEFAULT_IMAGE_MODEL)

  // ===== Getters =====
  const isDark = computed(() => theme.value === 'dark')

  // ===== Actions =====

  // 切换主题
  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', theme.value)
    applyTheme()
  }

  // 设置主题
  function setTheme(value) {
    if (value === 'light' || value === 'dark') {
      theme.value = value
      localStorage.setItem('theme', value)
      applyTheme()
    }
  }

  // 应用主题
  function applyTheme() {
    if (theme.value === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark')
    } else {
      document.documentElement.removeAttribute('data-theme')
    }
  }

  // 保存 API Key
  function setApiKey(key) {
    apiKey.value = key
    localStorage.setItem('api_key', key)
  }

  // 保存 API易 Key
  function setYiApiKey(key) {
    yiApiKey.value = key
    localStorage.setItem('yi_api_key', key)
    if (defaultProvider.value === 'yi') {
      apiKey.value = key
      localStorage.setItem('api_key', key)
    }
  }

  // 保存 API易 Access Token
  function setYiAccessToken(token) {
    yiAccessToken.value = token
    localStorage.setItem('yi_access_token', token)
  }

  // 保存百炼 Key
  function setBailianApiKey(key) {
    bailianApiKey.value = key
    localStorage.setItem('bailian_api_key', key)
    if (defaultProvider.value === 'bailian') {
      apiKey.value = key
      localStorage.setItem('api_key', key)
    }
  }

  // 保存默认提供商
  function setDefaultProvider(provider) {
    defaultProvider.value = provider
    localStorage.setItem('default_provider', provider)
    if (provider === 'yi') {
      apiKey.value = yiApiKey.value
    } else {
      apiKey.value = bailianApiKey.value
    }
    localStorage.setItem('api_key', apiKey.value)
  }

  // 保存默认聊天模型
  function setDefaultChatModel(model) {
    defaultChatModel.value = model
    localStorage.setItem('default_chat_model', model)
  }

  // 保存默认图片模型
  function setDefaultImageModel(model) {
    defaultImageModel.value = model
    localStorage.setItem('default_image_model', model)
  }

  // 初始化
  function init() {
    applyTheme()
  }

  return {
    // State
    theme,
    apiKey,
    yiApiKey,
    yiAccessToken,
    bailianApiKey,
    defaultProvider,
    defaultChatModel,
    defaultImageModel,

    // Getters
    isDark,

    // Actions
    toggleTheme,
    setTheme,
    applyTheme,
    setApiKey,
    setYiApiKey,
    setYiAccessToken,
    setBailianApiKey,
    setDefaultProvider,
    setDefaultChatModel,
    setDefaultImageModel,
    init
  }
})