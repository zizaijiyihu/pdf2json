import React, { useState, useEffect, useMemo } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import useStore from '../store/useStore'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import 'react-pdf/dist/esm/Page/TextLayer.css'

// 配置PDF.js worker - 使用npm包自带的worker
pdfjs.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

function PdfViewer() {
  const isPdfViewerOpen = useStore(state => state.isPdfViewerOpen)
  const currentPdf = useStore(state => state.currentPdf)
  const closePdfViewer = useStore(state => state.closePdfViewer)
  const setPdfPage = useStore(state => state.setPdfPage)

  const [numPages, setNumPages] = useState(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // 使用useMemo稳定pdfUrl，避免重复渲染导致Document组件重新加载
  const pdfUrl = useMemo(() => {
    if (!currentPdf) return null
    const url = `/api/documents/${encodeURIComponent(currentPdf.filename)}/content`
    return url
  }, [currentPdf?.filename])

  // 使用useMemo缓存file对象，避免不必要的重新加载
  const fileConfig = useMemo(() => ({
    url: pdfUrl,
    httpHeaders: {
      'Accept': 'application/pdf'
    },
    withCredentials: false
  }), [pdfUrl])

  // 使用useMemo缓存options对象，避免不必要的重新加载
  const documentOptions = useMemo(() => ({
    cMapUrl: `https://unpkg.com/pdfjs-dist@${pdfjs.version}/cmaps/`,
    cMapPacked: true,
    standardFontDataUrl: `https://unpkg.com/pdfjs-dist@${pdfjs.version}/standard_fonts/`
  }), [pdfjs.version])

  // 当PDF信息变化时,更新页码
  useEffect(() => {
    if (currentPdf) {
      console.log('[PdfViewer] PDF changed, opening:', currentPdf.filename)
      console.log('[PdfViewer] PDF URL:', pdfUrl)
      setPageNumber(currentPdf.pageNumber || 1)
      setLoading(true)
      setError(null)
    }
  }, [currentPdf, pdfUrl])

  // PDF加载成功回调
  const onDocumentLoadSuccess = ({ numPages }) => {
    console.log('[PdfViewer] PDF loaded successfully, pages:', numPages)
    setNumPages(numPages)
    setLoading(false)
  }

  // PDF加载失败回调
  const onDocumentLoadError = (error) => {
    console.error('[PdfViewer] Failed to load PDF:', error)
    console.error('[PdfViewer] PDF URL was:', pdfUrl)
    console.error('[PdfViewer] Error details:', error)
    setError(`PDF加载失败: ${error.message || '未知错误'}`)
    setLoading(false)
  }

  // 翻页功能
  const goToPreviousPage = () => {
    if (pageNumber > 1) {
      const newPage = pageNumber - 1
      setPageNumber(newPage)
      setPdfPage(newPage)
    }
  }

  const goToNextPage = () => {
    if (pageNumber < numPages) {
      const newPage = pageNumber + 1
      setPageNumber(newPage)
      setPdfPage(newPage)
    }
  }

  const goToPage = (page) => {
    const targetPage = Math.max(1, Math.min(page, numPages))
    setPageNumber(targetPage)
    setPdfPage(targetPage)
  }

  if (!currentPdf || !pdfUrl) return null

  return (
    <div
      className={`${isPdfViewerOpen ? 'w-[500px] border-l border-gray-200' : 'w-0'
        } overflow-hidden transition-all duration-300 bg-white h-screen`}
    >
      <div className="w-[500px] h-full flex flex-col bg-white">
        {/* 头部工具栏 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium text-gray-800 truncate" title={currentPdf.filename}>
              {currentPdf.filename}
            </h3>
            {numPages && (
              <p className="text-xs text-gray-500">
                第 {pageNumber} 页 / 共 {numPages} 页
              </p>
            )}
          </div>
          <button
            onClick={closePdfViewer}
            className="ml-2 w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-700 rounded-full transition-colors flex-shrink-0"
          >
            <i className="fa fa-times" aria-hidden="true"></i>
          </button>
        </div>

        {/* PDF内容区域 */}
        <div className="flex-1 overflow-auto scrollbar-thin bg-gray-100 flex items-center justify-center p-2">
          {error && (
            <div className="text-center text-red-600">
              <i className="fa fa-exclamation-triangle text-3xl mb-2" aria-hidden="true"></i>
              <p>{error}</p>
            </div>
          )}

          {!error && (
            <Document
              file={fileConfig}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              options={documentOptions}
              loading={
                <div className="flex items-center justify-center py-20">
                  <i className="fa fa-circle-o-notch fa-spin text-2xl text-primary" aria-hidden="true"></i>
                </div>
              }
            >
              <Page
                pageNumber={pageNumber}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                width={470}
                className="shadow-lg"
              />
            </Document>
          )}
        </div>

        {/* 底部翻页控制栏 */}
        {numPages && (
          <div className="p-4 border-t border-gray-200 bg-white">
            <div className="flex items-center justify-center gap-4">
              <button
                onClick={goToPreviousPage}
                disabled={pageNumber <= 1}
                className="w-9 h-9 flex items-center justify-center text-gray-600 hover:text-primary hover:bg-gray-100 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <i className="fa fa-chevron-left" aria-hidden="true"></i>
              </button>

              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={pageNumber}
                  onChange={(e) => {
                    const page = parseInt(e.target.value, 10)
                    if (!isNaN(page)) {
                      goToPage(page)
                    }
                  }}
                  className="w-16 px-2 py-1 text-center border border-gray-300 rounded focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none"
                  min="1"
                  max={numPages}
                />
                <span className="text-gray-600">/ {numPages}</span>
              </div>

              <button
                onClick={goToNextPage}
                disabled={pageNumber >= numPages}
                className="w-9 h-9 flex items-center justify-center text-gray-600 hover:text-primary hover:bg-gray-100 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <i className="fa fa-chevron-right" aria-hidden="true"></i>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PdfViewer
