import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
})

export const chatApi = {
  sendMessage: async (message, model = 'deepseek-v4-flash', systemPrompt = '你是一个乐于助人的助手') => {
    try {
      const response = await api.post('/chat/', {
        model,
        message,
        system_prompt: systemPrompt,
        max_tokens: 1024,
        temperature: 0.7
      })
      return response.data
    } catch (error) {
      console.error('Chat API error:', error)
      throw error
    }
  },
  
  getModels: async () => {
    try {
      const response = await api.get('/chat/models')
      return response.data
    } catch (error) {
      console.error('Get models error:', error)
      throw error
    }
  }
}