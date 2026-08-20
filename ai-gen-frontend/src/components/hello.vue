<script setup>
// ... 其他代码

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

// ... 其他代码
</script>