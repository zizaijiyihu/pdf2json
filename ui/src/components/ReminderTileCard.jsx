import React, { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { sendChatMessage } from '../services/api'
import { getReminderAnalysis, setReminderAnalysis } from '../services/indexedDBCache'
import useStore from '../store/useStore'

/**
 * 简洁的提醒平铺卡片组件
 * 用于首页展示，样式更简洁紧凑
 */
function ReminderTileCard({ reminder, onClose, canAnalyze }) {
    const [status, setStatus] = useState('waiting') // waiting, loading, done, error
    const [content, setContent] = useState('')
    const abortControllerRef = useRef(null)

    // 状态管理
    const markAnalyzed = useStore(state => state.markAnalyzed)

    useEffect(() => {
        loadAnalysis()

        // 清理函数：组件卸载时中止请求
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort()
            }
        }
    }, [reminder.id])

    // 监听是否可以开始分析
    useEffect(() => {
        if (canAnalyze && status === 'waiting') {
            console.log('🚀 获得许可，开始分析:', reminder.id)
            startAnalysis()
        }
    }, [canAnalyze, status])

    const loadAnalysis = async () => {
        setStatus('waiting')
        setContent('')

        // 1. 先尝试从 IndexedDB 获取缓存
        const cachedAnalysis = await getReminderAnalysis(reminder.id)
        if (cachedAnalysis) {
            console.log('✓ 使用缓存的提醒分析:', reminder.id)
            setContent(cachedAnalysis)
            setStatus('done')
            markAnalyzed(reminder.id)
            return
        }

        // 2. 缓存未命中，保持 waiting 状态，等待父组件授权
        console.log('⏳ 等待分析授权:', reminder.id)
    }

    const startAnalysis = async () => {
        setStatus('loading')
        await analyzeReminder()
    }

    const analyzeReminder = async () => {
        abortControllerRef.current = new AbortController()
        let streamingContent = ''

        try {
            await sendChatMessage(
                reminder.content,
                null,
                (chunk) => {
                    if (chunk.type === 'content') {
                        streamingContent += chunk.content

                        // 检测 [NO_RESULT] 标记
                        if (streamingContent.includes('[NO_RESULT]')) {
                            setTimeout(() => {
                                onClose(reminder.id)
                            }, 300)
                            return
                        }

                        setContent(streamingContent)
                    }
                },
                abortControllerRef.current.signal,
                null,
                false,
                {
                    mode: 'reminder',
                    streamContent: false
                }
            )

            // 最终检查一次是否包含 [NO_RESULT]
            if (streamingContent.includes('[NO_RESULT]')) {
                setTimeout(() => {
                    onClose(reminder.id)
                }, 300)
            } else {
                // 分析成功,保存到 IndexedDB
                await setReminderAnalysis(reminder.id, streamingContent)
                setStatus('done')
                markAnalyzed(reminder.id)
                console.log('✅ 完成分析提醒:', reminder.id)
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('⏹️ 分析已中止:', reminder.id)
            } else {
                console.error('❌ 分析失败:', reminder.id, error)
                setStatus('error')
                // 即使失败也标记为已分析，以免阻塞队列
                markAnalyzed(reminder.id)
                setTimeout(() => {
                    onClose(reminder.id)
                }, 1000)
            }
        } finally {
            abortControllerRef.current = null
        }
    }

    return (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-300 flex flex-col w-full">
            {/* 头部 - 标题和关闭按钮 */}
            <div className="p-4 border-b border-gray-100 flex items-start justify-between bg-gradient-to-r from-blue-50/50 to-transparent">
                <div className="flex-1 pr-2">
                    <h4 className="text-sm font-semibold text-gray-800 line-clamp-2">
                        {reminder.content}
                    </h4>
                    {status === 'waiting' && (
                        <div className="flex items-center gap-0.5 mt-2 text-xs text-gray-400">
                            <div className="w-1 h-1 bg-gray-300 rounded-full"></div>
                            <div className="w-1 h-1 bg-gray-300 rounded-full"></div>
                            <div className="w-1 h-1 bg-gray-300 rounded-full"></div>
                        </div>
                    )}
                    {status === 'loading' && (
                        <div className="flex items-center gap-1.5 mt-2 text-xs text-gray-500">
                            <div className="w-1 h-1 bg-gray-400 rounded-full animate-pulse"></div>
                            <div className="w-1 h-1 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                            <div className="w-1 h-1 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                            <span className="ml-1">正在生成</span>
                        </div>
                    )}
                </div>

                {/* 关闭按钮 */}
                <button
                    onClick={() => onClose(reminder.id)}
                    className="w-7 h-7 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-all flex-shrink-0"
                    title="关闭"
                >
                    <i className="fa fa-times text-sm"></i>
                </button>
            </div>

            {/* 内容区域 */}
            {status === 'done' && content && (
                <div className="p-4 text-sm text-gray-700 leading-relaxed">
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
                            h3: ({ children }) => <h3 className="text-sm font-semibold my-1.5">{children}</h3>,
                            // 段落样式
                            p: ({ children }) => <p className="my-1.5">{children}</p>,
                            // 粗体
                            strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                            // 链接样式
                            a: ({ href, children, ...props }) => (
                                <a
                                    href={href}
                                    className="hover:text-primary/80 transition-all duration-200 group inline"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    {...props}
                                >
                                    <span className="border-b border-gray-300 group-hover:border-primary/60">{children}</span>
                                    <i className="fa fa-external-link text-xs opacity-60 group-hover:opacity-100 ml-1" aria-hidden="true"></i>
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
                <div className="p-4 text-xs text-red-500 flex items-center gap-2">
                    <i className="fa fa-exclamation-circle"></i>
                    <span>分析失败，即将关闭...</span>
                </div>
            )}

            {/* 等待占位 */}
            {status === 'waiting' && (
                <div className="p-4 flex items-center justify-center min-h-[100px]">
                    <div className="flex items-center gap-1">
                        <div className="w-1.5 h-1.5 bg-gray-300 rounded-full"></div>
                        <div className="w-1.5 h-1.5 bg-gray-300 rounded-full"></div>
                        <div className="w-1.5 h-1.5 bg-gray-300 rounded-full"></div>
                    </div>
                </div>
            )}

            {/* 加载占位 */}
            {status === 'loading' && (
                <div className="p-4 flex items-center justify-center min-h-[100px]">
                    <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse"></div>
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default ReminderTileCard
