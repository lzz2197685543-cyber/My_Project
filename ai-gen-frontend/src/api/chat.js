import client from './client'

export const chatApi = {
  /**
   * 普通聊天
   */
  completions(data) {
    return client.post('/api/v1/chat/completions', data)
  },

  /**
   * 流式聊天 - 使用 fetch + SSE
   */
  async stream(data, callbacks) {
    const { onChunk, onDone, onError } = callbacks || {}
    const apiKey = localStorage.getItem('api_key')

    try {
      const response = await fetch('/api/v1/chat/stream', {
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
              return
            }
            try {
              const json = JSON.parse(dataStr)
              if (json.error) {
                onError?.(json.error)
                return
              }
              const content = json.choices?.[0]?.delta?.content || ''
              if (content) {
                onChunk?.(content)
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }

      onDone?.()
    } catch (error) {
      onError?.(error.message)
    }
  }
}