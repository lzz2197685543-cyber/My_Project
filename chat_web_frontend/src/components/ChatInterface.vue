<template>
  <div class="chat-container">
    <div class="chat-header">
      <h1>DeepSeek 聊天助手</h1>
      <div class="model-selector">
        <label>模型：</label>
        <select v-model="selectedModel" @change="handleModelChange">
          <option v-for="model in models" :key="model" :value="model">
            {{ model }}
          </option>
        </select>
      </div>
    </div>
    <div class="messages-container" ref="messagesContainer">
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="message-content">
          <div class="message-avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-text">
            <div class="message-role">{{ msg.role === 'user' ? '我' : 'DeepSeek' }}</div>
            <div class="message-body">{{ msg.content }}</div>
          </div>
        </div>
      </div>
      <div v-if="isLoading" class="message assistant">
        <div class="message-content">
          <div class="message-avatar">🤖</div>
          <div class="message-text">
            <div class="message-role">DeepSeek</div>
            <div class="message-body typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="input-container">
      <textarea
        v-model="currentMessage"
        @keydown.ctrl.enter="sendMessage"
        placeholder="输入消息... (Ctrl+Enter 发送)"
        rows="3"
        :disabled="isLoading"
      ></textarea>
      <button @click="sendMessage" :disabled="!currentMessage.trim() || isLoading">
        {{ isLoading ? '发送中...' : '发送' }}
      </button>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { chatApi } from '../api/chat'

const messages = ref([])
const currentMessage = ref('')
const isLoading = ref(false)
const selectedModel = ref('deepseek-v4-flash')
const models = ref(['deepseek-v4-flash', 'deepseek-chat', 'deepseek-coder'])
const messagesContainer = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isLoading.value) return

  const userMessage = currentMessage.value.trim()
  messages.value.push({
    role: 'user',
    content: userMessage
  })
  currentMessage.value = ''
  await scrollToBottom()

  isLoading.value = true

  try {
    const response = await chatApi.sendMessage(
      userMessage,
      selectedModel.value
    )

    if (response.success) {
      messages.value.push({
        role: 'assistant',
        content: response.content
      })
    } else {
      messages.value.push({
        role: 'assistant',
        content: `❌ 错误：${response.error || '未知错误'}`
      })
    }
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: `❌ 请求失败：${error.message || '网络错误'}`
    })
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

const handleModelChange = () => {
  // 可以添加模型切换逻辑
  console.log('切换到模型:', selectedModel.value)
}

// 加载模型列表
const loadModels = async () => {
  try {
    const response = await chatApi.getModels()
    if (response.models) {
      models.value = response.models
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

onMounted(() => {
  loadModels()
  // 添加欢迎消息
  messages.value.push({
    role: 'assistant',
    content: '你好！我是 DeepSeek 助手，有什么可以帮你的吗？'
  })
})
</script>
<style scoped>
.chat-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: white;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.chat-header h1 {
  margin: 0;
  font-size: 24px;
  color: #2c3e50;
}

.model-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.model-selector select {
  padding: 8px 12px;
  border: 1px solid #dce1e8;
  border-radius: 6px;
  background: white;
  font-size: 14px;
  cursor: pointer;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: white;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.message {
  margin-bottom: 20px;
}

.message-content {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  background: #eef2f7;
}

.message.user .message-avatar {
  background: #4a90d9;
}

.message.assistant .message-avatar {
  background: #34c759;
}

.message-text {
  flex: 1;
}

.message-role {
  font-size: 12px;
  font-weight: 600;
  color: #7f8c8d;
  margin-bottom: 4px;
}

.message-body {
  padding: 12px 16px;
  background: #f0f2f5;
  border-radius: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message.user .message-body {
  background: #4a90d9;
  color: white;
}

.message.assistant .message-body {
  background: #f0f2f5;
  color: #2c3e50;
}

.typing {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing span {
  width: 8px;
  height: 8px;
  background: #7f8c8d;
  border-radius: 50%;
  animation: typing 1.4s infinite both;
}

.typing span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.input-container {
  display: flex;
  gap: 12px;
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.input-container textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #dce1e8;
  border-radius: 8px;
  resize: vertical;
  font-family: inherit;
  font-size: 14px;
  min-height: 60px;
  transition: border-color 0.3s;
}

.input-container textarea:focus {
  outline: none;
  border-color: #4a90d9;
}

.input-container button {
  padding: 12px 24px;
  background: #4a90d9;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
  align-self: flex-end;
}

.input-container button:hover:not(:disabled) {
  background: #357abd;
  transform: translateY(-1px);
}

.input-container button:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}
</style>
