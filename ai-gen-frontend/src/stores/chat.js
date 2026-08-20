import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chatApi } from '@/api/chat'
import { DEFAULT_CHAT_MODEL, DEFAULT_PROVIDER } from '@/constants/models'

export const useChatStore = defineStore('chat', () => {
  // ===== State =====
  const messages = ref([])
  const isLoading = ref(false)
  const isStreaming = ref(false)
  const streamContent = ref('')
  const currentModel = ref(DEFAULT_CHAT_MODEL)
  const currentProvider = ref(DEFAULT_PROVIDER)
  const error = ref(null)
  const conversations = ref([])
  const currentConversationId = ref(null)

  // ===== Getters =====
  const hasMessages = computed(() => messages.value.length > 0)
  const lastMessage = computed(() => messages.value[messages.value.length - 1] || null)
  const isAssistantTyping = computed(() => isLoading.value || isStreaming.value)

  // ===== Actions =====

  // 发送消息
  async function sendMessage(content) {
    if (!content.trim()) return

    error.value = null

    // 添加用户消息
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    }
    messages.value.push(userMessage)

    isLoading.value = true
    isStreaming.value = true
    streamContent.value = ''

    // 添加助手占位消息
    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      streaming: true
    }
    messages.value.push(assistantMessage)
    const assistantIndex = messages.value.length - 1

    try {
      const data = {
        messages: messages.value
          .filter(m => m.role !== 'system' || m.content)
          .map(m => ({
            role: m.role,
            content: m.content
          })),
        model: currentModel.value,
        provider: currentProvider.value,
        max_tokens: 2048,
        temperature: 0.7
      }

      await chatApi.stream(data, {
        onChunk: (chunk) => {
          streamContent.value += chunk
          messages.value[assistantIndex].content = streamContent.value
        },
        onDone: () => {
          isStreaming.value = false
          messages.value[assistantIndex].streaming = false
          isLoading.value = false
          // 更新会话
          updateConversation()
        },
        onError: (err) => {
          error.value = err
          isStreaming.value = false
          messages.value[assistantIndex].content = `❌ 错误: ${err}`
          messages.value[assistantIndex].streaming = false
          isLoading.value = false
        }
      })
    } catch (err) {
      error.value = err.message
      isStreaming.value = false
      messages.value[assistantIndex].content = `❌ 错误: ${err.message}`
      messages.value[assistantIndex].streaming = false
      isLoading.value = false
    }
  }

  // 更新会话
  function updateConversation() {
    if (!currentConversationId.value) {
      const conversation = {
        id: Date.now(),
        title: messages.value[0]?.content?.slice(0, 30) || '新对话',
        messages: JSON.parse(JSON.stringify(messages.value)),
        updatedAt: new Date().toISOString()
      }
      conversations.value.unshift(conversation)
      currentConversationId.value = conversation.id
    } else {
      const index = conversations.value.findIndex(c => c.id === currentConversationId.value)
      if (index !== -1) {
        conversations.value[index].messages = JSON.parse(JSON.stringify(messages.value))
        conversations.value[index].updatedAt = new Date().toISOString()
      }
    }
  }

  // 加载会话
  function loadConversation(id) {
    const conversation = conversations.value.find(c => c.id === id)
    if (conversation) {
      messages.value = JSON.parse(JSON.stringify(conversation.messages))
      currentConversationId.value = conversation.id
    }
  }

  // 新建会话
  function newConversation() {
    messages.value = []
    streamContent.value = ''
    currentConversationId.value = null
    error.value = null
  }

  // 清空消息
  function clearMessages() {
    messages.value = []
    streamContent.value = ''
    error.value = null
    currentConversationId.value = null
  }

  // 删除会话
  function deleteConversation(id) {
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (currentConversationId.value === id) {
      clearMessages()
    }
  }

  // 切换模型
  function setModel(model) {
    currentModel.value = model
  }

  // 切换提供商
  function setProvider(provider) {
    currentProvider.value = provider
  }

  return {
    // State
    messages,
    isLoading,
    isStreaming,
    streamContent,
    currentModel,
    currentProvider,
    error,
    conversations,
    currentConversationId,

    // Getters
    hasMessages,
    lastMessage,
    isAssistantTyping,

    // Actions
    sendMessage,
    loadConversation,
    newConversation,
    clearMessages,
    deleteConversation,
    setModel,
    setProvider
  }
})