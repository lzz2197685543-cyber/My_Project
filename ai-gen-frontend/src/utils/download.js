/**
 * 文件下载工具
 */

/**
 * 下载图片
 * @param {string} url - 图片 URL
 * @param {string} filename - 文件名
 */
export function downloadImage(url, filename) {
  if (!url) return

  const link = document.createElement('a')
  link.href = url
  link.download = filename || `image_${Date.now()}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * 下载多个图片（批量）
 * @param {Array} images - 图片列表 [{ url, filename }]
 * @param {number} delay - 每个下载之间的延迟 (ms)
 */
export function downloadImages(images, delay = 200) {
  images.forEach((img, index) => {
    setTimeout(() => {
      downloadImage(img.url, img.filename)
    }, index * delay)
  })
}

/**
 * 下载文件（通用）
 * @param {string} url - 文件 URL
 * @param {string} filename - 文件名
 */
export function downloadFile(url, filename) {
  downloadImage(url, filename)
}

/**
 * 下载 Base64 图片
 * @param {string} base64 - Base64 数据
 * @param {string} filename - 文件名
 */
export function downloadBase64Image(base64, filename) {
  if (!base64) return

  const link = document.createElement('a')
  link.href = base64
  link.download = filename || `image_${Date.now()}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * 通过 fetch 下载远程图片
 * @param {string} url - 图片 URL
 * @param {string} filename - 文件名
 */
export async function fetchAndDownload(url, filename) {
  try {
    const response = await fetch(url)
    const blob = await response.blob()
    const blobUrl = URL.createObjectURL(blob)

    const link = document.createElement('a')
    link.href = blobUrl
    link.download = filename || `image_${Date.now()}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    // 释放 URL
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000)
  } catch (error) {
    console.error('下载失败:', error)
    throw error
  }
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 * @returns {Promise<boolean>}
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (error) {
    console.error('复制失败:', error)
    // 降级方案
    const textarea = document.createElement('textarea')
    textarea.value = text
    document.body.appendChild(textarea)
    textarea.select()
    try {
      document.execCommand('copy')
      document.body.removeChild(textarea)
      return true
    } catch (e) {
      document.body.removeChild(textarea)
      return false
    }
  }
}