/**
 * 提供商常量定义
 */

export const PROVIDERS = {
  YI: {
    id: 'yi',
    name: 'API易',
    description: '支持 Gemini 和 GPT-Image 系列模型'
  },
  BAILIAN: {
    id: 'bailian',
    name: '百炼',
    description: '阿里云百炼平台'
  }
}

export const PROVIDER_LIST = Object.values(PROVIDERS)

export const DEFAULT_PROVIDER = import.meta.env.VITE_DEFAULT_PROVIDER || 'yi'