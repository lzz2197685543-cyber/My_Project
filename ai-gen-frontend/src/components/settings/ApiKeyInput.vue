<template>
  <div class="api-key-input">
    <div class="key-header">
      <span class="key-label">{{ label }}</span>
      <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
    </div>
    <div class="key-input-wrapper">
      <el-input
        :model-value="value"
        @update:model-value="onInput"
        :type="showKey ? 'text' : 'password'"
        :placeholder="placeholder"
        size="default"
        class="key-input"
        clearable
      >
        <template #append>
          <el-button
            :icon="showKey ? View : Hide"
            @click="toggleVisibility"
            text
          />
        </template>
      </el-input>
      <el-button
        size="default"
        :loading="testing"
        @click="onTest"
        class="test-btn"
      >
        {{ testing ? '测试中...' : '测试连接' }}
      </el-button>
    </div>
    <div v-if="testResult" class="test-result" :class="testResult.type">
      <el-icon>
        <CircleCheck v-if="testResult.type === 'success'" />
        <CircleClose v-else />
      </el-icon>
      <span>{{ testResult.message }}</span>
    </div>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
import { View, Hide, CircleCheck, CircleClose } from '@element-plus/icons-vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请输入 API Key'
  },
  testing: {
    type: Boolean,
    default: false
  },
  status: {
    type: String,
    default: 'unknown' // 'unknown' | 'configured' | 'valid' | 'invalid'
  },
  statusText: {
    type: String,
    default: '未配置'
  }
})

const emit = defineEmits(['update:value', 'test'])

const showKey = ref(false)
const testResult = ref(null)

// 计算状态类型
const statusType = computed(() => {
  const map = {
    unknown: 'info',
    configured: 'warning',
    valid: 'success',
    invalid: 'danger'
  }
  return map[props.status] || 'info'
})

// 切换可见性
const toggleVisibility = () => {
  showKey.value = !showKey.value
}

// 输入事件
const onInput = (val) => {
  emit('update:value', val)
  // 清除测试结果
  testResult.value = null
}

// 测试连接
const onTest = async () => {
  if (!props.value) {
    testResult.value = {
      type: 'error',
      message: '请先输入 API Key'
    }
    return
  }

  try {
    const result = await emit('test', props.value)
    if (result === true) {
      testResult.value = {
        type: 'success',
        message: '✅ 连接成功！'
      }
    } else {
      testResult.value = {
        type: 'error',
        message: `❌ 连接失败: ${result || '未知错误'}`
      }
    }
  } catch (error) {
    testResult.value = {
      type: 'error',
      message: `❌ 连接失败: ${error.message || '未知错误'}`
    }
  }
}

// 清除测试结果
const clearTestResult = () => {
  testResult.value = null
}

defineExpose({
  clearTestResult
})
</script>
<style scoped>
.api-key-input {
  padding: 16px;
  background: var(--bg-color);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  transition: all 0.3s;
}

.api-key-input:hover {
  border-color: var(--primary-color);
}

.key-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.key-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-regular);
}

.key-input-wrapper {
  display: flex;
  gap: 10px;
}

.key-input {
  flex: 1;
}

.key-input :deep(.el-input__wrapper) {
  border-radius: 6px 0 0 6px;
}

.key-input :deep(.el-input-group__append) {
  border-radius: 0 6px 6px 0;
}

.test-btn {
  flex-shrink: 0;
  border-radius: 6px;
}

.test-result {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  animation: fadeIn 0.3s ease-out;
}

.test-result.success {
  background: rgba(103, 194, 58, 0.1);
  color: var(--success-color);
}

.test-result.error {
  background: rgba(245, 108, 108, 0.1);
  color: var(--danger-color);
}

.test-result .el-icon {
  font-size: 18px;
}

/* 暗色主题 */
.dark .api-key-input {
  background: var(--bg-card);
}

.dark .test-result.success {
  background: rgba(103, 194, 58, 0.15);
}

.dark .test-result.error {
  background: rgba(245, 108, 108, 0.15);
}

/* 响应式 */
@media (max-width: 768px) {
  .api-key-input {
    padding: 12px;
  }

  .key-input-wrapper {
    flex-direction: column;
  }

  .test-btn {
    width: 100%;
  }
}
</style>
