import React, { useRef, useEffect, useState } from 'react'
import useStore from '../store/useStore'
import { sendChatMessage, analyzeImage } from '../services/api'
import ChatMessage from './ChatMessage'
import QuoteDisplay from './QuoteDisplay'


function ChatView() {
  const messages = useStore(state => state.messages)
  const chatHistory = useStore(state => state.chatHistory)
  const isLoading = useStore(state => state.isLoading)
  const addMessage = useStore(state => state.addMessage)
  const updateLastMessage = useStore(state => state.updateLastMessage)
  const setMessages = useStore(state => state.setMessages)
  const setChatHistory = useStore(state => state.setChatHistory)
  const setIsLoading = useStore(state => state.setIsLoading)
  const toggleKnowledgeSidebar = useStore(state => state.toggleKnowledgeSidebar)
  const toggleInstructionSidebar = useStore(state => state.toggleInstructionSidebar)
  const toggleReminderSidebar = useStore(state => state.toggleReminderSidebar)
  const fetchReminders = useStore(state => state.fetchReminders)
  const clearClosedReminders = useStore(state => state.clearClosedReminders)
  const resetAnalysisQueue = useStore(state => state.resetAnalysisQueue)

  // 轮播状态
  const currentCarouselQuestion = useStore(state => state.currentCarouselQuestion)

  const currentConversationId = useStore(state => state.currentConversationId)
  const setCurrentConversationId = useStore(state => state.setCurrentConversationId)
  const addConversation = useStore(state => state.addConversation)

  const [inputValue, setInputValue] = useState('')
  const [greetingVisible, setGreetingVisible] = useState(true)
  const [uploadedImages, setUploadedImages] = useState([])
  const [analyzingImage, setAnalyzingImage] = useState(null)
  const [isRefreshingReminders, setIsRefreshingReminders] = useState(false)

  const messageContainerRef = useRef(null)
  const inputRef = useRef(null)
  const abortControllerRef = useRef(null)

  const hasMessages = messages.length > 0

  // 自动滚动到底部
  useEffect(() => {
    if (messageContainerRef.current) {
      messageContainerRef.current.scrollTop = messageContainerRef.current.scrollHeight
    }
  }, [messages])

  // 生成缩略图
  const generateThumbnail = (file) => {
    return new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = (e) => resolve(e.target.result)
      reader.readAsDataURL(file)
    })
  }

  // 处理图片上传和分析
  const handleImageUpload = async (file) => {
    const imageId = Date.now() + '-' + Math.random().toString(36).substr(2, 9)

    try {
      // 1. 生成缩略图
      const thumbnail = await generateThumbnail(file)

      // 2. 添加到列表
      const newImage = {
        id: imageId,
        file: file,
        thumbnail: thumbnail,
        status: 'uploading',
        imageUrl: null,
        analysis: null
      }
      setUploadedImages(prev => [...prev, newImage])
      setAnalyzingImage(imageId)

      // 3. 上传并分析
      const result = await analyzeImage(file)

      if (result.success) {
        // 4. 更新图片信息
        setUploadedImages(prev => prev.map(img =>
          img.id === imageId
            ? {
              ...img,
              status: 'done',
              imageUrl: result.image_url,
              analysis: result.analysis
            }
            : img
        ))
      } else {
        throw new Error(result.error)
      }
    } catch (error) {
      console.error('Image analysis failed:', error)
      setUploadedImages(prev => prev.map(img =>
        img.id === imageId ? { ...img, status: 'error' } : img
      ))
    } finally {
      setTimeout(() => {
        setAnalyzingImage(null)
      }, 500)
    }
  }

  // 处理粘贴事件
  const handlePaste = async (e) => {
    const items = e.clipboardData?.items
    if (!items) return

    for (let item of items) {
      if (item.type.startsWith('image/')) {
        e.preventDefault()
        const file = item.getAsFile()
        if (file) {
          await handleImageUpload(file)
        }
        break
      }
    }
  }

  // 删除图片
  const removeImage = (imageId) => {
    setUploadedImages(prev => prev.filter(img => img.id !== imageId))
  }

  // 处理刷新提醒（清空四层缓存）
  const handleRefreshReminders = async () => {
    setIsRefreshingReminders(true)
    try {
      // 第一层：清空 localStorage 中的关闭记录
      clearClosedReminders()
      console.log('✓ 已清空关闭提醒记录 (localStorage)')

      // 第二层：清空 IndexedDB 中的大模型分析结果缓存
      const { clearAllCache } = await import('../services/indexedDBCache')
      await clearAllCache()
      console.log('✓ 已清空大模型分析缓存 (IndexedDB)')

      // 第三层：重置 AI 分析队列
      resetAnalysisQueue()
      console.log('✓ 已重置 AI 分析队列')

      // 第四层：重新从后端获取提醒列表
      await fetchReminders()
      console.log('✓ 已重新获取提醒列表')

      console.log('✅ 提醒数据已完全刷新（四层缓存已清空）')
    } catch (error) {
      console.error('❌ 刷新提醒失败:', error)
    } finally {
      setIsRefreshingReminders(false)
    }
  }

  // 处理停止生成
  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      setIsLoading(false)
    }
  }

  // 处理发送消息
  const handleSendMessage = async () => {
    const text = inputValue.trim()
    if (!text || isLoading) return

    // 构建完整消息（文本 + 图片分析）
    let fullMessage = text

    if (uploadedImages.length > 0) {
      const imageAnalyses = uploadedImages
        .filter(img => img.status === 'done' && img.analysis)
        .map(img => img.analysis)
        .join('\n\n')

      if (imageAnalyses) {
        // 添加结构化的上下文标识
        fullMessage = `【我上传了图片，已解析为以下结果】\n\n${imageAnalyses}\n\n【基于上述图片内容，我的问题是】\n\n${text}`
      }
    }

    // 添加用户消息（显示文本+缩略图）
    addMessage({
      role: 'user',
      content: text,
      images: uploadedImages
        .filter(img => img.status === 'done')
        .map(img => ({
          url: img.imageUrl,
          thumbnail: img.thumbnail
        }))
    })

    setInputValue('')
    setUploadedImages([]) // 清空图片列表

    // 隐藏问候语
    if (greetingVisible) {
      setTimeout(() => setGreetingVisible(false), 800)
    }

    // 发送到后端（流式）
    setIsLoading(true)

    // 创建一个空的assistant消息用于流式更新
    addMessage({ role: 'assistant', content: '' })

    // 创建 AbortController
    abortControllerRef.current = new AbortController()

    let streamingContent = ''

    try {
      const response = await sendChatMessage(
        fullMessage,
        chatHistory,
        (chunk) => {
          if (chunk.type === 'content') {
            // 流式更新内容
            streamingContent += chunk.content
            updateLastMessage(streamingContent)
          } else if (chunk.type === 'tool_call') {
            console.log('Tool call:', chunk.data)
          }
        },
        abortControllerRef.current.signal,
        currentConversationId, // 传入当前会话ID
        true // 启用历史记录
      )

      // 更新历史
      if (response.history) {
        setChatHistory(response.history)
      }

      // 如果是新会话，更新会话ID并添加到列表
      if (response.conversation_id && response.conversation_id !== currentConversationId) {
        setCurrentConversationId(response.conversation_id)
        // 添加到会话列表（简单起见，这里只添加基本信息，标题暂时用第一条消息）
        addConversation({
          conversation_id: response.conversation_id,
          title: text.substring(0, 30) + (text.length > 30 ? '...' : ''),
          updated_at: new Date().toISOString()
        })
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        // 用户主动中断，不显示错误
        console.log('Generation stopped by user')
      } else {
        console.error('Failed to send message:', error)
        // 更新最后一条消息为错误信息
        updateLastMessage('抱歉，发送消息失败，请稍后重试。')
      }
    } finally {
      abortControllerRef.current = null
      setIsLoading(false)
    }
  }

  // 处理键盘事件
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // 自动调整输入框高度
  const adjustInputHeight = (e) => {
    const target = e.target
    target.style.height = 'auto'
    target.style.height = Math.min(target.scrollHeight, 100) + 'px'
  }

  return (
    <div className={`${hasMessages ? 'flex flex-col h-[calc(100vh-2rem)]' : 'flex flex-col'} w-[750px]`}>
      {/* 消息容器 - 有消息时固定高度并可滚动 */}
      {hasMessages && (
        <div
          ref={messageContainerRef}
          className="flex-1 overflow-y-auto scrollbar-thin bg-white transition-all duration-1200 ease-out pt-[5vh]"
        >
          <div className="w-full max-w-[760px] mx-auto p-4">
            {messages.map((msg, index) => (
              <ChatMessage key={index} message={msg} />
            ))}
            {isLoading && (
              <div className="mb-4 max-w-[80%] bg-white p-3 rounded-lg rounded-tr-none border border-gray-100">
                <div className="flex items-center gap-2 text-gray-500">
                  <i className="fa fa-circle-o-notch fa-spin" aria-hidden="true"></i>
                  <span>思考中...</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 输入容器 - 固定在底部 */}
      <div
        className={`${hasMessages ? 'flex-shrink-0' : 'flex-grow'} flex flex-col bg-white transition-all duration-1200 ease-out`}
      >
        <div className="w-full flex flex-col">
          <div className="w-full flex flex-col items-center" style={{ flexGrow: 5 }}>
            {/* 语录展示 */}
            {!hasMessages && (
              <QuoteDisplay visible={greetingVisible} />
            )}
          </div>
        </div>

        <div className={`${!hasMessages ? 'z-10 bg-white pb-8' : 'pb-[5vh]'} flex flex-col items-center w-full flex-shrink-0`}>
          {/* 输入区 */}
          <div className="w-full max-w-[760px] p-4 mx-auto">
            {/* 输入容器 - flex布局，图片在左侧 */}
            <div className="flex items-start gap-3 relative border border-gray-300 rounded-2xl p-4 shadow-md bg-white focus-within:ring-2 focus-within:ring-primary/50 focus-within:border-primary transition-all">
              {/* 图片预览区 - 左侧 */}
              {uploadedImages.length > 0 && (
                <div className="flex gap-2 flex-shrink-0">
                  {uploadedImages.map(img => (
                    <div
                      key={img.id}
                      className="relative w-16 h-16 rounded-lg overflow-hidden border border-gray-200"
                    >
                      {/* 缩略图 */}
                      <img
                        src={img.thumbnail}
                        alt="preview"
                        className="w-full h-full object-cover"
                      />

                      {/* 状态覆盖层 - 仅上传中显示 */}
                      {img.status === 'uploading' && analyzingImage === img.id && (
                        <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                          <i className="fa fa-spinner fa-spin text-white text-lg"></i>
                        </div>
                      )}

                      {/* 错误状态覆盖层 */}
                      {img.status === 'error' && (
                        <div className="absolute inset-0 bg-red-500/80 flex items-center justify-center">
                          <i className="fa fa-exclamation text-white text-sm"></i>
                        </div>
                      )}

                      {/* 删除按钮 - 始终显示 */}
                      <button
                        onClick={() => removeImage(img.id)}
                        className="absolute top-0.5 left-0.5 w-5 h-5 bg-black/70 rounded-full flex items-center justify-center hover:bg-black/90 transition-colors"
                        title="删除"
                      >
                        <i className="fa fa-times text-white text-xs"></i>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* 输入框容器 - 占据剩余空间 */}
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => {
                    setInputValue(e.target.value)
                    adjustInputHeight(e)
                  }}
                  onKeyDown={handleKeyDown}
                  onPaste={handlePaste}
                  className="w-full pr-20 outline-none resize-none bg-transparent transition-all duration-300"
                  placeholder={currentCarouselQuestion || '发消息或粘贴图片，输入/选择技能'}
                  rows="2"
                  disabled={isLoading}
                  style={{ minHeight: '48px' }}
                />

                {/* 工具按钮组 - 绝对定位在右下角 */}
                <div className="absolute right-0 bottom-0 flex space-x-2">
                  <button
                    onClick={toggleInstructionSidebar}
                    className="w-8 h-8 flex items-center justify-center text-gray-600 hover:text-primary hover:bg-gray-100 rounded-full transition-colors"
                    title="我的指示"
                  >
                    <i className="fa fa-lightbulb-o" aria-hidden="true"></i>
                  </button>
                  <button
                    onClick={toggleReminderSidebar}
                    className="w-8 h-8 flex items-center justify-center text-gray-600 hover:text-primary hover:bg-gray-100 rounded-full transition-colors"
                    title="我的提醒"
                  >
                    <i className="fa fa-bell-o" aria-hidden="true"></i>
                  </button>
                  <button
                    onClick={toggleKnowledgeSidebar}
                    className="w-8 h-8 flex items-center justify-center text-gray-600 hover:text-primary hover:bg-gray-100 rounded-full transition-colors"
                    title="知识库"
                  >
                    <i className="fa fa-book" aria-hidden="true"></i>
                  </button>
                  <button
                    onClick={isLoading ? handleStopGeneration : handleSendMessage}
                    disabled={!isLoading && !inputValue.trim()}
                    className="w-8 h-8 flex items-center justify-center text-white bg-primary hover:bg-primary/90 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title={isLoading ? "停止生成" : "发送"}
                  >
                    <i className={isLoading ? "fa fa-stop" : "fa fa-paper-plane-o"} aria-hidden="true"></i>
                  </button>
                </div>
              </div>
            </div>

            {/* 技能组件 */}
            <div className="mt-4 flex items-center gap-3 justify-center transition-all duration-1200 ease-out">
              {/* 演讲力教练 */}
              <button
                onClick={() => {
                  // TODO: 添加链接逻辑
                  console.log('演讲力教练')
                }}
                className="group flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 rounded-xl hover:border-primary hover:shadow-md transition-all duration-300 hover:scale-105"
              >
                <i className="fa fa-microphone text-gray-500 group-hover:text-primary group-hover:scale-110 transition-all" aria-hidden="true"></i>
                <span className="text-sm font-medium text-gray-700 group-hover:text-primary transition-colors">演讲力教练</span>
              </button>

              {/* 晋升辅导 */}
              <button
                onClick={() => {
                  // TODO: 添加链接逻辑
                  console.log('晋升辅导')
                }}
                className="group flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 rounded-xl hover:border-primary hover:shadow-md transition-all duration-300 hover:scale-105"
              >
                <i className="fa fa-line-chart text-gray-500 group-hover:text-primary group-hover:scale-110 transition-all" aria-hidden="true"></i>
                <span className="text-sm font-medium text-gray-700 group-hover:text-primary transition-colors">晋升辅导</span>
              </button>

              {/* 敬请期待 */}
              <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl cursor-not-allowed opacity-60">
                <i className="fa fa-lock text-gray-400" aria-hidden="true"></i>
                <span className="text-sm font-medium text-gray-400">敬请期待</span>
              </div>

              {/* 刷新提醒按钮 - 低调的小图标 */}
              <button
                onClick={handleRefreshReminders}
                disabled={isRefreshingReminders}
                className="group relative flex items-center justify-center w-10 h-10 text-gray-400 hover:text-primary hover:bg-gray-50 rounded-full transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <i className={`fa fa-refresh ${isRefreshingReminders ? 'fa-spin' : ''}`} aria-hidden="true"></i>

                {/* Hover 提示文字 */}
                <span className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-gray-800 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                  刷新提醒消息
                </span>
              </button>
            </div>

          </div>

        </div>

      </div>
    </div>
  )
}

export default ChatView
