/**
 * IndexedDB 缓存工具
 * 用于缓存提醒的 AI 分析结果
 */

const DB_NAME = 'km-agent-cache'
const DB_VERSION = 1
const STORE_NAME = 'reminder-analysis'
const CACHE_DURATION = 5 * 60 * 60 * 1000 // 5小时(毫秒)

/**
 * 初始化或获取 IndexedDB 连接
 */
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onerror = () => {
      console.error('IndexedDB 打开失败:', request.error)
      reject(request.error)
    }

    request.onsuccess = () => {
      resolve(request.result)
    }

    request.onupgradeneeded = (event) => {
      const db = event.target.result

      // 创建对象存储(如果不存在)
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const objectStore = db.createObjectStore(STORE_NAME, { keyPath: 'id' })
        // 创建索引用于查询过期时间
        objectStore.createIndex('expiresAt', 'expiresAt', { unique: false })
      }
    }
  })
}

/**
 * 获取缓存的提醒分析结果
 * @param {string} reminderId - 提醒ID
 * @returns {Promise<string|null>} - 分析结果文本,如果不存在或已过期返回 null
 */
export async function getReminderAnalysis(reminderId) {
  try {
    const db = await openDB()
    const transaction = db.transaction([STORE_NAME], 'readonly')
    const objectStore = transaction.objectStore(STORE_NAME)
    const request = objectStore.get(reminderId)

    return new Promise((resolve, reject) => {
      request.onsuccess = () => {
        const result = request.result

        // 检查是否存在
        if (!result) {
          resolve(null)
          return
        }

        // 检查是否过期
        const now = Date.now()
        if (result.expiresAt <= now) {
          // 已过期,删除并返回 null
          deleteReminderAnalysis(reminderId)
          resolve(null)
          return
        }

        resolve(result.analysis)
      }

      request.onerror = () => {
        console.error('读取 IndexedDB 失败:', request.error)
        reject(request.error)
      }
    })
  } catch (error) {
    console.error('获取提醒分析失败:', error)
    return null
  }
}

/**
 * 保存提醒分析结果到缓存
 * @param {string} reminderId - 提醒ID
 * @param {string} analysis - AI 分析结果
 * @returns {Promise<void>}
 */
export async function setReminderAnalysis(reminderId, analysis) {
  try {
    const db = await openDB()
    const transaction = db.transaction([STORE_NAME], 'readwrite')
    const objectStore = transaction.objectStore(STORE_NAME)

    const now = Date.now()
    const data = {
      id: reminderId,
      analysis: analysis,
      createdAt: now,
      expiresAt: now + CACHE_DURATION
    }

    const request = objectStore.put(data)

    return new Promise((resolve, reject) => {
      request.onsuccess = () => {
        resolve()
      }

      request.onerror = () => {
        console.error('写入 IndexedDB 失败:', request.error)
        reject(request.error)
      }
    })
  } catch (error) {
    console.error('保存提醒分析失败:', error)
  }
}

/**
 * 删除指定提醒的分析结果
 * @param {string} reminderId - 提醒ID
 * @returns {Promise<void>}
 */
export async function deleteReminderAnalysis(reminderId) {
  try {
    const db = await openDB()
    const transaction = db.transaction([STORE_NAME], 'readwrite')
    const objectStore = transaction.objectStore(STORE_NAME)
    const request = objectStore.delete(reminderId)

    return new Promise((resolve, reject) => {
      request.onsuccess = () => {
        resolve()
      }

      request.onerror = () => {
        console.error('删除 IndexedDB 记录失败:', request.error)
        reject(request.error)
      }
    })
  } catch (error) {
    console.error('删除提醒分析失败:', error)
  }
}

/**
 * 清理所有过期的缓存
 * @returns {Promise<number>} - 删除的记录数
 */
export async function cleanExpiredCache() {
  try {
    const db = await openDB()
    const transaction = db.transaction([STORE_NAME], 'readwrite')
    const objectStore = transaction.objectStore(STORE_NAME)
    const index = objectStore.index('expiresAt')

    const now = Date.now()
    const range = IDBKeyRange.upperBound(now)
    const request = index.openCursor(range)

    let deletedCount = 0

    return new Promise((resolve, reject) => {
      request.onsuccess = (event) => {
        const cursor = event.target.result
        if (cursor) {
          cursor.delete()
          deletedCount++
          cursor.continue()
        } else {
          console.log(`清理了 ${deletedCount} 条过期缓存`)
          resolve(deletedCount)
        }
      }

      request.onerror = () => {
        console.error('清理过期缓存失败:', request.error)
        reject(request.error)
      }
    })
  } catch (error) {
    console.error('清理过期缓存失败:', error)
    return 0
  }
}

/**
 * 清空所有缓存
 * @returns {Promise<void>}
 */
export async function clearAllCache() {
  try {
    const db = await openDB()
    const transaction = db.transaction([STORE_NAME], 'readwrite')
    const objectStore = transaction.objectStore(STORE_NAME)
    const request = objectStore.clear()

    return new Promise((resolve, reject) => {
      request.onsuccess = () => {
        console.log('已清空所有缓存')
        resolve()
      }

      request.onerror = () => {
        console.error('清空缓存失败:', request.error)
        reject(request.error)
      }
    })
  } catch (error) {
    console.error('清空缓存失败:', error)
  }
}
