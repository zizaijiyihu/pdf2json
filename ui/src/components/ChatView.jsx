import React, { useRef, useEffect, useState } from 'react'
import useStore from '../store/useStore'
import { sendChatMessage, analyzeImage } from '../services/api'
import ChatMessage from './ChatMessage'

function ChatView() {
  const messages = useStore(state => state.messages)
  const chatHistory = useStore(state => state.chatHistory)
  const isLoading = useStore(state => state.isLoading)
  const owner = useStore(state => state.owner)
  const addMessage = useStore(state => state.addMessage)
  const updateLastMessage = useStore(state => state.updateLastMessage)
  const setMessages = useStore(state => state.setMessages)
  const setChatHistory = useStore(state => state.setChatHistory)
  const setIsLoading = useStore(state => state.setIsLoading)
  const toggleKnowledgeSidebar = useStore(state => state.toggleKnowledgeSidebar)

  const [inputValue, setInputValue] = useState('')
  const [greetingVisible, setGreetingVisible] = useState(true)
  const [uploadedImages, setUploadedImages] = useState([])
  const [analyzingImage, setAnalyzingImage] = useState(null)
  const [analyzeProgress, setAnalyzeProgress] = useState(0)

  const messageContainerRef = useRef(null)
  const inputRef = useRef(null)

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
      setAnalyzeProgress(0)

      // 3. 上传并分析
      setAnalyzeProgress(20)
      const result = await analyzeImage(file, owner)
      setAnalyzeProgress(60)

      if (result.success) {
        setAnalyzeProgress(100)
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
        setAnalyzeProgress(0)
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

    let streamingContent = ''

    try {
      const response = await sendChatMessage(fullMessage, chatHistory, (chunk) => {
        if (chunk.type === 'content') {
          // 流式更新内容
          streamingContent += chunk.content
          updateLastMessage(streamingContent)
        } else if (chunk.type === 'tool_call') {
          console.log('Tool call:', chunk.data)
        }
      })

      // 更新历史
      if (response.history) {
        setChatHistory(response.history)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      // 更新最后一条消息为错误信息
      updateLastMessage('抱歉，发送消息失败，请稍后重试。')
    } finally {
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
    <div className="w-[800px] h-[calc(100vh-200px)] my-[100px] flex flex-col bg-white relative">
      {/* 消息容器 */}
      <div
        ref={messageContainerRef}
        className={`${hasMessages ? 'flex-1' : 'hidden'} overflow-y-auto scrollbar-thin bg-white w-full transition-all duration-1200 ease-out`}
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

      {/* 输入容器 */}
      <div
        className={`${hasMessages
          ? 'h-[100px] justify-center'
          : 'flex-1 items-center justify-center'
          } flex flex-col bg-white w-full transition-all duration-1200 ease-out`}
      >
        {/* 问候语 */}
        {!hasMessages && (
          <div
            className={`text-2xl text-gray-800 font-medium mb-8 transition-opacity duration-800 ${greetingVisible ? 'opacity-100' : 'opacity-0'
              }`}
          >
            创造知识   共享知识
          </div>
        )}

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
                      <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center">
                        <i className="fa fa-spinner fa-spin text-white text-sm mb-1"></i>
                        <span className="text-white text-xs">{analyzeProgress}%</span>
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
                className="w-full pr-20 outline-none resize-none bg-transparent"
                placeholder="发消息或粘贴图片，输入/选择技能"
                rows="2"
                disabled={isLoading}
                style={{ minHeight: '48px' }}
              />

              {/* 工具按钮组 - 绝对定位在右下角 */}
              <div className="absolute right-0 bottom-0 flex space-x-2">
                <button
                  onClick={toggleKnowledgeSidebar}
                  className="w-8 h-8 flex items-center justify-center text-gray-600 hover:text-primary hover:bg-gray-100 rounded-full transition-colors"
                  title="知识库"
                >
                  <i className="fa fa-book" aria-hidden="true"></i>
                </button>
                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className="w-8 h-8 flex items-center justify-center text-white bg-primary hover:bg-primary/90 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="发送"
                >
                  <i className="fa fa-paper-plane-o" aria-hidden="true"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatView
