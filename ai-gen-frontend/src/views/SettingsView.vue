<template>
  <div class="settings-view">
    <h2 class="page-title">⚙️ 设置</h2>
    <div class="settings-container">
      <!-- API Key 配置 -->
      <el-card class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>🔑 API Key 配置</span>
            <el-tag size="small" type="info">必填</el-tag>
          </div>
        </template>
        <ApiKeyInput
          label="API易 (Yi)"
          v-model="settingsStore.yiApiKey"
          :testing="testingYi"
          :status="yiStatus"
          :status-text="yiStatusText"
          placeholder="请输入 API易 API Key"
          @test="testYiConnection"
        />

        <div style="margin-top: 16px">
          <ApiKeyInput
            label="API易 Access Token"
            v-model="settingsStore.yiAccessToken"
            :testing="testingYiToken"
            :status="yiTokenStatus"
            :status-text="yiTokenStatusText"
            placeholder="请输入 API易 Access Token"
            @test="testYiToken"
          />
        </div>
        <div style="margin-top: 16px">
          <ApiKeyInput
            label="百炼 (Bailian)"
            v-model="settingsStore.bailianApiKey"
            :testing="testingBailian"
            :status="bailianStatus"
            :status-text="bailianStatusText"
            placeholder="请输入百炼 API Key"
            @test="testBailianConnection"
          />
        </div>
      </el-card>
      <!-- 默认设置 -->
      <el-card class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>🎯 默认设置</span>
          </div>
        </template>
        <el-form label-width="120px" size="default">
          <el-form-item label="默认提供商">
            <el-select
              v-model="settingsStore.defaultProvider"
              @change="onProviderChange"
              style="width: 200px"
            >
              <el-option label="API易" value="yi" />
              <el-option label="百炼" value="bailian" />
            </el-select>
          </el-form-item>
          <el-form-item label="默认聊天模型">
            <el-select
              v-model="settingsStore.defaultChatModel"
              style="width: 250px"
              filterable
            >
              <el-option
                v-for="model in chatModels"
                :key="model.id"
                :label="model.display_name || model.id"
                :value="model.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="默认图片模型">
            <el-select
              v-model="settingsStore.defaultImageModel"
              style="width: 250px"
              filterable
            >
              <el-option
                v-for="model in imageModels"
                :key="model.id"
                :label="model.display_name || model.id"
                :value="model.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>
      <!-- 外观设置 -->
      <el-card class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>🎨 外观设置</span>
          </div>
        </template>
        <ThemeSwitcher />
      </el-card>
      <!-- 保存按钮 -->
      <div class="settings-actions">
        <el-button type="primary" size="large" @click="saveSettings">
          <el-icon><Check /></el-icon>
          保存设置
        </el-button>
        <el-button size="large" @click="resetSettings">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Refresh } from '@element-plus/icons-vue'
import { useSettingsStore } from '@/stores/settings'
import { useModelsStore } from '@/stores/models'
import ApiKeyInput from '@/components/settings/ApiKeyInput.vue'
import ThemeSwitcher from '@/components/settings/ThemeSwitcher.vue'

const settingsStore = useSettingsStore()
const modelsStore = useModelsStore()

// ===== 状态 =====
const testingYi = ref(false)
const testingYiToken = ref(false)
const testingBailian = ref(false)

// ===== 计算属性 =====
const chatModels = computed(() => {
  const allModels = modelsStore.allModels
  return allModels.filter(m => m.type === 'chat')
})

const imageModels = computed(() => {
  const allModels = modelsStore.allModels
  return allModels.filter(m => m.type === 'image')
})

// API Key 状态
const yiStatus = computed(() => {
  if (settingsStore.yiApiKey) return 'configured'
  return 'unknown'
})

const yiStatusText = computed(() => {
  if (settingsStore.yiApiKey) return '已配置'
  return '未配置'
})

const yiTokenStatus = computed(() => {
  if (settingsStore.yiAccessToken) return 'configured'
  return 'unknown'
})

const yiTokenStatusText = computed(() => {
  if (settingsStore.yiAccessToken) return '已配置'
  return '未配置'
})

const bailianStatus = computed(() => {
  if (settingsStore.bailianApiKey) return 'configured'
  return 'unknown'
})

const bailianStatusText = computed(() => {
  if (settingsStore.bailianApiKey) return '已配置'
  return '未配置'
})

// ===== 方法 =====

// 测试 API易 连接
const testYiConnection = async (key) => {
  testingYi.value = true
  try {
    // 模拟测试 - 实际应该调用 API
    await new Promise(resolve => setTimeout(resolve, 1000))
    if (key && key.length > 10) {
      testingYi.value = false
      return true
    } else {
      testingYi.value = false
      return 'API Key 格式不正确'
    }
  } catch (error) {
    testingYi.value = false
    return error.message
  }
}

// 测试 API易 Token
const testYiToken = async (token) => {
  testingYiToken.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    if (token && token.length > 10) {
      testingYiToken.value = false
      return true
    } else {
      testingYiToken.value = false
      return 'Token 格式不正确'
    }
  } catch (error) {
    testingYiToken.value = false
    return error.message
  }
}

// 测试百炼连接
const testBailianConnection = async (key) => {
  testingBailian.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    if (key && key.length > 10) {
      testingBailian.value = false
      return true
    } else {
      testingBailian.value = false
      return 'API Key 格式不正确'
    }
  } catch (error) {
    testingBailian.value = false
    return error.message
  }
}

// 提供商变化时更新 API Key
const onProviderChange = (val) => {
  if (val === 'yi') {
    settingsStore.apiKey = settingsStore.yiApiKey
  } else {
    settingsStore.apiKey = settingsStore.bailianApiKey
  }
  localStorage.setItem('api_key', settingsStore.apiKey)
}

// 保存设置
const saveSettings = () => {
  // 更新通用 API Key
  if (settingsStore.defaultProvider === 'yi') {
    settingsStore.apiKey = settingsStore.yiApiKey
  } else {
    settingsStore.apiKey = settingsStore.bailianApiKey
  }
  localStorage.setItem('api_key', settingsStore.apiKey)

  ElMessage.success('设置已保存')
}

// 重置设置
const resetSettings = () => {
  ElMessageBox.confirm('确定要重置所有设置吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    // 重置为默认值
    settingsStore.setTheme('light')
    settingsStore.setYiApiKey('')
    settingsStore.setYiAccessToken('')
    settingsStore.setBailianApiKey('')
    settingsStore.setDefaultProvider('yi')
    settingsStore.setDefaultChatModel('deepseek-chat')
    settingsStore.setDefaultImageModel('gemini-3.1-flash-lite-image')
    settingsStore.setApiKey('')
    ElMessage.success('已重置所有设置')
  }).catch(() => {})
}

// ===== 生命周期 =====
onMounted(() => {
  modelsStore.loadModels()
})
</script>
<style scoped>
.settings-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 8px 0;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 24px 0;
}

.settings-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-card {
  border-radius: 12px !important;
  border: 1px solid var(--border-color) !important;
}

.settings-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-regular);
}

.settings-card :deep(.el-card__body) {
  padding: 20px;
}

.settings-card :deep(.el-form-item) {
  margin-bottom: 18px;
}

.settings-card :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

.settings-actions {
  display: flex;
  gap: 12px;
  padding: 8px 0 16px 0;
}

.settings-actions .el-button {
  min-width: 120px;
}

.settings-actions .el-button .el-icon {
  margin-right: 6px;
}

/* 暗色主题 */
.dark .settings-card {
  border-color: var(--border-color) !important;
}

.dark .settings-card :deep(.el-card__header) {
  border-bottom-color: var(--border-color);
}

/* 响应式 */
@media (max-width: 768px) {
  .settings-view {
    padding: 4px 0;
  }

  .page-title {
    font-size: 18px;
    margin-bottom: 16px;
  }

  .settings-card :deep(.el-card__body) {
    padding: 16px;
  }

  .settings-actions {
    flex-direction: column;
  }

  .settings-actions .el-button {
    width: 100%;
  }

  .settings-card :deep(.el-form-item) {
    flex-direction: column;
    align-items: flex-start;
  }

  .settings-card :deep(.el-form-item__label) {
    width: auto !important;
    padding-bottom: 4px;
  }

  .settings-card :deep(.el-form-item__content) {
    width: 100%;
    margin-left: 0 !important;
  }

  .settings-card :deep(.el-select) {
    width: 100% !important;
  }
}
</style>
