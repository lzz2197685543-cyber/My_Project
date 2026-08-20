<template>
  <div class="chat-input">
    <div class="input-wrapper">
      <!-- 输入框 -->
      <el-input
        ref="inputRef"
        v-model="inputContent"
        type="textarea"
        :rows="2"
        :disabled="disabled"
        placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
        @keydown.enter.prevent="handleKeyDown"
        @input="onInput"
        resize="none"
        class="input-area"
      />

      <!-- 底部工具栏 -->
      <div class="input-toolbar">
        <div class="toolbar-left">
          <el-button size="small" text @click="clearInput" title="清空">
            <el-icon><Delete /></el-icon>
          </el-button>
          <span class="char-count">{{ inputContent.length }}/{{ maxLength }}</span>
        </div>
        <div class="toolbar-right">
          <el-button
            type="primary"
            :disabled="!inputContent.trim() || disabled"
            :loading="loading"
            @click="sendMessage"
          >
            <el-icon><Promotion /></el-icon>
            {{ loading ? '发送中...' : '发送' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, nextTick } from 'vue'
import { Delete, Promotion } from '@element-plus/icons-vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  maxLength: {
    type: Number,
    default: 4000
  }
})

const emit = defineEmits(['send', 'input'])

const inputRef = ref(null)
const inputContent = ref('')

// 发送消息
const sendMessage = () => {
  const content = inputContent.value.trim()
  if (!content || props.disabled) return

  emit('send', content)
  inputContent.value = ''
  focusInput()
}

// 键盘事件
const handleKeyDown = (event) => {
  if (event.shiftKey) {
    // Shift+Enter 换行
    return
  }
  // Enter 发送
  event.preventDefault()
  sendMessage()
}

// 输入事件
const onInput = () => {
  emit('input', inputContent.value)
  // 自动调整高度
  const textarea = inputRef.value?.$el?.querySelector('textarea')
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }
}

// 清空输入
const clearInput = () => {
  inputContent.value = ''
  focusInput()
}

// 聚焦输入
const focusInput = () => {
  nextTick(() => {
    inputRef.value?.$el?.querySelector('textarea')?.focus()
  })
}

// 设置输入内容
const setContent = (content) => {
  inputContent.value = content
}

// 暴露方法
defineExpose({
  focusInput,
  setContent,
  clearInput
})
</script>
<style scoped>
.chat-input {
  padding: 16px 20px;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
  transition: background 0.3s, border-color 0.3s;
}

.input-wrapper {
  max-width: 900px;
  margin: 0 auto;
}

.input-area :deep(.el-textarea__inner) {
  border-radius: 12px 12px 0 0;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  min-height: 60px;
  max-height: 120px;
  background: var(--bg-color);
  border-color: var(--border-color);
  transition: border-color 0.2s;
}

.input-area :deep(.el-textarea__inner:focus) {
  border-color: var(--primary-color);
}

.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-color);
  border-radius: 0 0 12px 12px;
  border: 1px solid var(--border-color);
  border-top: none;
  transition: border-color 0.2s;
}

.input-area :deep(.el-textarea__inner:focus) ~ .input-toolbar {
  border-color: var(--primary-color);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.char-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 暗色主题 */
.dark .input-area :deep(.el-textarea__inner) {
  background: var(--bg-card);
}

.dark .input-toolbar {
  background: var(--bg-card);
}

/* 响应式 */
@media (max-width: 768px) {
  .chat-input {
    padding: 12px;
  }

  .input-area :deep(.el-textarea__inner) {
    min-height: 48px;
    font-size: 15px;
  }

  .input-toolbar {
    padding: 6px 10px;
  }

  .toolbar-left .el-button {
    padding: 4px;
  }
}
</style>
