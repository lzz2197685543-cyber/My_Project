<template>
  <div
    class="chat-message"
    :class="[
      message.role,
      { streaming: message.streaming }
    ]"
  >
    <div class="message-avatar">
      <el-avatar :size="36" :icon="message.role === 'user' ? UserFilled : Service" />
    </div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-role">
          {{ message.role === 'user' ? '用户' : '助手' }}
        </span>
        <span class="message-time">{{ formatTime(message.timestamp) }}</span>
      </div>
      <div class="message-body" v-html="renderedContent" />

      <!-- 操作按钮 -->
      <div v-if="message.role === 'assistant' && message.content && !message.streaming" class="message-actions">
        <el-button size="small" text @click="copyContent">
          <el-icon><CopyDocument /></el-icon>
          复制
        </el-button>
        <el-button size="small" text @click="regenerate">
          <el-icon><Refresh /></el-icon>
          重新生成
        </el-button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UserFilled, Service, CopyDocument, Refresh } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const props = defineProps({
  message: {
    type: Object,
    required: true,
    validator: (val) => {
      return val.role && ['user', 'assistant', 'system'].includes(val.role)
    }
  }
})

const emit = defineEmits(['regenerate'])

// Markdown 渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function(str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }
    return ''
  }
})

// 渲染内容
const renderedContent = computed(() => {
  if (!props.message.content) return ''
  return md.render(props.message.content)
})

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 复制内容
const copyContent = () => {
  navigator.clipboard.writeText(props.message.content)
  ElMessage.success('已复制到剪贴板')
}

// 重新生成
const regenerate = () => {
  emit('regenerate')
}
</script>
<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  animation: fadeIn 0.3s ease-out;
}

.chat-message.user {
  flex-direction: row-reverse;
}

.chat-message.user .message-content {
  align-items: flex-end;
}

.chat-message.user .message-body {
  background: var(--primary-color);
  color: white;
  border-radius: 12px 4px 12px 12px;
}

.chat-message.assistant .message-body {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 4px 12px 12px 12px;
}

.message-avatar {
  flex-shrink: 0;
  padding-top: 4px;
}

.message-avatar :deep(.el-avatar) {
  background: var(--bg-color);
  border: 1px solid var(--border-color);
}

.chat-message.user .message-avatar :deep(.el-avatar) {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.message-content {
  display: flex;
  flex-direction: column;
  max-width: 75%;
  min-width: 60px;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.chat-message.user .message-header {
  flex-direction: row-reverse;
}

.message-role {
  font-weight: 600;
  color: var(--text-regular);
}

.message-time {
  font-size: 11px;
}

.message-body {
  padding: 12px 16px;
  line-height: 1.7;
  word-break: break-word;
  overflow-wrap: break-word;
}

.message-body :deep(p) {
  margin: 0 0 8px 0;
}

.message-body :deep(p:last-child) {
  margin-bottom: 0;
}

.message-body :deep(pre) {
  background: var(--bg-color);
  padding: 12px 16px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-body :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

.message-body :deep(ul),
.message-body :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}

.message-body :deep(blockquote) {
  border-left: 3px solid var(--primary-color);
  padding-left: 12px;
  margin: 8px 0;
  color: var(--text-secondary);
}

.message-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}

.message-body :deep(th),
.message-body :deep(td) {
  border: 1px solid var(--border-color);
  padding: 6px 12px;
  text-align: left;
}

.message-body :deep(th) {
  background: var(--bg-color);
}

.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-content:hover .message-actions {
  opacity: 1;
}

.message-actions .el-button {
  font-size: 12px;
  color: var(--text-secondary);
}

.message-actions .el-button:hover {
  color: var(--primary-color);
}

/* 流式输出光标 */
.streaming .message-body::after {
  content: '▊';
  display: inline-block;
  animation: blink 1s step-end infinite;
  color: var(--primary-color);
  margin-left: 2px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 暗色主题 */
.dark .message-body :deep(pre) {
  background: #2d2d2d;
}

.dark .message-body :deep(th) {
  background: #2d2d2d;
}

.dark .message-body :deep(blockquote) {
  color: var(--text-secondary);
}

.dark .chat-message.assistant .message-body {
  background: var(--bg-card);
}

/* 响应式 */
@media (max-width: 768px) {
  .chat-message {
    padding: 12px 16px;
    gap: 8px;
  }

  .message-content {
    max-width: 85%;
  }

  .message-body {
    padding: 10px 12px;
    font-size: 14px;
  }
}
</style>
