import React, { useState, useRef, useEffect } from 'react'
import { updateInstruction, deleteInstruction } from '../services/api'
import useStore from '../store/useStore'

function InstructionItem({ instruction }) {
    const [isEditing, setIsEditing] = useState(false)
    const [editContent, setEditContent] = useState(instruction.content)
    const [isSaving, setIsSaving] = useState(false)
    const [isDeleting, setIsDeleting] = useState(false)

    const updateInstructionInList = useStore(state => state.updateInstructionInList)
    const removeInstruction = useStore(state => state.removeInstruction)

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
            await updateInstruction(instruction.id, {
                content: editContent,
                is_active: instruction.is_active,
                priority: instruction.priority
            })

            updateInstructionInList(instruction.id, { content: editContent })
            setIsEditing(false)
        } catch (error) {
            console.error('Failed to update instruction:', error)
            alert('更新失败: ' + error.message)
        } finally {
            setIsSaving(false)
        }
    }

    const handleDelete = async () => {
        if (!window.confirm('确定要删除这条指示吗？')) return

        setIsDeleting(true)
        try {
            await deleteInstruction(instruction.id)
            removeInstruction(instruction.id)
        } catch (error) {
            console.error('Failed to delete instruction:', error)
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
        <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow group">
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
                                setEditContent(instruction.content)
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
                    <div className="text-sm text-gray-800 whitespace-pre-wrap mb-3">
                        {instruction.content}
                    </div>
                    <div className="flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <span className="text-xs text-gray-400">
                            {new Date(instruction.created_at).toLocaleDateString()}
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

export default InstructionItem
