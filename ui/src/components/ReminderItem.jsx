import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { updateReminder, deleteReminder } from '../services/api'
import useStore from '../store/useStore'

function ReminderItem({ reminder }) {
    const [isEditing, setIsEditing] = useState(false)
    const [editContent, setEditContent] = useState(reminder.content)
    const [isSaving, setIsSaving] = useState(false)
    const [isDeleting, setIsDeleting] = useState(false)

    const updateReminderInList = useStore(state => state.updateReminderInList)
    const removeReminder = useStore(state => state.removeReminder)

    const textareaRef = useRef(null)

    useEffect(() => {
        if (isEditing && textareaRef.current) {
            textareaRef.current.focus()
            textareaRef.current.style.height = 'auto'
            textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
        }
    }, [isEditing])

    const handleSave = async () => {
        if (!editContent.trim() || isSaving) return

        setIsSaving(true)
        try {
            await updateReminder(reminder.id, editContent)
            updateReminderInList(reminder.id, { content: editContent })
            setIsEditing(false)
        } catch (error) {
            console.error('Failed to update reminder:', error)
            alert('更新失败: ' + error.message)
        } finally {
            setIsSaving(false)
        }
    }

    const handleDelete = async () => {
        setIsDeleting(true)
        try {
            await deleteReminder(reminder.id)
            removeReminder(reminder.id)
        } catch (error) {
            console.error('Failed to delete reminder:', error)
            alert('删除失败: ' + error.message)
            setIsDeleting(false)
        }
    }

    const handleTextareaInput = (e) => {
        setEditContent(e.target.value)
        e.target.style.height = 'auto'
        e.target.style.height = e.target.scrollHeight + 'px'
    }

    return (
        <div className="bg-transparent border border-gray-100 rounded-lg p-4 hover:bg-gray-50/50 transition-all group">
            {isEditing ? (
                <div className="space-y-3">
                    <textarea
                        ref={textareaRef}
                        value={editContent}
                        onChange={handleTextareaInput}
                        className="w-full p-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none resize-none"
                        rows="3"
                        disabled={isSaving}
                    />
                    <div className="flex justify-end gap-2">
                        <button
                            onClick={() => {
                                setIsEditing(false)
                                setEditContent(reminder.content)
                            }}
                            className="px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded transition-colors"
                            disabled={isSaving}
                        >
                            取消
                        </button>
                        <button
                            onClick={handleSave}
                            className="px-3 py-1 text-xs text-white bg-primary hover:bg-primary/90 rounded transition-colors flex items-center gap-1"
                            disabled={isSaving}
                        >
                            {isSaving && <i className="fa fa-spinner fa-spin"></i>}
                            保存
                        </button>
                    </div>
                </div>
            ) : (
                <>
                    <div className="text-sm text-gray-800 mb-3">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                // 代码块样式
                                code: ({ inline, children, ...props }) => {
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
                            }}
                        >
                            {reminder.content}
                        </ReactMarkdown>
                    </div>
                    <div className="flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="text-xs text-gray-400">
                            {new Date(reminder.created_at).toLocaleDateString()}
                        </span>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setIsEditing(true)}
                                className="text-gray-400 hover:text-primary transition-colors"
                                title="编辑"
                            >
                                <i className="fa fa-pencil"></i>
                            </button>
                            <button
                                onClick={handleDelete}
                                className="text-gray-400 hover:text-red-500 transition-colors"
                                title="删除"
                                disabled={isDeleting}
                            >
                                {isDeleting ? (
                                    <i className="fa fa-spinner fa-spin"></i>
                                ) : (
                                    <i className="fa fa-trash-o"></i>
                                )}
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default ReminderItem
