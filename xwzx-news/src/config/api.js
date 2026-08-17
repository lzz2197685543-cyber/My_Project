/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 */

// API基础URL配置
export const apiConfig = {
  // 后端API基础URL
  baseURL: 'http://127.0.0.1:8000',
}

export const aiChatConfig = {
  // OpenAI API地址
  apiEndpoint: 'https://ws-5vz62sfwt5od2rps.cn-beijing.maas.aliyuncs.com/compatible-mode/v1',
  
  // API Key (由开发人员指定)
  apiKey: 'sk-ws-H.EEYMLIL.gjC3.MEUCIQDlSLy5Rhj6Eo2ERzW-uwzECFSmh7sJDJNiHNblpNYS7AIgK2xivVP0SSPBAEuWYbHeiHw3u2jnj3-v7aiccVK9PH0',
  
  // 使用的模型
  model: 'qwen3.6-flash'
}
