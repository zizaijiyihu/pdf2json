const API_BASE_URL = '/api'

/**
 * 发送聊天消息(流式)
 * @param {string} message - 用户消息
 * @param {Array} history - 聊天历史
 * @param {Function} onChunk - 流式数据回调
 * @param {AbortSignal} signal - 可选的 AbortSignal 用于取消请求
 * @param {string} conversationId - 可选的会话ID
 * @param {boolean} enableHistory - 是否启用历史记录
 * @returns {Promise<Object>} 最终结果
 */
export async function sendChatMessage(message, history = [], onChunk, signal = null, conversationId = null, enableHistory = true) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      history,
      conversation_id: conversationId,
      enable_history: enableHistory
    }),
    signal: signal
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to send message')
  }

  // 处理SSE流
  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  let fullContent = ''
  let toolCalls = []
  let finalHistory = null
  let finalConversationId = null
  let buffer = '' // 缓冲区，用于处理跨chunk的不完整行

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    // 将新数据追加到缓冲区
    buffer += decoder.decode(value, { stream: true })

    // 按行分割，但保留最后一个可能不完整的行
    const lines = buffer.split('\n')
    buffer = lines.pop() || '' // 最后一行可能不完整，保留到缓冲区

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.substring(6))

          if (data.type === 'content') {
            // 内容流式输出
            fullContent += data.data
            if (onChunk) {
              onChunk({ type: 'content', content: data.data })
            }
          } else if (data.type === 'tool_call') {
            // 工具调用通知
            toolCalls.push(data.data)
            if (onChunk) {
              onChunk({ type: 'tool_call', data: data.data })
            }
          } else if (data.type === 'done') {
            // 完成
            finalHistory = data.data.history
            toolCalls = data.data.tool_calls
            finalConversationId = data.data.conversation_id
          } else if (data.type === 'error') {
            throw new Error(data.data.error)
          }
        } catch (e) {
          console.error('Failed to parse SSE data:', e, 'Line:', line)
        }
      }
    }
  }

  // 处理缓冲区中剩余的最后一行
  if (buffer.startsWith('data: ')) {
    try {
      const data = JSON.parse(buffer.substring(6))
      if (data.type === 'done') {
        finalHistory = data.data.history
        toolCalls = data.data.tool_calls
        finalConversationId = data.data.conversation_id
      }
    } catch (e) {
      console.error('Failed to parse final SSE data:', e)
    }
  }

  return {
    response: fullContent,
    tool_calls: toolCalls,
    history: finalHistory,
    conversation_id: finalConversationId
  }
}

/**
 * 获取文档列表
 * @returns {Promise<Object>} 文档列表
 */
export async function getDocuments() {
  const url = `${API_BASE_URL}/documents`

  const response = await fetch(url)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to fetch documents')
  }

  return response.json()
}

/**
 * 上传并向量化PDF
 * @param {File} file - PDF文件
 * @param {number} isPublic - 是否公开 (0=私有, 1=公开)
 * @param {Function} onProgress - 进度回调
 * @returns {Promise<Object>} 上传结果
 */
export async function uploadPDF(file, isPublic = 0, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('is_public', isPublic.toString())

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    throw new Error('Upload failed')
  }

  // 处理SSE流
  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  let result = null
  let buffer = '' // 缓冲区，用于处理跨chunk的不完整行

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    // 将新数据追加到缓冲区
    buffer += decoder.decode(value, { stream: true })

    // 按行分割，但保留最后一个可能不完整的行
    const lines = buffer.split('\n')
    buffer = lines.pop() || '' // 最后一行可能不完整，保留到缓冲区

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.substring(6))
          // console.log('[DEBUG] SSE Data:', data)

          // 调用进度回调
          if (onProgress) {
            onProgress(data)
          }

          // 检查错误状态
          if (data.stage === 'error') {
            throw new Error(data.error || '上传处理失败')
          }

          // 保存最终结果
          if (data.stage === 'completed') {
            result = data
          }
        } catch (e) {
          console.error('Failed to parse SSE data:', e)
          // 如果是Error对象，向上抛出
          if (e instanceof Error && e.message !== 'Failed to parse SSE data:') {
            throw e
          }
        }
      }
    }
  }

  // 处理缓冲区中剩余的最后一行
  if (buffer.startsWith('data: ')) {
    try {
      const data = JSON.parse(buffer.substring(6))
      if (onProgress) {
        onProgress(data)
      }
      if (data.stage === 'completed') {
        result = data
      }
    } catch (e) {
      console.error('Failed to parse final SSE data:', e)
    }
  }

  return result
}

/**
 * 删除文档
 * @param {string} filename - 文件名
 * @returns {Promise<Object>} 删除结果
 */
export async function deleteDocument(filename) {
  const url = `${API_BASE_URL}/documents/${encodeURIComponent(filename)}`

  const response = await fetch(url, { method: 'DELETE' })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to delete document')
  }

  return response.json()
}

/**
 * 修改文档可见性
 * @param {string} filename - 文件名
 * @param {number} isPublic - 是否公开 (0=私有, 1=公开)
 * @returns {Promise<Object>} 更新结果
 */
export async function updateDocumentVisibility(filename, isPublic) {
  const url = `${API_BASE_URL}/documents/${encodeURIComponent(filename)}/visibility`

  const response = await fetch(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ is_public: isPublic })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to update document visibility')
  }

  return response.json()
}

/**
 * 上传并分析图片
 * @param {File} file - 图片文件
 * @param {string} prompt - 可选的分析提示词
 * @returns {Promise<Object>} 分析结果
 */
export async function analyzeImage(file, prompt = null) {
  const formData = new FormData()
  formData.append('file', file)
  if (prompt) {
    formData.append('prompt', prompt)
  }

  const response = await fetch(`${API_BASE_URL}/analyze-image`, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to analyze image')
  }

  return response.json()
}

/**
 * 检查服务健康状态
 * @returns {Promise<Object>} 健康状态
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`)
  return response.json()
}

/**
 * 获取用户指示列表
 * @returns {Promise<Object>} 指示列表
 */
export async function getInstructions() {
  const url = `${API_BASE_URL}/instructions`

  const response = await fetch(url)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to fetch instructions')
  }

  return response.json()
}

/**
 * 创建新指示
 * @param {string} content - 指示内容
 * @param {number} priority - 优先级
 * @returns {Promise<Object>} 创建结果
 */
export async function createInstruction(content, priority = 0) {
  const body = { content, priority }

  const response = await fetch(`${API_BASE_URL}/instructions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to create instruction')
  }

  return response.json()
}

/**
 * 更新指示
 * @param {number} id - 指示ID
 * @param {Object} data - 更新数据 {content, is_active, priority}
 * @returns {Promise<Object>} 更新结果
 */
export async function updateInstruction(id, data) {
  const body = { ...data }

  const response = await fetch(`${API_BASE_URL}/instructions/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to update instruction')
  }

  return response.json()
}

/**
 * 删除指示
 * @param {number} id - 指示ID
 * @returns {Promise<Object>} 删除结果
 */
export async function deleteInstruction(id) {
  const response = await fetch(`${API_BASE_URL}/instructions/${id}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({})
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to delete instruction')
  }

  return response.json()
}

/**
 * 获取语录列表
 * @param {number} page - 页码
 * @param {number} pageSize - 每页数量
 * @returns {Promise<Object>} 语录列表
 */
export async function getQuotes(page = 1, pageSize = 10) {
  const url = `${API_BASE_URL}/quotes?page=${page}&page_size=${pageSize}`
  const response = await fetch(url)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to fetch quotes')
  }

  return response.json()
}

/**
 * 创建新语录
 * @param {string} content - 语录内容
 * @param {number} isFixed - 是否固定 (0=否, 1=是)
 * @returns {Promise<Object>} 创建结果
 */
export async function createQuote(content, isFixed = 0) {
  const body = { content, is_fixed: isFixed }
  const response = await fetch(`${API_BASE_URL}/quotes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to create quote')
  }

  return response.json()
}

/**
 * 更新语录
 * @param {number} id - 语录ID
 * @param {string} content - 语录内容
 * @param {number} isFixed - 是否固定 (0=否, 1=是)
 * @returns {Promise<Object>} 更新结果
 */
export async function updateQuote(id, content, isFixed) {
  const body = { content, is_fixed: isFixed }
  const response = await fetch(`${API_BASE_URL}/quotes/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to update quote')
  }

  return response.json()
}

/**
 * 删除语录
 * @param {number} id - 语录ID
 * @returns {Promise<Object>} 删除结果
 */
export async function deleteQuote(id) {
  const response = await fetch(`${API_BASE_URL}/quotes/${id}`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to delete quote')
  }

  return response.json()
}

// ==================== 会话管理 API ====================

/**
 * 获取会话列表
 * @param {number} limit - 限制数量
 * @param {number} offset - 偏移量
 * @returns {Promise<Object>} 会话列表
 */
export async function getConversations(limit = 20, offset = 0) {
  const url = `${API_BASE_URL}/conversations?limit=${limit}&offset=${offset}`
  const response = await fetch(url)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to fetch conversations')
  }

  return response.json()
}

/**
 * 创建新会话
 * @param {string} title - 会话标题(可选)
 * @returns {Promise<Object>} 创建结果
 */
export async function createConversation(title = null) {
  const body = title ? { title } : {}
  const response = await fetch(`${API_BASE_URL}/conversations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to create conversation')
  }

  return response.json()
}

/**
 * 获取会话消息历史
 * @param {string} conversationId - 会话ID
 * @param {number} limit - 限制数量
 * @returns {Promise<Object>} 消息历史
 */
export async function getConversationMessages(conversationId, limit = 100) {
  const url = `${API_BASE_URL}/conversations/${conversationId}/messages?limit=${limit}`
  const response = await fetch(url)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to fetch conversation messages')
  }

  return response.json()
}

/**
 * 更新会话标题
 * @param {string} conversationId - 会话ID
 * @param {string} title - 新标题
 * @returns {Promise<Object>} 更新结果
 */
export async function updateConversationTitle(conversationId, title) {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to update conversation title')
  }

  return response.json()
}

/**
 * 删除会话
 * @param {string} conversationId - 会话ID
 * @returns {Promise<Object>} 删除结果
 */
export async function deleteConversation(conversationId) {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Failed to delete conversation')
  }

  return response.json()
}
