// src/api/client.js
import axios from 'axios'

// ✅ 修改：不要加 /api，让请求路径自己带
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加 API Key
client.interceptors.request.use(
  (config) => {
    const apiKey = localStorage.getItem('api_key')
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
client.interceptors.response.use(
  (response) => {
    if (response.data && response.data.code !== undefined) {
      if (response.data.code === 200) {
        return response.data.data
      } else {
        return Promise.reject(new Error(response.data.message || '请求失败'))
      }
    }
    return response.data
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    const message = error.response?.data?.message || error.message || '网络请求失败'
    return Promise.reject(new Error(message))
  }
)

export default client