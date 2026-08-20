<template>
  <div class="chat-view">
    <!-- 顶部工具栏 -->
    <div class="chat-header">
      <div class="header-left">
        <h2>💬 聊天</h2>
        <el-tag v-if="chatStore.isStreaming" size="small" type="warning">
          <el-icon class="is-loading"><Loading /></el-icon>
          生成中...
        </el-tag>
      </div>

      <div class="header-right">
        <ModelSelector
          :provider="chatStore.currentProvider"
          :model="chatStore.currentModel"
          type="chat"
          @update:provider="onProviderChange"
          @update:model="onModelChange"
        />

        <el-button
          size="small"
          plain
          @click="newConversation"
          :disabled="chatStore.isLoading"
        >
          <el-icon><Plus /></el-icon>
          新建对话
        </el-button>

        <el-button
          size="small"
          type="danger"
          plain
          @click="clearChat"
          :disabled="!chatStore.hasMessages || chatStore.isLoading"
        >
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="chat-body">
      <!-- 历史对话侧边栏 -->
      <div v-if="chatStore.conversations.length > 0" class="chat-sidebar">
        <div class="sidebar-title">📋 历史对话</div>
        <div
          v-for="conv in chatStore.conversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ active: conv.id === chatStore.currentConversationId }"
          @click="loadConversation(conv.id)"
        >
          <span class="conv-title">{{ conv.title || '新对话' }}</span>
          <span class="conv-time">{{ formatTime(conv.updatedAt) }}</span>
          <el-icon class="delete-conv" @click.stop="deleteConversation(conv.id)">
            <Close />
          </el-icon>
        </div>
      </div>

      <!-- 消息区域 + 输入框 -->
      <div class="chat-main">
        <!-- 消息列表 -->
        <div class="chat-messages" ref="messagesRef">
          <!-- 空状态 -->
          <div v-if="!chatStore.hasMessages" class="empty-state">
            <el-icon size="64"><ChatDotSquare /></el-icon>
            <h3>开始新的对话</h3>
            <p>在下方输入框输入消息，开始与 AI 对话</p>
            <div class="quick-prompts">
              <el-tag
                v-for="prompt in quickPrompts"
                :key="prompt"
                @click="quickSend(prompt)"
                class="quick-tag"
              >
                {{ prompt }}
              </el-tag>
            </div>
          </div>

          <!-- 消息列表 -->
          <div v-else class="message-list">
            <ChatMessage
              v-for="(msg, index) in chatStore.messages"
              :key="msg.id || index"
              :message="msg"
              @regenerate="regenerateMessage(index)"
            />
          </div>

          <!-- 加载指示器 -->
          <div v-if="chatStore.isLoading && !chatStore.isStreaming" class="loading-indicator">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>思考中...</span>
          </div>
        </div>

        <!-- 输入框 - 固定在底部 -->
        <div class="chat-input-wrapper">
          <ChatInput
            ref="chatInputRef"
            :disabled="chatStore.isLoading"
            :loading="chatStore.isLoading"
            @send="handleSend"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Loading, Close, ChatDotSquare } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { useModelsStore } from '@/stores/models'
import ModelSelector from '@/components/common/ModelSelector.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatInput from '@/components/chat/ChatInput.vue'

const chatStore = useChatStore()
const modelsStore = useModelsStore()
const messagesRef = ref(null)
const chatInputRef = ref(null)

// 快捷提示词
const quickPrompts = [
  '你好，介绍一下自己',
  '给我讲个笑话',
  '什么是人工智能？',
  '帮我写一首诗',
  '如何学习 Python？'
]

// ===== 方法 =====

// 发送消息
const handleSend = async (content) => {
  await chatStore.sendMessage(content)
  scrollToBottom()
}

// 快捷发送
const quickSend = (prompt) => {
  chatInputRef.value?.setContent(prompt)
  handleSend(prompt)
}

// 切换提供商
const onProviderChange = (val) => {
  chatStore.setProvider(val)
  const models = modelsStore.getModelsByProvider(val, 'chat')
  if (models.length > 0) {
    chatStore.setModel(models[0].id)
  }
}

// 切换模型
const onModelChange = (val) => {
  chatStore.setModel(val)
}

// 新建对话
const newConversation = () => {
  if (chatStore.hasMessages) {
    ElMessageBox.confirm('当前对话未保存，确定新建对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      chatStore.newConversation()
      ElMessage.success('已创建新对话')
    }).catch(() => {})
  } else {
    chatStore.newConversation()
  }
}

// 清空对话
const clearChat = () => {
  ElMessageBox.confirm('确定要清空所有对话吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    chatStore.clearMessages()
    ElMessage.success('已清空对话')
  }).catch(() => {})
}

// 加载历史对话
const loadConversation = (id) => {
  chatStore.loadConversation(id)
  scrollToBottom()
}

// 删除历史对话
const deleteConversation = (id) => {
  ElMessageBox.confirm('确定要删除此对话吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    chatStore.deleteConversation(id)
    ElMessage.success('已删除对话')
  }).catch(() => {})
}

// 重新生成消息
const regenerateMessage = (index) => {
  const messages = chatStore.messages
  let userIndex = -1
  for (let i = index - 1; i >= 0; i--) {
    if (messages[i].role === 'user') {
      userIndex = i
      break
    }
  }

  if (userIndex !== -1) {
    chatStore.messages = messages.slice(0, index)
    const userContent = messages[userIndex].content
    chatStore.sendMessage(userContent)
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      const container = messagesRef.value
      container.scrollTop = container.scrollHeight
    }
  })
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 监听消息变化滚动到底部
watch(() => chatStore.messages.length, scrollToBottom)
watch(() => chatStore.streamContent, scrollToBottom)

// 加载模型
onMounted(() => {
  modelsStore.loadModels()
})
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-color);
  border-radius: 12px;
  overflow: hidden;
}

/* 头部 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* 主体 */
.chat-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 历史对话侧边栏 */
.chat-sidebar {
  width: 220px;
  padding: 12px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 8px 4px 12px 4px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.conversation-item:hover {
  background: rgba(64, 158, 255, 0.06);
}

.conversation-item.active {
  background: rgba(64, 158, 255, 0.12);
}

.conv-title {
  flex: 1;
  font-size: 13px;
  color: var(--text-regular);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-time {
  font-size: 11px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.delete-conv {
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .delete-conv {
  opacity: 1;
}

.delete-conv:hover {
  color: var(--danger-color);
}

/* 聊天主区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  background: var(--bg-color);
}

.message-list {
  display: flex;
  flex-direction: column;
}

/* 加载指示器 */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  color: var(--text-secondary);
  font-size: 14px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
}

.empty-state .el-icon {
  color: var(--text-placeholder);
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 20px;
  color: var(--text-regular);
  margin: 0 0 8px 0;
}

.empty-state p {
  font-size: 14px;
  margin: 0 0 20px 0;
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-width: 500px;
  justify-content: center;
}

.quick-tag {
  cursor: pointer;
  transition: all 0.2s;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
}

.quick-tag:hover {
  background: var(--primary-color);
  color: white;
  transform: translateY(-2px);
}

/* 输入框容器 - 固定在底部 */
.chat-input-wrapper {
  flex-shrink: 0;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
}

/* 暗色主题 */
.dark .chat-sidebar {
  background: var(--bg-card);
}

.dark .conversation-item:hover {
  background: rgba(64, 158, 255, 0.12);
}

.dark .conversation-item.active {
  background: rgba(64, 158, 255, 0.2);
}

/* 响应式 */
@media (max-width: 768px) {
  .chat-header {
    padding: 12px 16px;
  }

  .header-left h2 {
    font-size: 16px;
  }

  .chat-messages {
    padding: 12px 16px;
  }

  .chat-sidebar {
    width: 180px;
    padding: 8px;
  }

  .conversation-item {
    padding: 8px 10px;
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .chat-sidebar {
    display: none;
  }

  .header-right {
    width: 100%;
    flex-wrap: wrap;
  }

  .header-right .model-selector {
    width: 100%;
  }
}
</style>