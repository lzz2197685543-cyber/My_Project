/**
 * 流式处理组合式函数
 */
import { ref } from 'vue'

export function useStream() {
  const isStreaming = ref(false)
  const streamError = ref(null)
  const streamContent = ref('')

  /**
   * 执行流式请求
   * @param {string} url - 请求地址
   * @param {object} data - 请求数据
   * @param {object} callbacks - 回调函数
   */
  const startStream = async (url, data, callbacks = {}) => {
    const { onChunk, onDone, onError, onStart } = callbacks

    isStreaming.value = true
    streamError.value = null
    streamContent.value = ''
    onStart?.()

    try {
      const apiKey = localStorage.getItem('api_key')
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey || ''
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`HTTP ${response.status}: ${errorText}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmedLine = line.trim()
          if (!trimmedLine) continue

          if (trimmedLine.startsWith('data: ')) {
            const dataStr = trimmedLine.slice(6)
            if (dataStr === '[DONE]') {
              onDone?.()
              isStreaming.value = false
              return
            }
            try {
              const json = JSON.parse(dataStr)
              if (json.error) {
                throw new Error(json.error)
              }
              const content = json.choices?.[0]?.delta?.content || ''
              if (content) {
                streamContent.value += content
                onChunk?.(content)
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }

      onDone?.()
      isStreaming.value = false

    } catch (error) {
      streamError.value = error.message
      isStreaming.value = false
      onError?.(error.message)
    }
  }

  // 停止流式
  const stopStream = () => {
    isStreaming.value = false
  }

  // 重置状态
  const resetStream = () => {
    isStreaming.value = false
    streamError.value = null
    streamContent.value = ''
  }

  return {
    isStreaming,
    streamError,
    streamContent,
    startStream,
    stopStream,
    resetStream
  }
}