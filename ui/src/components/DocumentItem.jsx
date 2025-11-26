import React, { useState } from 'react'
import useStore from '../store/useStore'
import { deleteDocument, updateDocumentVisibility as updateDocVisibilityAPI } from '../services/api'

function DocumentItem({ document }) {
  const removeDocument = useStore(state => state.removeDocument)
  const updateDocumentVisibility = useStore(state => state.updateDocumentVisibility)
  const openPdfViewer = useStore(state => state.openPdfViewer)
  const [showDeleteModal, setShowDeleteModal] = useState(false)

  const isPublic = document.is_public === 1

  const handleDelete = async () => {
    try {
      await deleteDocument(document.filename)
      removeDocument(document.filename, document.owner)
      setShowDeleteModal(false)
    } catch (error) {
      console.error('Failed to delete document:', error)
      alert('删除失败: ' + error.message)
    }
  }

  const handleToggleVisibility = async (e) => {
    e.stopPropagation()
    const newIsPublic = isPublic ? 0 : 1
    try {
      await updateDocVisibilityAPI(document.filename, newIsPublic)
      updateDocumentVisibility(document.filename, document.owner, newIsPublic)
    } catch (error) {
      console.error('Failed to update visibility:', error)
      alert('修改失败: ' + error.message)
    }
  }

  const handleClick = () => {
    openPdfViewer({
      filename: document.filename,
      owner: document.owner,
      pageNumber: 1
    }, true) // true 表示从知识文档列表打开
  }

  return (
    <>
      <div
        className="border border-gray-200 rounded-lg p-4 hover:border-primary transition-colors cursor-pointer relative group"
        onClick={handleClick}
      >
        <div className="flex items-start space-x-3">
          <div className={`w-10 h-10 ${isPublic ? 'bg-blue-100' : 'bg-green-100'} rounded-lg flex items-center justify-center ${isPublic ? 'text-blue-600' : 'text-green-600'}`}>
            <i className={`fa ${isPublic ? 'fa-globe' : 'fa-lock'}`} aria-hidden="true"></i>
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-gray-800">{document.filename}</h3>
            <p className="text-sm text-gray-500 mt-1">
              {isPublic ? '公有文档' : '私有文档'}
              {document.page_count && ` · ${document.page_count}页`}
            </p>
          </div>
          {/* 按钮组 - 总是显示，后端会验证权限 */}
          <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {/* 公开/私有切换按钮 */}
            <button
              onClick={handleToggleVisibility}
              className="w-6 h-6 flex items-center justify-center text-gray-400 hover:text-primary hover:bg-primary/10 rounded-full transition-all"
              title={isPublic ? '设为私有' : '设为公开'}
            >
              <i className={`fa ${isPublic ? 'fa-lock' : 'fa-globe'} text-sm`} aria-hidden="true"></i>
            </button>
            {/* 删除按钮 */}
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowDeleteModal(true)
              }}
              className="w-6 h-6 flex items-center justify-center text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-all"
              title="删除文档"
            >
              <i className="fa fa-trash-o text-sm" aria-hidden="true"></i>
            </button>
          </div>
        </div>
      </div>

      {/* 删除确认弹窗 */}
      {showDeleteModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setShowDeleteModal(false)}
        >
          <div
            className="bg-white rounded-xl shadow-2xl p-6 w-96 transform transition-all"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mr-4">
                <i className="fa fa-exclamation-triangle text-red-600 text-xl" aria-hidden="true"></i>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800">确认删除</h3>
                <p className="text-sm text-gray-500">此操作无法撤销</p>
              </div>
            </div>
            <p className="text-gray-600 mb-6">
              确定要删除文档 "<span className="font-medium">{document.filename}</span>" 吗？
            </p>
            <div className="flex space-x-3">
              <button
                onClick={handleDelete}
                className="flex-1 py-2 px-4 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                确认删除
              </button>
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 py-2 px-4 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default DocumentItem
