import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import useStore from '../store/useStore'

function ChatMessage({ message }) {
  const openPdfViewer = useStore(state => state.openPdfViewer)

  const isUser = message.role === 'user'

  const handleDocumentClick = (filename, pageNumber) => {
    openPdfViewer({ filename, pageNumber })
  }

  // 自定义渲染组件
  const components = {
    // 自定义链接渲染 - 识别 http://pdf/文档.pdf:页码 格式
    a: ({ node, children, href, ...props }) => {
      // 匹配 http://pdf/文档名.pdf:页码 格式
      const match = href?.match(/^http:\/\/pdf\/(.+\.pdf):(\d+)$/)
      if (match) {
        // 解码文件名（因为ReactMarkdown可能已经对href进行了URL编码）
        const filename = decodeURIComponent(match[1])
        const pageNumber = parseInt(match[2], 10)
        return (
          <button
            onClick={(e) => {
              e.preventDefault()
              handleDocumentClick(filename, pageNumber)
            }}
            className="inline-flex items-center gap-1 text-primary hover:text-primary/80 hover:underline transition-colors cursor-pointer"
            title={`查看 ${filename} 第 ${pageNumber} 页`}
          >
            <i className="fa fa-file-pdf-o" aria-hidden="true"></i>
            <span>{children}</span>
          </button>
        )
      }
      return <a href={href} {...props} className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">{children}</a>
    },
    // 代码块样式
    code: ({ node, inline, children, ...props }) => {
      return inline ? (
        <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
          {children}
        </code>
      ) : (
        <code className="block bg-gray-100 p-2 rounded text-sm font-mono overflow-x-auto" {...props}>
          {children}
        </code>
      )
    },
    // 列表样式
    ul: ({ children }) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
    // 标题样式
    h1: ({ children }) => <h1 className="text-xl font-bold my-2">{children}</h1>,
    h2: ({ children }) => <h2 className="text-lg font-bold my-2">{children}</h2>,
    h3: ({ children }) => <h3 className="text-base font-bold my-1.5">{children}</h3>,
    // 段落样式
    p: ({ children }) => <p className="my-1.5">{children}</p>,
    // 粗体
    strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
    // 表格样式
    table: ({ children }) => (
      <div className="overflow-x-auto my-4">
        <table className="min-w-full border-collapse border border-gray-300">
          {children}
        </table>
      </div>
    ),
    thead: ({ children }) => <thead className="bg-gray-100">{children}</thead>,
    tbody: ({ children }) => <tbody>{children}</tbody>,
    tr: ({ children }) => <tr className="border-b border-gray-300">{children}</tr>,
    th: ({ children }) => (
      <th className="border border-gray-300 px-4 py-2 text-left font-semibold">
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className="border border-gray-300 px-4 py-2">
        {children}
      </td>
    ),
  }

  return (
    <div className={`mb-4 max-w-[80%] ${isUser ? 'ml-auto' : ''}`}>
      <div className={`p-3 rounded-lg ${isUser
        ? 'bg-light-blue rounded-tl-none'
        : 'bg-white border border-gray-100 rounded-tr-none'
        }`}>
        {isUser ? (
          // 用户消息直接显示
          <div>
            {message.content}
            {/* 显示附带的图片 */}
            {message.images && message.images.length > 0 && (
              <div className="flex gap-2 mt-2 flex-wrap">
                {message.images.map((img, idx) => (
                  <img
                    key={idx}
                    src={img.thumbnail}
                    alt="attachment"
                    className="max-w-[120px] max-h-[120px] rounded border border-gray-200 object-contain cursor-pointer hover:opacity-80 transition-opacity bg-gray-50"
                    onClick={() => window.open(img.url, '_blank')}
                    title="点击查看原图"
                  />
                ))}
              </div>
            )}
          </div>
        ) : (
          // 系统消息使用markdown渲染
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={components}
          >
            {message.content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  )
}

export default ChatMessage
