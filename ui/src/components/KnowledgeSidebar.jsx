import React, { useEffect, useRef, useState } from 'react'
import useStore from '../store/useStore'
import { getDocuments, uploadPDF } from '../services/api'
import DocumentItem from './DocumentItem'

function KnowledgeSidebar() {
  const isOpen = useStore(state => state.isKnowledgeSidebarOpen)
  const setKnowledgeSidebarOpen = useStore(state => state.setKnowledgeSidebarOpen)
  const documents = useStore(state => state.documents)
  const setDocuments = useStore(state => state.setDocuments)
  const addDocument = useStore(state => state.addDocument)
  const uploadProgress = useStore(state => state.uploadProgress)
  const setUploadProgress = useStore(state => state.setUploadProgress)
  const resetUploadProgress = useStore(state => state.resetUploadProgress)

  const fileInputRef = useRef(null)

  const [isLoading, setIsLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const PAGE_SIZE = 20

  // 加载文档列表
  useEffect(() => {
    if (isOpen && documents.length === 0) {
      loadDocuments()
    }
  }, [isOpen])

  const loadDocuments = async (isLoadMore = false) => {
    if (isLoading) return

    setIsLoading(true)
    try {
      const currentPage = isLoadMore ? page : 1
      const response = await getDocuments(currentPage, PAGE_SIZE)
      const newDocuments = response.documents || []

      if (isLoadMore) {
        setDocuments([...documents, ...newDocuments])
      } else {
        setDocuments(newDocuments)
      }

      setPage(currentPage + 1)
      setHasMore(newDocuments.length === PAGE_SIZE)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // 处理文件上传
  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    // 重置文件输入,允许重复上传同一文件
    e.target.value = ''

    setUploadProgress({
      isUploading: true,
      filename: file.name,
      progress: 0,
      stage: 'init',
      message: '开始处理...',
      currentStep: ''
    })

    try {
      const result = await uploadPDF(file, 0, (progressData) => {
        console.log('[DEBUG] Component Progress Update:', progressData)
        setUploadProgress({
          progress: progressData.progress_percent || 0,
          stage: progressData.stage || '',
          message: progressData.message || '',
          currentStep: progressData.current_step || '',  // Capture current_step
          currentPage: progressData.current_page || 0,
          totalPages: progressData.total_pages || 0
        })
      })

      // 上传完成,添加到文档列表
      if (result && result.data) {
        addDocument({
          filename: file.name,
          is_public: 0,
          page_count: result.data.total_pages || 0
        })
      }

      // 1秒后隐藏进度条
      setTimeout(() => {
        resetUploadProgress()
      }, 1000)
    } catch (error) {
      console.error('Upload failed:', error)
      alert('上传失败: ' + error.message)
      resetUploadProgress()
    }
  }

  return (
    <div
      className={`${isOpen ? 'w-80 border-l border-gray-200' : 'w-0'
        } overflow-hidden transition-all duration-300 bg-white`}
    >
      <div className="w-80 h-[calc(100vh-200px)] my-[100px] p-6 overflow-y-auto scrollbar-thin">
        {/* 头部 */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-800">知识文档</h2>
          <button
            onClick={() => setKnowledgeSidebarOpen(false)}
            className="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-700 rounded-full transition-colors"
          >
            <i className="fa fa-times" aria-hidden="true"></i>
          </button>
        </div>

        {/* 文件上传组件 */}
        <div className="mb-6">
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-primary transition-colors cursor-pointer bg-gray-50"
          >
            <i className="fa fa-cloud-upload text-3xl text-gray-400 mb-2" aria-hidden="true"></i>
            <p className="text-gray-600 text-sm mb-1">点击或拖拽文件上传</p>
            <p className="text-xs text-gray-500">支持 PDF、Excel 格式</p>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.xlsx,.xls"
              onChange={handleFileSelect}
            />
          </div>

          {/* 上传进度显示 */}
          {uploadProgress.isUploading && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="mb-3">
                <span className="text-sm font-medium text-gray-700">
                  {uploadProgress.filename}
                </span>
              </div>

              {/* 显示详细消息和页码 */}
              <div className="text-sm text-primary mb-2">
                {uploadProgress.message}
                {uploadProgress.totalPages > 0 && uploadProgress.currentPage > 0 && (
                  <span className="ml-2 text-xs text-gray-600">
                    ({uploadProgress.currentPage}/{uploadProgress.totalPages})
                  </span>
                )}
              </div>

              {/* 进度条 */}
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress.progress}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>

        {/* 文档列表 */}
        <div
          className="space-y-4"
          onScroll={(e) => {
            const { scrollTop, clientHeight, scrollHeight } = e.target
            if (scrollHeight - scrollTop - clientHeight < 50 && !isLoading && hasMore) {
              loadDocuments(true)
            }
          }}
        >
          {documents.length === 0 && !isLoading ? (
            <div className="text-center text-gray-500 py-8">
              <i className="fa fa-folder-open-o text-4xl mb-2" aria-hidden="true"></i>
              <p className="text-sm">暂无文档</p>
            </div>
          ) : (
            <>
              {/* 文档总数显示 */}
              <div className="text-sm text-gray-600 mb-2">
                共 {documents.length} 个文档
              </div>

              {/* 文档列表 */}
              {documents.map((doc, index) => (
                <DocumentItem key={`${doc.filename}-${doc.owner}-${index}`} document={doc} />
              ))}

              {isLoading && (
                <div className="flex flex-col items-center justify-center py-4 text-gray-400 gap-2">
                  <i className="fa fa-circle-o-notch fa-spin text-sm"></i>
                  <span className="text-xs">加载中...</span>
                </div>
              )}

              {!hasMore && documents.length > 0 && (
                <div className="text-center py-4 text-xs text-gray-300">
                  没有更多了
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default KnowledgeSidebar
