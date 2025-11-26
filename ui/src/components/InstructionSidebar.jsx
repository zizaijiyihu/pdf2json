import React, { useEffect, useState } from 'react'
import useStore from '../store/useStore'
import { getInstructions, createInstruction } from '../services/api'
import InstructionItem from './InstructionItem'

function InstructionSidebar() {
    const isOpen = useStore(state => state.isInstructionSidebarOpen)
    const setInstructionSidebarOpen = useStore(state => state.setInstructionSidebarOpen)
    const instructions = useStore(state => state.instructions)
    const setInstructions = useStore(state => state.setInstructions)
    const addInstruction = useStore(state => state.addInstruction)
    const clearMessages = useStore(state => state.clearMessages) // 清空对话历史

    const [isCreating, setIsCreating] = useState(false)
    const [newContent, setNewContent] = useState('')
    const [isSaving, setIsSaving] = useState(false)

    // 加载指示列表
    useEffect(() => {
        if (isOpen && instructions.length === 0) {
            loadInstructions()
        }
    }, [isOpen])

    const loadInstructions = async () => {
        try {
            const response = await getInstructions()
            setInstructions(response.instructions || [])
        } catch (error) {
            console.error('Failed to load instructions:', error)
        }
    }

    const handleCreate = async () => {
        if (!newContent.trim() || isSaving) return

        setIsSaving(true)
        try {
            const result = await createInstruction(newContent)
            if (result.success) {
                // 重新加载列表或者直接添加到store
                // 这里为了简单直接添加到store，实际应该用后端返回的完整对象
                // 但后端返回的 instruction_id，我们需要构造一个对象
                const newInstruction = {
                    id: result.instruction_id,
                    content: newContent,
                    is_active: 1,
                    priority: 0,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                }
                addInstruction(newInstruction)
                setNewContent('')
                setIsCreating(false)

                // 清空对话历史，避免旧的上下文污染
                clearMessages()
            }
        } catch (error) {
            console.error('Failed to create instruction:', error)
            alert('创建失败: ' + error.message)
        } finally {
            setIsSaving(false)
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
                    <h2 className="text-xl font-semibold text-gray-800">我的指示</h2>
                    <button
                        onClick={() => setInstructionSidebarOpen(false)}
                        className="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-700 rounded-full transition-colors"
                    >
                        <i className="fa fa-times" aria-hidden="true"></i>
                    </button>
                </div>

                {/* 创建新指示 */}
                <div className="mb-6">
                    {isCreating ? (
                        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                            <textarea
                                value={newContent}
                                onChange={(e) => setNewContent(e.target.value)}
                                placeholder="请输入新的指示内容..."
                                className="w-full p-2 mb-3 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none resize-none bg-white"
                                rows="3"
                                autoFocus
                            />
                            <div className="flex justify-end gap-2">
                                <button
                                    onClick={() => {
                                        setIsCreating(false)
                                        setNewContent('')
                                    }}
                                    className="px-3 py-1 text-xs text-gray-600 hover:bg-gray-200 rounded transition-colors"
                                    disabled={isSaving}
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleCreate}
                                    className="px-3 py-1 text-xs text-white bg-primary hover:bg-primary/90 rounded transition-colors flex items-center gap-1"
                                    disabled={isSaving || !newContent.trim()}
                                >
                                    {isSaving && <i className="fa fa-spinner fa-spin"></i>}
                                    创建
                                </button>
                            </div>
                        </div>
                    ) : (
                        <button
                            onClick={() => setIsCreating(true)}
                            className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-primary hover:text-primary transition-colors flex items-center justify-center gap-2"
                        >
                            <i className="fa fa-plus"></i>
                            <span>新建指示</span>
                        </button>
                    )}
                </div>

                {/* 指示列表 */}
                <div className="space-y-4">
                    {instructions.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                            <i className="fa fa-lightbulb-o text-4xl mb-2" aria-hidden="true"></i>
                            <p className="text-sm">暂无指示</p>
                        </div>
                    ) : (
                        instructions.map((inst) => (
                            <InstructionItem key={inst.id} instruction={inst} />
                        ))
                    )}
                </div>
            </div>
        </div>
    )
}

export default InstructionSidebar
