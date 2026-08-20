<template>
  <div class="multi-image-upload">
    <!-- 上传区域 -->
    <el-upload
      ref="uploadRef"
      :action="uploadUrl"
      :headers="uploadHeaders"
      :file-list="fileList"
      :limit="limit"
      :multiple="true"
      :auto-upload="true"
      :on-success="onSuccess"
      :on-error="onError"
      :on-exceed="onExceed"
      :before-upload="beforeUpload"
      :on-remove="onRemove"
      list-type="picture-card"
      class="upload-grid"
      :disabled="disabled || fileList.length >= limit"
    >
      <el-icon><Plus /></el-icon>
      <div class="upload-text">
        <span>上传图片</span>
        <span class="upload-hint">{{ fileList.length }}/{{ limit }}</span>
      </div>
    </el-upload>

    <!-- 已上传列表 -->
    <div v-if="fileList.length > 0" class="uploaded-list">
      <div
        v-for="(file, index) in fileList"
        :key="file.uid || index"
        class="uploaded-item"
        :class="{ active: selectedIndex === index }"
        @click="selectImage(index)"
      >
        <img :src="getFileUrl(file)" class="item-image" />
        <div class="item-overlay">
          <span class="item-index">{{ index + 1 }}</span>
          <el-icon class="item-delete" @click.stop="removeImage(index)">
            <Close />
          </el-icon>
        </div>
      </div>
    </div>

    <!-- 提示信息 -->
    <div class="upload-tips">
      <el-alert
        v-if="fileList.length < 2"
        title="至少需要 2 张图片进行融合"
        type="info"
        :closable="false"
        show-icon
      />
      <el-alert
        v-else-if="fileList.length >= 2"
        title="已准备好融合，输入提示词后点击生成"
        type="success"
        :closable="false"
        show-icon
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Close } from '@element-plus/icons-vue'

const props = defineProps({
  limit: {
    type: Number,
    default: 14
  },
  disabled: {
    type: Boolean,
    default: false
  },
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'change', 'remove'])

const uploadRef = ref(null)
const fileList = ref([])
const selectedIndex = ref(0)

const uploadUrl = '/api/v1/images/upload'
const uploadHeaders = computed(() => {
  const apiKey = localStorage.getItem('api_key')
  return apiKey ? { 'X-API-Key': apiKey } : {}
})

// ✅ 获取文件URL
const getFileUrl = (file) => {
  if (!file) return ''
  
  if (file.url) {
    let url = file.url
    if (!url.startsWith('http') && !url.startsWith('/')) {
      url = '/' + url
    }
    return url
  }
  
  if (file.path) {
    let path = file.path.replace(/\\/g, '/')
    if (path.includes('data/input/')) {
      const filename = path.split('data/input/').pop()
      return '/data/input/' + filename
    }
    if (path.includes('input/')) {
      const filename = path.split('input/').pop()
      return '/input/' + filename
    }
    if (!path.startsWith('/') && !path.startsWith('http')) {
      return '/' + path
    }
    return path
  }
  
  if (file.raw) {
    return URL.createObjectURL(file.raw)
  }
  
  return ''
}

const hasEnoughImages = computed(() => fileList.value.length >= 2)

// 上传前验证
const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt20M = file.size / 1024 / 1024 < 20

  if (!isImage) {
    ElMessage.error('只支持图片格式')
    return false
  }
  if (!isLt20M) {
    ElMessage.error('图片大小不能超过 20MB')
    return false
  }
  return true
}

// ✅ 上传成功 - 确保保存完整路径
const onSuccess = (response, file) => {
  console.log('📸 上传响应:', response)
  
  if (response) {
    // 从响应中提取数据
    let fileData = response
    if (response.data) {
      fileData = response.data
    }
    
    // ✅ 构建完整的文件对象
    const newFile = {
      uid: file.uid,
      name: fileData.filename || file.name,
      raw: file.raw,
      path: fileData.path || '',  // 完整路径
      content_type: fileData.content_type || file.type,
      size: fileData.size || file.size
    }
    
    // ✅ 构建 URL
    if (fileData.path) {
      let path = fileData.path.replace(/\\/g, '/')
      const filename = path.split('/').pop()
      newFile.url = '/data/input/' + filename
    } else if (fileData.url) {
      newFile.url = fileData.url
    }
    
    console.log('📸 处理后的文件:', newFile)
    
    fileList.value.push(newFile)
    emit('update:modelValue', fileList.value)
    emit('change', fileList.value)
    ElMessage.success(`上传成功: ${file.name}`)
  } else {
    ElMessage.error('上传失败: 没有返回数据')
  }
}

// 上传失败
const onError = (error) => {
  console.error('上传错误:', error)
  ElMessage.error(`上传失败: ${error.message || '未知错误'}`)
}

// 超出限制
const onExceed = () => {
  ElMessage.warning(`最多上传 ${props.limit} 张图片`)
}

// 移除图片
const onRemove = (file) => {
  const index = fileList.value.findIndex(f => f.uid === file.uid)
  if (index !== -1) {
    fileList.value.splice(index, 1)
    emit('update:modelValue', fileList.value)
    emit('remove', file, index)
    if (selectedIndex.value >= fileList.value.length) {
      selectedIndex.value = Math.max(0, fileList.value.length - 1)
    }
  }
}

const removeImage = (index) => {
  const file = fileList.value[index]
  if (file) {
    uploadRef.value?.handleRemove(file)
  }
}

const selectImage = (index) => {
  selectedIndex.value = index
}

const getImagePaths = () => {
  return fileList.value.map(f => {
    // 优先使用 path，否则使用 url
    if (f.path) {
      // 确保路径是绝对路径或完整路径
      let path = f.path.replace(/\\/g, '/')
      // 如果是相对路径，添加 data/input/ 前缀
      if (!path.includes('data/input/') && !path.includes(':\\')) {
        // 如果只是文件名，构建完整路径
        const filename = path.split('/').pop()
        return 'D:/sd14/AI_GEN/ai-gen-backend/data/input/' + filename
      }
      return path
    }
    return f.url || ''
  })
}

const clearAll = () => {
  fileList.value = []
  selectedIndex.value = 0
  emit('update:modelValue', fileList.value)
}

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.length > 0) {
    fileList.value = newVal
  }
}, { immediate: true, deep: true })

defineExpose({
  fileList,
  getImagePaths,
  clearAll,
  hasEnoughImages
})
</script>

<style scoped>
.multi-image-upload {
  width: 100%;
}

.upload-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
}

.upload-grid :deep(.el-upload) {
  width: 100%;
  height: 100px;
}

.upload-grid :deep(.el-upload--picture-card) {
  width: 100%;
  height: 100px;
  border-radius: 8px;
  border: 2px dashed var(--border-color);
  background: var(--bg-color);
  transition: all 0.3s;
}

.upload-grid :deep(.el-upload--picture-card:hover) {
  border-color: var(--primary-color);
  background: rgba(64, 158, 255, 0.04);
}

.upload-grid :deep(.el-upload-list--picture-card) {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
  width: 100%;
}

.upload-grid :deep(.el-upload-list__item) {
  width: 100%;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  margin: 0;
}

.upload-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.upload-hint {
  font-size: 11px;
  color: var(--text-placeholder);
}

.uploaded-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.uploaded-item {
  position: relative;
  width: 100%;
  padding-bottom: 100%;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  background: var(--bg-color);
}

.uploaded-item:hover {
  border-color: var(--primary-color);
  transform: scale(1.02);
}

.uploaded-item.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.3);
}

.item-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  background: linear-gradient(to bottom, rgba(0,0,0,0.3) 0%, transparent 50%);
}

.uploaded-item:hover .item-overlay {
  opacity: 1;
}

.item-index {
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 10px;
  padding: 0 6px;
  border-radius: 10px;
  line-height: 18px;
}

.item-delete {
  font-size: 14px;
  color: white;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  padding: 2px;
  cursor: pointer;
  transition: all 0.2s;
}

.item-delete:hover {
  background: var(--danger-color);
  transform: scale(1.1);
}

.upload-tips {
  margin-top: 12px;
}

.upload-tips :deep(.el-alert) {
  border-radius: 8px;
  padding: 8px 12px;
}

.dark .upload-grid :deep(.el-upload--picture-card) {
  background: var(--bg-card);
}

.dark .uploaded-item {
  background: var(--bg-card);
}

@media (max-width: 768px) {
  .upload-grid {
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 8px;
  }

  .upload-grid :deep(.el-upload--picture-card) {
    height: 80px;
  }

  .upload-grid :deep(.el-upload-list__item) {
    height: 80px;
  }

  .uploaded-list {
    grid-template-columns: repeat(auto-fill, minmax(64px, 1fr));
    gap: 8px;
  }
}
</style>