// src/constants/models.js
/**
 * 模型常量定义
 */

// ==================== API易 图片模型 ====================
export const YI_IMAGE_MODELS = [
  { id: 'gemini-3.1-flash-lite-image', display_name: 'Gemini 3.1 Flash Lite', type: 'image', provider: 'yi' },
  { id: 'gemini-3.1-flash-image-preview', display_name: 'Gemini 3.1 Flash', type: 'image', provider: 'yi' },
  { id: 'gemini-2.5-flash-image', display_name: 'Gemini 2.5 Flash', type: 'image', provider: 'yi' },
  { id: 'gemini-3-pro-image-preview', display_name: 'Gemini 3 Pro', type: 'image', provider: 'yi' },
  { id: 'gpt-image-2', display_name: 'GPT-Image 2', type: 'image', provider: 'yi' },
  { id: 'gpt-image-2-all', display_name: 'GPT-Image 2 All', type: 'image', provider: 'yi' },
  { id: 'gpt-image-2-vip', display_name: 'GPT-Image 2 VIP', type: 'image', provider: 'yi' }
]

// ==================== API易 聊天模型 ====================
export const YI_CHAT_MODELS = [
  { id: 'deepseek-chat', display_name: 'DeepSeek Chat', type: 'chat', provider: 'yi' },
  { id: 'deepseek-reasoner', display_name: 'DeepSeek Reasoner', type: 'chat', provider: 'yi' },
  { id: 'deepseek-v4-flash', display_name: 'DeepSeek V4 Flash', type: 'chat', provider: 'yi' },
  { id: 'deepseek-v3.2', display_name: 'DeepSeek V3.2', type: 'chat', provider: 'yi' },
  { id: 'qwen3.6-flash', display_name: 'Qwen 3.6 Flash', type: 'chat', provider: 'yi' },
  { id: 'qwen3.5-flash', display_name: 'Qwen 3.5 Flash', type: 'chat', provider: 'yi' },
  { id: 'gemini-2.5-flash', display_name: 'Gemini 2.5 Flash', type: 'chat', provider: 'yi' },
  { id: 'gemini-3.1-pro-preview', display_name: 'Gemini 3.1 Pro', type: 'chat', provider: 'yi' },
  { id: 'gpt-4.1-mini', display_name: 'GPT 4.1 Mini', type: 'chat', provider: 'yi' },
  { id: 'gpt-4o-mini', display_name: 'GPT 4o Mini', type: 'chat', provider: 'yi' },
  { id: 'gpt-5.4-pro', display_name: 'GPT 5.4 Pro', type: 'chat', provider: 'yi' },
  { id: 'claude-haiku-4-5-20251001', display_name: 'Claude Haiku 4.5', type: 'chat', provider: 'yi' },
  { id: 'claude-opus-5', display_name: 'Claude Opus 5', type: 'chat', provider: 'yi' }
]

// ==================== 百炼 图片模型 ====================
export const BAILIAN_IMAGE_MODELS = [
  { id: 'z-image-turbo', display_name: 'Z-Image-Turbo', type: 'image', provider: 'bailian', supports_text2img: true, supports_img2img: false },
  { id: 'wan2.7-image-pro', display_name: '万相 2.7 Pro', type: 'image', provider: 'bailian', supports_text2img: true, supports_img2img: true },
  { id: 'wan2.7-image', display_name: '万相 2.7', type: 'image', provider: 'bailian', supports_text2img: true, supports_img2img: true },
  { id: 'qwen-image-3.0-pro', display_name: '千问 Image 3.0 Pro', type: 'image', provider: 'bailian', supports_text2img: true, supports_img2img: true },
  { id: 'qwen-image-3.0', display_name: '千问 Image 3.0', type: 'image', provider: 'bailian', supports_text2img: true, supports_img2img: true },
  { id: 'qwen-image-2.0-pro', display_name: '千问 Image 2.0 Pro', type: 'image', provider: 'bailian', supports_text2img: true, supports_img2img: true },
  { id: 'qwen-image-2.0', display_name: '千问 Image 2.0', type: 'image', provider: 'bailian', supports_text2img: true, supports_img2img: false }
]

// ==================== 百炼 聊天模型 ====================
export const BAILIAN_CHAT_MODELS = [
  { id: 'qwen3.8-max', display_name: 'Qwen 3.8 Max', type: 'chat', provider: 'bailian' },
  { id: 'qwen3.7-max', display_name: 'Qwen 3.7 Max', type: 'chat', provider: 'bailian' },
  { id: 'qwen3.6-plus', display_name: 'Qwen 3.6 Plus', type: 'chat', provider: 'bailian' },
  { id: 'qwen3.7-plus', display_name: 'Qwen 3.7 Plus', type: 'chat', provider: 'bailian' },
  { id: 'qwen3.6-flash', display_name: 'Qwen 3.6 Flash', type: 'chat', provider: 'bailian' },
  { id: 'qwen3.7-flash', display_name: 'Qwen 3.7 Flash', type: 'chat', provider: 'bailian' },
  { id: 'qwen-plus', display_name: 'Qwen Plus', type: 'chat', provider: 'bailian' },
  { id: 'qwen-turbo', display_name: 'Qwen Turbo', type: 'chat', provider: 'bailian' },
  { id: 'qwen-flash', display_name: 'Qwen Flash', type: 'chat', provider: 'bailian' },
  { id: 'deepseek-v4-pro', display_name: 'DeepSeek V4 Pro', type: 'chat', provider: 'bailian' },
  { id: 'deepseek-v4-flash', display_name: 'DeepSeek V4 Flash', type: 'chat', provider: 'bailian' },
  { id: 'deepseek-r1', display_name: 'DeepSeek R1', type: 'chat', provider: 'bailian' },
  { id: 'kimi-k2.7-code', display_name: 'Kimi K2.7 Code', type: 'chat', provider: 'bailian' },
  { id: 'glm-5.2', display_name: 'GLM 5.2', type: 'chat', provider: 'bailian' },
  { id: 'MiniMax-M2.5', display_name: 'MiniMax M2.5', type: 'chat', provider: 'bailian' },
  { id: 'mimo-v2.5-pro', display_name: 'MiMo V2.5 Pro', type: 'chat', provider: 'bailian' }
]

// ==================== 模型映射 ====================
export const ALL_MODELS = {
  yi: {
    image: YI_IMAGE_MODELS,
    chat: YI_CHAT_MODELS
  },
  bailian: {
    image: BAILIAN_IMAGE_MODELS,
    chat: BAILIAN_CHAT_MODELS
  }
}

// ==================== 默认值 ====================
// ✅ 添加 DEFAULT_PROVIDER 导出
export const DEFAULT_PROVIDER = 'yi'
export const DEFAULT_CHAT_MODEL = 'deepseek-chat'
export const DEFAULT_IMAGE_MODEL = 'gemini-3.1-flash-lite-image'

// 从环境变量读取（如果有）
export const getDefaultProvider = () => {
  return import.meta.env.VITE_DEFAULT_PROVIDER || DEFAULT_PROVIDER
}

export const getDefaultChatModel = () => {
  return import.meta.env.VITE_DEFAULT_CHAT_MODEL || DEFAULT_CHAT_MODEL
}

export const getDefaultImageModel = () => {
  return import.meta.env.VITE_DEFAULT_IMAGE_MODEL || DEFAULT_IMAGE_MODEL
}