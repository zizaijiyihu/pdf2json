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

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 10

  // Calculate pagination
  const totalPages = Math.ceil(documents.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentDocuments = documents.slice(startIndex, endIndex)

  // Reset to first page when documents change
  useEffect(() => {
    setCurrentPage(1)
  }, [documents.length])

  // 加载文档列表
  useEffect(() => {
    if (isOpen && documents.length === 0) {
      loadDocuments()
    }
  }, [isOpen])

  const loadDocuments = async () => {
    try {
      const response = await getDocuments()
      setDocuments(response.documents || [])
    } catch (error) {
      console.error('Failed to load documents:', error)
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
      message: '开始处理...'
    })

    try {
      const result = await uploadPDF(file, 0, (progressData) => {
        setUploadProgress({
          progress: progressData.progress_percent || 0,
          stage: progressData.stage || '',
          message: progressData.message || '',
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
            <p className="text-xs text-gray-500">目前仅支持 PDF 格式</p>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf"
              onChange={handleFileSelect}
            />
          </div>

          {/* 上传进度显示 */}
          {uploadProgress.isUploading && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">{uploadProgress.filename}</span>
                <span className="text-xs text-gray-500">{uploadProgress.stage}</span>
              </div>
              <div className="text-sm text-primary mb-2">
                {uploadProgress.totalPages > 0
                  ? `共${uploadProgress.totalPages}页，第${uploadProgress.currentPage}页解析中`
                  : uploadProgress.message}
              </div>
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
        <div className="space-y-4">
          {documents.length === 0 ? (
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

              {/* 当前页文档列表 */}
              {currentDocuments.map((doc, index) => (
                <DocumentItem key={`${doc.filename}-${doc.owner}-${startIndex + index}`} document={doc} />
              ))}

              {/* 分页控件 */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 pt-4 border-t border-gray-200">
                  {/* 上一页按钮 */}
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className={`px-3 py-1 rounded-md text-sm transition-colors ${currentPage === 1
                        ? 'text-gray-400 cursor-not-allowed'
                        : 'text-gray-700 hover:bg-gray-100'
                      }`}
                  >
                    <i className="fa fa-chevron-left" aria-hidden="true"></i>
                  </button>

                  {/* 页码显示 */}
                  <div className="flex items-center gap-1">
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => {
                      // 只显示当前页附近的页码
                      if (
                        page === 1 ||
                        page === totalPages ||
                        (page >= currentPage - 1 && page <= currentPage + 1)
                      ) {
                        return (
                          <button
                            key={page}
                            onClick={() => setCurrentPage(page)}
                            className={`w-8 h-8 rounded-md text-sm transition-colors ${currentPage === page
                                ? 'bg-primary text-white'
                                : 'text-gray-700 hover:bg-gray-100'
                              }`}
                          >
                            {page}
                          </button>
                        )
                      } else if (
                        page === currentPage - 2 ||
                        page === currentPage + 2
                      ) {
                        return <span key={page} className="text-gray-400">...</span>
                      }
                      return null
                    })}
                  </div>

                  {/* 下一页按钮 */}
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className={`px-3 py-1 rounded-md text-sm transition-colors ${currentPage === totalPages
                        ? 'text-gray-400 cursor-not-allowed'
                        : 'text-gray-700 hover:bg-gray-100'
                      }`}
                  >
                    <i className="fa fa-chevron-right" aria-hidden="true"></i>
                  </button>
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
