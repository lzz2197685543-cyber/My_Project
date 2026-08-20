<template>
  <div class="control-panel">
    <!-- 面板头部 -->
    <div class="panel-header">
      <h3>🎨 图片生成</h3>
      <el-tag size="small" type="info">{{ providerLabel }}</el-tag>
    </div>
    <!-- 参考图片上传 (图生图/融合时显示) -->
    <div v-if="showUpload" class="upload-section">
      <div class="section-title">
        <span>📸 参考图片</span>
        <span v-if="maxUpload > 1" class="badge">最多 {{ maxUpload }} 张</span>
      </div>
      <slot name="upload" />
    </div>
    <!-- 提示词 -->
    <div class="prompt-section">
      <div class="section-title">
        <span>📝 提示词</span>
        <div class="prompt-actions">
          <el-button size="small" text type="primary" @click="onOptimize" :loading="optimizing">
            <el-icon><MagicStick /></el-icon> 优化
          </el-button>
          <el-button size="small" text type="primary" @click="showTemplate = true">
            <el-icon><Files /></el-icon> 模板
          </el-button>
        </div>
      </div>
      <el-input
        v-model="promptValue"
        type="textarea"
        :rows="4"
        placeholder="描述你想要生成的图片..."
        maxlength="2000"
        show-word-limit
        resize="none"
        class="prompt-input"
      />

      <!-- 快捷标签 -->
      <div class="quick-tags">
        <el-tag
          v-for="tag in quickTags"
          :key="tag"
          size="small"
          class="quick-tag"
          @click="appendTag(tag)"
        >
          {{ tag }}
        </el-tag>
      </div>
    </div>
    <!-- 参数设置 -->
    <div class="params-section">
      <div class="section-title">🎯 参数设置</div>
      <el-form label-width="80px" size="small">
        <!-- 提供商 -->
        <el-form-item label="提供商">
          <el-select v-model="providerValue" @change="onProviderChange">
            <el-option label="API易" value="yi" />
            <el-option label="百炼" value="bailian" />
          </el-select>
        </el-form-item>
        <!-- 模型 -->
        <el-form-item label="模型">
          <el-select v-model="modelValue" placeholder="选择模型" filterable>
            <el-option
              v-for="model in availableModels"
              :key="model.id"
              :label="model.display_name || model.id"
              :value="model.id"
            />
          </el-select>
        </el-form-item>
        <!-- 图片尺寸 -->
        <el-form-item label="图片尺寸">
          <el-select v-model="sizeValue" style="width: 100%">
            <el-option label="1K · 标准·高效" value="1K" />
            <el-option label="2K · 高清" value="2K" />
            <el-option label="4K · 超清" value="4K" />
          </el-select>
        </el-form-item>
        <!-- 宽高比 -->
        <el-form-item label="宽高比">
          <el-select v-model="aspectValue" filterable>
            <el-option label="1:1 (正方形)" value="1:1" />
            <el-option label="16:9 (横屏)" value="16:9" />
            <el-option label="9:16 (竖屏)" value="9:16" />
            <el-option label="3:2" value="3:2" />
            <el-option label="2:3" value="2:3" />
            <el-option label="4:3" value="4:3" />
            <el-option label="3:4" value="3:4" />
            <el-option label="21:9 (宽屏)" value="21:9" />
          </el-select>
        </el-form-item>
        <!-- 数量 -->
        <el-form-item v-if="showCount" label="数量">
          <el-input-number v-model="countValue" :min="1" :max="10" />
        </el-form-item>
        <!-- 优化开关 -->
        <el-form-item label="优化">
          <el-switch v-model="optimizeValue" active-text="开启" inactive-text="关闭" />
        </el-form-item>
        <!-- 智能改写 (百炼) -->
        <el-form-item v-if="providerValue === 'bailian'" label="智能改写">
          <el-switch v-model="promptExtendValue" active-text="开启" inactive-text="关闭" />
        </el-form-item>
      </el-form>
    </div>
    <!-- 生成按钮 -->
<!-- 生成按钮 - 去掉 loading，只显示文字状态 -->
<el-button
  class="generate-btn"
  type="primary"
  size="large"
  :disabled="generating || !prompt.trim()"
  @click="onGenerate"
>
  <el-icon><Picture /></el-icon>
  {{ generating ? '生成中...' : '🚀 开始生成' }}
</el-button>
    <!-- 生成记录 -->
    <div v-if="showHistory" class="history-section">
      <div class="section-title">
        <span>📊 生成记录</span>
        <el-button size="small" text @click="onClearHistory">清空</el-button>
      </div>
      <div class="history-list">
        <div
          v-for="item in historyList"
          :key="item.id"
          class="history-item"
          @click="onLoadHistory(item)"
        >
          <el-image :src="item.thumbnail || item.images?.[0]?.url" fit="cover" class="history-thumb" />
          <div class="history-info">
            <span class="history-prompt">{{ truncateText(item.prompt, 25) }}</span>
            <span class="history-time">{{ formatTime(item.timestamp) }}</span>
          </div>
        </div>
        <div v-if="historyList.length === 0" class="history-empty">
          暂无生成记录
        </div>
      </div>
    </div>
    <!-- 模板弹窗 -->
    <el-dialog v-model="showTemplate" title="📋 提示词模板" width="600px">
      <div class="template-grid">
        <div
          v-for="template in promptTemplates"
          :key="template.name"
          class="template-item"
          @click="applyTemplate(template)"
        >
          <div class="template-icon">{{ template.icon || '📝' }}</div>
          <span class="template-name">{{ template.name }}</span>
          <p class="template-desc">{{ template.description }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Files, Picture } from '@element-plus/icons-vue'
import { useModelsStore } from '@/stores/models'

const props = defineProps({
  provider: { type: String, default: 'yi' },
  model: { type: String, default: '' },
  prompt: { type: String, default: '' },
  imageSize: { type: String, default: '1K' },
  aspectRatio: { type: String, default: '1:1' },
  count: { type: Number, default: 1 },
  optimize: { type: Boolean, default: true },
  promptExtend: { type: Boolean, default: false },
  generating: { type: Boolean, default: false },
  optimizing: { type: Boolean, default: false },
  showUpload: { type: Boolean, default: false },
  showCount: { type: Boolean, default: true },
  showHistory: { type: Boolean, default: true },
  maxUpload: { type: Number, default: 1 },
  history: { type: Array, default: () => [] }
})

const emit = defineEmits([
  'update:provider', 'update:model', 'update:prompt',
  'update:imageSize', 'update:aspectRatio', 'update:count',
  'update:optimize', 'update:promptExtend',
  'generate', 'optimize', 'loadHistory', 'clearHistory'
])

const modelsStore = useModelsStore()
const showTemplate = ref(false)

// 本地状态
const providerValue = ref(props.provider)
const modelValue = ref(props.model)
const promptValue = ref(props.prompt)
const sizeValue = ref(props.imageSize)
const aspectValue = ref(props.aspectRatio)
const countValue = ref(props.count)
const optimizeValue = ref(props.optimize)
const promptExtendValue = ref(props.promptExtend)

// 计算属性
const providerLabel = computed(() => {
  return providerValue.value === 'yi' ? 'API易' : '百炼'
})

const availableModels = computed(() => {
  return modelsStore.getModelsByProvider(providerValue.value, 'image')
})

const historyList = computed(() => props.history)

// 快捷标签
const quickTags = ['写实风格', '卡通风格', '水彩画', '电影级布光', '高清', '唯美', '赛博朋克', '复古', '3D渲染', '极简']

// 提示词模板
const promptTemplates = [
  { name: '写实人物', icon: '👤', description: '真实感人物肖像，细节丰富', prompt: '写实风格人物肖像，高清细节，自然光线' },
  { name: '风景画', icon: '🏞️', description: '壮丽自然风景，色彩丰富', prompt: '壮丽的自然风景，丰富的色彩层次，细节精致' },
  { name: '动漫风格', icon: '🎨', description: '日系动漫风格，色彩明亮', prompt: '日系动漫风格，色彩明亮，线条流畅，可爱风格' },
  { name: '赛博朋克', icon: '🌃', description: '赛博朋克风格，霓虹灯效', prompt: '赛博朋克城市，霓虹灯光，未来科技感，冷色调' },
  { name: '水彩画', icon: '🖌️', description: '水彩画风格，柔和朦胧', prompt: '水彩画风格，色彩柔和，笔触自然，朦胧美感' },
  { name: '3D渲染', icon: '💎', description: '3D渲染风格，立体感强', prompt: '3D渲染风格，立体感强，光影细腻，质感真实' }
]

// 监听外部变化
watch(() => props.provider, (val) => { providerValue.value = val })
watch(() => props.model, (val) => { modelValue.value = val })
watch(() => props.prompt, (val) => { promptValue.value = val })

// 发送更新事件
watch(providerValue, (val) => { emit('update:provider', val) })
watch(modelValue, (val) => { emit('update:model', val) })
watch(promptValue, (val) => { emit('update:prompt', val) })
watch(sizeValue, (val) => { emit('update:imageSize', val) })
watch(aspectValue, (val) => { emit('update:aspectRatio', val) })
watch(countValue, (val) => { emit('update:count', val) })
watch(optimizeValue, (val) => { emit('update:optimize', val) })
watch(promptExtendValue, (val) => { emit('update:promptExtend', val) })

// 方法
const onProviderChange = () => {
  const models = availableModels.value
  if (models.length > 0) {
    modelValue.value = models[0].id
  }
}

const appendTag = (tag) => {
  const current = promptValue.value
  if (current) {
    promptValue.value = `${current}, ${tag}`
  } else {
    promptValue.value = tag
  }
}

const onGenerate = () => {
  if (!promptValue.value.trim()) {
    ElMessage.warning('请输入提示词')
    return
  }
  emit('generate', {
    prompt: promptValue.value,
    model: modelValue.value,
    provider: providerValue.value,
    imageSize: sizeValue.value,
    aspectRatio: aspectValue.value,
    count: countValue.value,
    optimize: optimizeValue.value,
    promptExtend: promptExtendValue.value
  })
}

const onOptimize = () => {
  if (!promptValue.value.trim()) {
    ElMessage.warning('请先输入提示词')
    return
  }
  emit('optimize', promptValue.value)
}

const applyTemplate = (template) => {
  promptValue.value = template.prompt
  showTemplate.value = false
  ElMessage.success(`已应用模板: ${template.name}`)
}

const onLoadHistory = (item) => {
  promptValue.value = item.prompt
  emit('loadHistory', item)
}

const onClearHistory = () => {
  emit('clearHistory')
}

const truncateText = (text, maxLen) => {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}

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
</script>
<style scoped>
.control-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  overflow-y: auto;
  padding-right: 4px;
}

/* 面板头部 */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.panel-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

/* 区块标题 */
.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-regular);
  margin-bottom: 8px;
}

.badge {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-color);
  padding: 0 8px;
  border-radius: 10px;
}

.prompt-actions {
  display: flex;
  gap: 4px;
}

/* 上传区域 */
.upload-section {
  padding: 12px;
  background: var(--bg-color);
  border-radius: 8px;
}

/* 提示词 */
.prompt-section {
  flex-shrink: 0;
}

.prompt-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  min-height: 100px;
  background: var(--bg-color);
  border-color: var(--border-color);
}

.quick-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.quick-tag {
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.quick-tag:hover {
  background: var(--primary-color);
  color: white;
}

/* 参数设置 */
.params-section {
  flex-shrink: 0;
}

.params-section :deep(.el-form-item) {
  margin-bottom: 12px;
}

.params-section :deep(.el-form-item__label) {
  font-size: 13px;
  color: var(--text-regular);
}

/* 生成按钮 */
.generate-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  flex-shrink: 0;
  margin: 4px 0;
}

.generate-btn .el-icon {
  margin-right: 8px;
}

/* 历史记录 */
.history-section {
  flex: 1;
  min-height: 100px;
  max-height: 200px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  background: rgba(64, 158, 255, 0.06);
}

.history-thumb {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  flex-shrink: 0;
  object-fit: cover;
  background: var(--bg-color);
}

.history-info {
  flex: 1;
  min-width: 0;
}

.history-prompt {
  display: block;
  font-size: 13px;
  color: var(--text-regular);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  font-size: 11px;
  color: var(--text-secondary);
}

.history-empty {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px 0;
  font-size: 13px;
}

/* 模板弹窗 */
.template-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.template-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--bg-color);
}

.template-item:hover {
  border-color: var(--primary-color);
  background: rgba(64, 158, 255, 0.04);
  transform: translateY(-2px);
}

.template-icon {
  font-size: 28px;
  margin-bottom: 6px;
}

.template-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-regular);
}

.template-desc {
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
  margin: 4px 0 0 0;
}

/* 暗色主题 */
.dark .upload-section {
  background: var(--bg-card);
}

.dark .prompt-input :deep(.el-textarea__inner) {
  background: var(--bg-card);
}

.dark .template-item {
  background: var(--bg-card);
}

.dark .history-item:hover {
  background: rgba(64, 158, 255, 0.12);
}

/* 滚动条 */
.control-panel::-webkit-scrollbar {
  width: 4px;
}

.control-panel::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

/* 响应式 */
@media (max-width: 768px) {
  .template-grid {
    grid-template-columns: 1fr;
  }

  .history-section {
    max-height: 120px;
  }
}
</style>
