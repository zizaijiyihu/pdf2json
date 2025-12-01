import React, { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { sendChatMessage } from '../services/api'

function ReminderAnalysisCard({ reminder, onClose }) {
    const [status, setStatus] = useState('loading') // loading, done, error
    const [content, setContent] = useState('')
    const [isExpanded, setIsExpanded] = useState(true)
    const abortControllerRef = useRef(null)

    useEffect(() => {
        analyzeReminder()

        // 清理函数：组件卸载时中止请求
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort()
            }
        }
    }, [reminder.id])

    const analyzeReminder = async () => {
        setStatus('loading')
        setContent('')

        abortControllerRef.current = new AbortController()
        let streamingContent = ''

        try {
            await sendChatMessage(
                reminder.content,
                null, // 不传历史
                (chunk) => {
                    if (chunk.type === 'content') {
                        streamingContent += chunk.content
                        setContent(streamingContent)
                    }
                },
                abortControllerRef.current.signal,
                null, // 不传 conversation_id
                false // 禁用历史记录
            )

            setStatus('done')
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Analysis aborted for reminder:', reminder.id)
            } else {
                console.error('Failed to analyze reminder:', error)
                setStatus('error')
                // 错误时自动关闭
                setTimeout(() => {
                    onClose(reminder.id)
                }, 1000)
            }
        } finally {
            abortControllerRef.current = null
        }
    }

    return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden transition-all">
            {/* 头部 - 标题和操作 */}
            <div
                className="p-3 bg-gray-50/50 border-b border-gray-100 flex items-start justify-between cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex-1 pr-2">
                    <div className="text-sm font-medium text-gray-800 line-clamp-2">
                        {reminder.content}
                    </div>
                    {status === 'loading' && (
                        <div className="flex items-center gap-1.5 mt-1.5 text-xs text-gray-400">
                            <div className="w-1 h-1 bg-gray-400 rounded-full animate-pulse"></div>
                            <div className="w-1 h-1 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                            <div className="w-1 h-1 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                            <span className="ml-1">分析中</span>
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-1">
                    {/* 展开/收起图标 */}
                    {status === 'done' && (
                        <button
                            onClick={(e) => {
                                e.stopPropagation()
                                setIsExpanded(!isExpanded)
                            }}
                            className="w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600 rounded transition-colors"
                        >
                            <i className={`fa fa-chevron-${isExpanded ? 'up' : 'down'} text-xs`}></i>
                        </button>
                    )}

                    {/* 关闭按钮 */}
                    <button
                        onClick={(e) => {
                            e.stopPropagation()
                            onClose(reminder.id)
                        }}
                        className="w-6 h-6 flex items-center justify-center text-gray-400 hover:text-red-500 rounded transition-colors"
                        title="关闭"
                    >
                        <i className="fa fa-times text-xs"></i>
                    </button>
                </div>
            </div>

            {/* 内容区域 */}
            {isExpanded && status === 'done' && content && (
                <div className="p-3 text-sm text-gray-700 leading-relaxed max-h-60 overflow-y-auto scrollbar-thin">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            // 代码块样式
                            code: ({ inline, children, ...props }) => {
                                return inline ? (
                                    <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
                                        {children}
                                    </code>
                                ) : (
                                    <code className="block bg-gray-100 p-2 rounded text-xs font-mono overflow-x-auto my-2" {...props}>
                                        {children}
                                    </code>
                                )
                            },
                            // 列表样式
                            ul: ({ children }) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
                            // 标题样式
                            h1: ({ children }) => <h1 className="text-base font-bold my-2">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-sm font-bold my-2">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-sm font-bold my-1.5">{children}</h3>,
                            // 段落样式
                            p: ({ children }) => <p className="my-1.5">{children}</p>,
                            // 粗体
                            strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                            // 链接样式
                            a: ({ href, children, ...props }) => (
                                <a href={href} className="text-primary hover:underline" target="_blank" rel="noopener noreferrer" {...props}>
                                    {children}
                                </a>
                            ),
                            // 表格样式
                            table: ({ children }) => (
                                <div className="overflow-x-auto my-3">
                                    <table className="min-w-full border-collapse border border-gray-300 text-xs">
                                        {children}
                                    </table>
                                </div>
                            ),
                            thead: ({ children }) => <thead className="bg-gray-100">{children}</thead>,
                            tbody: ({ children }) => <tbody>{children}</tbody>,
                            tr: ({ children }) => <tr className="border-b border-gray-300">{children}</tr>,
                            th: ({ children }) => (
                                <th className="border border-gray-300 px-3 py-1.5 text-left font-semibold">
                                    {children}
                                </th>
                            ),
                            td: ({ children }) => (
                                <td className="border border-gray-300 px-3 py-1.5">
                                    {children}
                                </td>
                            ),
                        }}
                    >
                        {content}
                    </ReactMarkdown>
                </div>
            )}

            {/* 错误状态 */}
            {status === 'error' && (
                <div className="p-3 text-xs text-red-500 flex items-center gap-2">
                    <i className="fa fa-exclamation-circle"></i>
                    <span>分析失败，即将关闭...</span>
                </div>
            )}
        </div>
    )
}

export default ReminderAnalysisCard
