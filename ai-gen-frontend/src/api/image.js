import client from './client'

export const imageApi = {
  /**
   * 文生图
   */
  textToImage(data) {
    return client.post('/api/v1/images/text-to-image', data)
  },

  /**
   * 图生图
   */
  imageToImage(data) {
    return client.post('/api/v1/images/image-to-image', data)
  },

  /**
   * 多图融合
   */
  fuse(data) {
    return client.post('/api/v1/images/fuse', data)
  },

  /**
   * 上传图片
   */
  upload(file) {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/api/v1/images/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}