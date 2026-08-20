<template>
  <div class="image-upload" :class="{ dragging: isDragging }">
    <!-- 拖拽上传区域 -->
    <el-upload
      v-if="!hasImages"
      ref="uploadRef"
      :action="uploadUrl"
      :headers="uploadHeaders"
      :file-list="fileList"
      :limit="limit"
      :multiple="multiple"
      :auto-upload="true"
      :on-success="onSuccess"
      :on-error="onError"
      :on-exceed="onExceed"
      :before-upload="beforeUpload"
      drag
      class="upload-area"
      :disabled="disabled"
    >
      <el-icon class="upload-icon"><UploadFilled /></el-icon>
      <div class="upload-text">
        <span>点击上传{{ label }}</span>
        <span class="upload-hint">{{ hint }}</span>
      </div>
    </el-upload>

    <!-- 已上传预览 -->
    <div v-else class="uploaded-preview">
      <div
        v-for="(file, index) in fileList"
        :key="file.uid || index"
        class="preview-item"
        :class="{ active: selectedIndex === index }"
        @click="selectImage(index)"
      >
        <img
          :src="getFileUrl(file)"
          class="preview-image"
          @error="handleImageError(index)"
        />
        <el-icon class="remove-icon" @click.stop="removeImage(index)">
          <Close />
        </el-icon>
        <span class="preview-index">{{ index + 1 }}</span>
      </div>

      <!-- 继续添加按钮 -->
      <div
        v-if="fileList.length < limit"
        class="preview-item add-more"
        @click="triggerUpload"
      >
        <el-icon><Plus /></el-icon>
        <span>添加</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Close, Plus } from '@element-plus/icons-vue'

const props = defineProps({
  label: {
    type: String,
    default: '参考图片'
  },
  hint: {
    type: String,
    default: '支持 JPG、PNG 格式，单图最大 20M'
  },
  limit: {
    type: Number,
    default: 1
  },
  multiple: {
    type: Boolean,
    default: false
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
const isDragging = ref(false)
const fileList = ref([])
const selectedIndex = ref(0)

const uploadUrl = '/api/v1/images/upload'
const uploadHeaders = computed(() => {
  const apiKey = localStorage.getItem('api_key')
  return apiKey ? { 'X-API-Key': apiKey } : {}
})

const hasImages = computed(() => fileList.value.length > 0)

// ✅ 获取文件URL
const getFileUrl = (file) => {
  if (!file) {
    console.warn('⚠️ 文件对象为空')
    return ''
  }
  
  console.log('🔍 获取文件URL:', file)
  
  // 如果有 url，直接使用
  if (file.url) {
    let url = file.url
    if (!url.startsWith('http') && !url.startsWith('/')) {
      url = '/' + url
    }
    return url
  }
  
  // 如果有 path
  if (file.path) {
    let path = file.path.replace(/\\/g, '/')
    
    // 如果是 data/input 路径
    if (path.includes('data/input/')) {
      const filename = path.split('data/input/').pop()
      return '/data/input/' + filename
    }
    
    // 如果是 input 路径
    if (path.includes('input/')) {
      const filename = path.split('input/').pop()
      return '/input/' + filename
    }
    
    // 其他情况
    if (!path.startsWith('/') && !path.startsWith('http')) {
      return '/' + path
    }
    return path
  }
  
  // 如果有预览 URL（本地上传）
  if (file.preview) {
    return file.preview
  }
  
  // 最后尝试使用 URL.createObjectURL
  if (file.raw) {
    return URL.createObjectURL(file.raw)
  }
  
  return ''
}

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

// ✅ 上传成功 - 正确处理返回数据
const onSuccess = (response, file) => {
  console.log('📸 上传响应 - 完整:', JSON.stringify(response, null, 2))
  
  // 检查 response 的结构
  // 可能的格式: 
  // 1. 直接是 data: {filename, path, ...}
  // 2. 包含 code, data, message
  
  let fileData = response
  if (response && response.data) {
    fileData = response.data
  }
  
  console.log('📸 文件数据:', fileData)
  
  if (fileData) {
    // 构建完整的图片信息
    const newFile = {
      uid: file.uid,
      name: fileData.filename || file.name,
      raw: file.raw,
      path: fileData.path || '',
      content_type: fileData.content_type || file.type,
      size: fileData.size || file.size
    }
    
    // ✅ 构建可访问的 URL
    if (fileData.path) {
      let path = fileData.path.replace(/\\/g, '/')
      // 提取文件名
      const filename = path.split('/').pop()
      // 构建访问 URL
      newFile.url = '/data/input/' + filename
      console.log('📸 构建的 URL:', newFile.url)
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

// 选择图片
const selectImage = (index) => {
  selectedIndex.value = index
}

// 删除图片
const removeImage = (index) => {
  const removed = fileList.value[index]
  fileList.value.splice(index, 1)
  emit('update:modelValue', fileList.value)
  emit('remove', removed, index)

  if (selectedIndex.value >= fileList.value.length) {
    selectedIndex.value = Math.max(0, fileList.value.length - 1)
  }
}

// 触发上传
const triggerUpload = () => {
  uploadRef.value?.$el?.querySelector('input')?.click()
}

// 图片加载错误处理
const handleImageError = (index) => {
  console.warn(`图片 ${index + 1} 加载失败`)
}

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  if (newVal && newVal.length > 0) {
    fileList.value = newVal
  }
}, { immediate: true, deep: true })

// 暴露方法
defineExpose({
  fileList,
  clearFiles: () => {
    fileList.value = []
    selectedIndex.value = 0
  },
  getFiles: () => fileList.value
})
</script>

<style scoped>
.image-upload {
  width: 100%;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  padding: 32px 20px;
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  transition: all 0.3s;
  background: var(--bg-color);
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: var(--primary-color);
  background: rgba(64, 158, 255, 0.04);
}

.dragging .upload-area :deep(.el-upload-dragger) {
  border-color: var(--primary-color);
  background: rgba(64, 158, 255, 0.08);
}

.upload-icon {
  font-size: 40px;
  color: var(--primary-color);
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 12px;
  color: var(--text-regular);
}

.upload-hint {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 已上传预览 */
.uploaded-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px;
  background: var(--bg-color);
  border-radius: 12px;
  min-height: 80px;
}

.preview-item {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  flex-shrink: 0;
  background: var(--bg-color);
}

.preview-item:hover {
  border-color: var(--primary-color);
}

.preview-item.active {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.3);
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-icon {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.preview-item:hover .remove-icon {
  opacity: 1;
}

.preview-index {
  position: absolute;
  bottom: 2px;
  left: 2px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 10px;
  padding: 0 6px;
  border-radius: 10px;
}

.add-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-color);
  border: 2px dashed var(--border-color);
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.add-more:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.add-more .el-icon {
  font-size: 24px;
}

/* 暗色主题 */
.dark .upload-area :deep(.el-upload-dragger) {
  background: var(--bg-card);
}

.dark .uploaded-preview {
  background: var(--bg-card);
}

.dark .add-more {
  background: var(--bg-card);
}

/* 响应式 */
@media (max-width: 768px) {
  .preview-item {
    width: 60px;
    height: 60px;
  }

  .uploaded-preview {
    padding: 8px;
    gap: 8px;
  }
}
</style>