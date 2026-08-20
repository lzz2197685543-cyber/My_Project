/**
 * 验证工具
 */

/**
 * 验证是否为有效的 URL
 * @param {string} url - URL 字符串
 * @returns {boolean}
 */
export function isValidUrl(url) {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * 验证是否为 Base64 图片
 * @param {string} str - 字符串
 * @returns {boolean}
 */
export function isBase64Image(str) {
  if (!str) return false
  return /^data:image\/(png|jpeg|jpg|gif|webp|bmp);base64,/.test(str)
}

/**
 * 验证是否为图片文件扩展名
 * @param {string} filename - 文件名
 * @returns {boolean}
 */
export function isImageFile(filename) {
  if (!filename) return false
  const extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff']
  const ext = filename.toLowerCase().slice(filename.lastIndexOf('.'))
  return extensions.includes(ext)
}

/**
 * 验证文件大小
 * @param {number} size - 文件大小 (bytes)
 * @param {number} maxSize - 最大大小 (bytes)
 * @returns {boolean}
 */
export function isValidFileSize(size, maxSize = 20 * 1024 * 1024) {
  return size <= maxSize
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @param {number} decimals - 小数位数
 * @returns {string}
 */
export function formatFileSize(bytes, decimals = 1) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * 验证提示词长度
 * @param {string} prompt - 提示词
 * @param {number} maxLength - 最大长度
 * @returns {boolean}
 */
export function isValidPrompt(prompt, maxLength = 2000) {
  if (!prompt) return false
  return prompt.trim().length <= maxLength
}

/**
 * 验证数量
 * @param {number} count - 数量
 * @param {number} min - 最小值
 * @param {number} max - 最大值
 * @returns {boolean}
 */
export function isValidCount(count, min = 1, max = 10) {
  return count >= min && count <= max
}

/**
 * 验证 API Key 格式
 * @param {string} key - API Key
 * @param {string} provider - 提供商
 * @returns {boolean}
 */
export function isValidApiKey(key, provider = 'yi') {
  if (!key) return false
  // 简单验证：至少 10 个字符
  if (key.length < 10) return false
  // 只包含合法字符
  return /^[a-zA-Z0-9\-_]+$/.test(key)
}

/**
 * 验证电子邮件格式
 * @param {string} email - 邮箱
 * @returns {boolean}
 */
export function isValidEmail(email) {
  if (!email) return false
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}