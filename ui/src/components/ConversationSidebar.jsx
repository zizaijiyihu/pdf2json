import React, { useEffect, useState } from 'react'
import useStore from '../store/useStore'
import { getConversations, deleteConversation, getConversationMessages } from '../services/api'

function ConversationSidebar() {
    const isOpen = useStore(state => state.isConversationSidebarOpen)
    const toggleSidebar = useStore(state => state.toggleConversationSidebar)
    const conversations = useStore(state => state.conversations)
    const setConversations = useStore(state => state.setConversations)
    const currentConversationId = useStore(state => state.currentConversationId)
    const setCurrentConversationId = useStore(state => state.setCurrentConversationId)
    const setChatHistory = useStore(state => state.setChatHistory)
    const setMessages = useStore(state => state.setMessages)
    const removeConversation = useStore(state => state.removeConversation)

    const [isLoading, setIsLoading] = useState(false)

    // 加载会话列表
    useEffect(() => {
        if (isOpen) {
            loadConversations()
        }
    }, [isOpen])

    const loadConversations = async () => {
        setIsLoading(true)
        try {
            const res = await getConversations(50, 0) // 加载最近50条
            setConversations(res.data.conversations || [])
        } catch (error) {
            console.error('Failed to load conversations:', error)
        } finally {
            setIsLoading(false)
        }
    }

    // 新建会话
    const handleNewChat = () => {
        // 清空当前状态
        setCurrentConversationId(null)
        setChatHistory([])
        setMessages([])
        // 关闭侧边栏
        toggleSidebar()
    }

    // 切换会话
    const handleSelectChat = async (conversationId) => {
        if (currentConversationId === conversationId) return

        setCurrentConversationId(conversationId)
        setMessages([]) // 先清空当前显示

        try {
            const res = await getConversationMessages(conversationId)
            // 后端返回的消息格式: { role, content, tool_calls, ... }
            // 前端需要的格式: { role, content, ... } (基本一致)

            setMessages(res.data.messages || [])
            setChatHistory(res.data.messages || []) // 同时更新历史上下文

            // 移动端或小屏幕下自动关闭侧边栏
            // toggleSidebar()
        } catch (error) {
            console.error('Failed to load conversation messages:', error)
        }
    }

    // 删除会话
    const handleDeleteChat = async (e, conversationId) => {
        e.stopPropagation() // 阻止冒泡
        // if (!window.confirm('确定要删除这个会话吗？')) return

        try {
            await deleteConversation(conversationId)
            removeConversation(conversationId)
        } catch (error) {
            console.error('Failed to delete conversation:', error)
        }
    }

    return (
        <>
            {/* 触发器 (抽屉把手) - 仅在关闭时显示 */}
            {!isOpen && (
                <div
                    onClick={toggleSidebar}
                    className="fixed left-0 top-1/2 transform -translate-y-1/2 w-6 h-24 bg-white border-y border-r border-gray-200 hover:bg-gray-50 rounded-r-xl cursor-pointer transition-all z-50 flex items-center justify-center group shadow-md"
                    title="历史会话"
                >
                    <div className="w-1 h-8 bg-gray-300 group-hover:bg-gray-400 rounded-full"></div>
                </div>
            )}

            {/* 侧边栏抽屉 */}
            <div
                className={`fixed left-0 top-0 h-full bg-white shadow-2xl z-40 transition-transform duration-300 ease-in-out transform ${isOpen ? 'translate-x-0' : '-translate-x-full'
                    }`}
                style={{ width: '280px' }}
            >
                <div className="flex flex-col h-full">
                    {/* 头部 */}
                    <div className="p-5 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                        <h2 className="text-lg font-semibold text-gray-800">历史会话</h2>
                        <button
                            onClick={toggleSidebar}
                            className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-all"
                        >
                            <i className="fa fa-times"></i>
                        </button>
                    </div>

                    {/* 新建对话按钮 */}
                    <div className="p-4">
                        <button
                            onClick={handleNewChat}
                            className="w-full py-2.5 px-4 bg-white text-gray-700 border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all flex items-center justify-center gap-2 shadow-sm hover:shadow active:scale-[0.98]"
                        >
                            <i className="fa fa-plus text-primary"></i>
                            <span className="font-medium">新建对话</span>
                        </button>
                    </div>

                    {/* 会话列表 */}
                    <div className="flex-1 overflow-y-auto scrollbar-thin p-3 space-y-1">
                        {isLoading ? (
                            <div className="flex flex-col items-center justify-center py-10 text-gray-400 gap-2">
                                <i className="fa fa-circle-o-notch fa-spin text-xl"></i>
                                <span className="text-sm">加载中...</span>
                            </div>
                        ) : conversations.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-12 text-gray-400 gap-3">
                                <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
                                    <i className="fa fa-comments-o text-xl"></i>
                                </div>
                                <p className="text-sm">暂无历史会话</p>
                            </div>
                        ) : (
                            conversations.map(conv => (
                                <div
                                    key={conv.conversation_id}
                                    onClick={() => handleSelectChat(conv.conversation_id)}
                                    className={`group relative p-3 rounded-xl cursor-pointer transition-all duration-200 border ${currentConversationId === conv.conversation_id
                                        ? 'bg-blue-50/80 text-primary border-blue-100 shadow-sm'
                                        : 'hover:bg-gray-50 text-gray-700 border-transparent hover:border-gray-100'
                                        }`}
                                >
                                    <div className="pr-8 truncate font-medium text-sm">
                                        {conv.title || '新会话'}
                                    </div>
                                    <div className="text-xs text-gray-400 mt-1.5 flex items-center gap-1">
                                        <i className="fa fa-clock-o text-[10px]"></i>
                                        {new Date(conv.updated_at).toLocaleDateString()} {new Date(conv.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>

                                    {/* 删除按钮 (悬停显示) */}
                                    <button
                                        onClick={(e) => handleDeleteChat(e, conv.conversation_id)}
                                        className="absolute right-2 top-1/2 transform -translate-y-1/2 w-7 h-7 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full opacity-0 group-hover:opacity-100 transition-all"
                                        title="删除会话"
                                    >
                                        <i className="fa fa-trash-o text-sm"></i>
                                    </button>
                                </div>
                            ))
                        )}
                    </div>

                    {/* 底部信息 */}
                    <div className="p-4 border-t border-gray-100 bg-gray-50/30">
                        <div className="flex items-center justify-center gap-2 text-xs text-gray-400">
                            <i className="fa fa-shield"></i>
                            <span>内容由 AI 生成，请仔细甄别</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* 遮罩层 (点击关闭) */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/10 backdrop-blur-[1px] z-30 transition-opacity duration-300"
                    onClick={toggleSidebar}
                ></div>
            )}
        </>
    )
}

export default ConversationSidebar
