<template>
  <div class="model-selector">
    <!-- 提供商选择 -->
    <el-select
      :model-value="provider"
      @update:model-value="onProviderChange"
      size="default"
      class="provider-select"
      placeholder="选择提供商"
    >
      <el-option
        v-for="p in providers"
        :key="p.id"
        :label="p.name"
        :value="p.id"
      />
    </el-select>
    <!-- 模型选择 -->
    <el-select
      :model-value="model"
      @update:model-value="onModelChange"
      size="default"
      class="model-select"
      placeholder="选择模型"
      filterable
    >
      <el-option-group
        v-if="chatModels.length > 0"
        label="💬 聊天模型"
      >
        <el-option
          v-for="m in chatModels"
          :key="m.id"
          :label="m.display_name || m.id"
          :value="m.id"
        />
      </el-option-group>
      <el-option-group
        v-if="imageModels.length > 0"
        label="🎨 图片模型"
      >
        <el-option
          v-for="m in imageModels"
          :key="m.id"
          :label="m.display_name || m.id"
          :value="m.id"
        />
      </el-option-group>
    </el-select>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { useModelsStore } from '@/stores/models'
import { PROVIDER_LIST } from '@/constants/providers'

const props = defineProps({
  provider: {
    type: String,
    required: true
  },
  model: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'chat', // 'chat' | 'image'
    validator: (val) => ['chat', 'image'].includes(val)
  }
})

const emit = defineEmits(['update:provider', 'update:model'])

const modelsStore = useModelsStore()
const providers = PROVIDER_LIST

const models = computed(() => {
  return modelsStore.getModelsByProvider(props.provider)
})

const chatModels = computed(() => {
  return models.value?.chat || []
})

const imageModels = computed(() => {
  return models.value?.image || []
})

const onProviderChange = (val) => {
  emit('update:provider', val)
  // 自动选择第一个模型
  const modelList = props.type === 'chat' ? chatModels.value : imageModels.value
  if (modelList.length > 0) {
    emit('update:model', modelList[0].id)
  }
}

const onModelChange = (val) => {
  emit('update:model', val)
}
</script>
<style scoped>
.model-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.provider-select {
  width: 110px;
}

.model-select {
  width: 200px;
}

/* 暗色主题 */
.dark .provider-select :deep(.el-input__wrapper) {
  background: var(--bg-card);
}

.dark .model-select :deep(.el-input__wrapper) {
  background: var(--bg-card);
}

/* 响应式 */
@media (max-width: 768px) {
  .model-selector {
    flex-direction: column;
    width: 100%;
  }

  .provider-select,
  .model-select {
    width: 100%;
  }
}
</style>
