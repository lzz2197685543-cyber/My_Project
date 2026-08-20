import client from './client'

export const modelsApi = {
  /**
   * 获取所有模型
   */
  listModels(provider) {
    const url = provider ? `/api/v1/models?provider=${provider}` : '/api/v1/models'
    return client.get(url)
  },

  /**
   * 获取提供商列表
   */
  listProviders() {
    return client.get('/api/v1/models/providers')
  },

  /**
   * 获取指定提供商的模型
   */
  getModelsByProvider(provider) {
    return client.get(`/api/v1/models/${provider}`)
  }
}