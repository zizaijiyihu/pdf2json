import React, { useState, useEffect } from 'react'
import { getQuotes, createQuote, updateQuote, deleteQuote } from '../services/api'

function QuoteDisplay({ visible }) {
    const [currentQuote, setCurrentQuote] = useState(null)
    const [displayQuotes, setDisplayQuotes] = useState([]) // Store carousel quotes
    const [currentIndex, setCurrentIndex] = useState(0) // Current carousel index
    const [isTransitioning, setIsTransitioning] = useState(false) // Animation state
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [quotes, setQuotes] = useState([])
    const [loading, setLoading] = useState(false)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)

    // Form state
    const [editingId, setEditingId] = useState(null)
    const [editContent, setEditContent] = useState('')
    const [editIsFixed, setEditIsFixed] = useState(0)
    const [newContent, setNewContent] = useState('')
    const [newIsFixed, setNewIsFixed] = useState(0)
    const [deleteConfirmId, setDeleteConfirmId] = useState(null)

    // Fetch quotes for display carousel
    const fetchDisplayQuote = async () => {
        try {
            const data = await getQuotes(1, 20)
            if (data.items && data.items.length > 0) {
                const fixedQuote = data.items.find(q => q.is_fixed === 1)
                if (fixedQuote) {
                    // If there's a fixed quote, only show that one
                    setDisplayQuotes([fixedQuote])
                    setCurrentQuote(fixedQuote)
                } else {
                    // Use all quotes for carousel
                    setDisplayQuotes(data.items)
                    setCurrentQuote(data.items[0])
                }
            } else {
                const defaultQuote = { content: '创造知识   共享知识' }
                setDisplayQuotes([defaultQuote])
                setCurrentQuote(defaultQuote)
            }
        } catch (error) {
            console.error('Failed to fetch display quote:', error)
            const defaultQuote = { content: '创造知识   共享知识' }
            setDisplayQuotes([defaultQuote])
            setCurrentQuote(defaultQuote)
        }
    }

    useEffect(() => {
        fetchDisplayQuote()
    }, [])

    // Auto carousel effect (only if there are multiple quotes and no fixed quote)
    useEffect(() => {
        if (displayQuotes.length <= 1) return // Don't carousel for single quote or fixed quote

        const interval = setInterval(() => {
            setIsTransitioning(true)

            setTimeout(() => {
                setCurrentIndex((prevIndex) => {
                    const nextIndex = (prevIndex + 1) % displayQuotes.length
                    setCurrentQuote(displayQuotes[nextIndex])
                    return nextIndex
                })

                setTimeout(() => {
                    setIsTransitioning(false)
                }, 50) // Brief delay before fade in
            }, 700) // Fade out duration (matches duration-700)
        }, 10000) // Change every 10 seconds

        return () => clearInterval(interval)
    }, [displayQuotes])

    // Fetch list for management
    const fetchQuotesList = async (pageNum = 1) => {
        setLoading(true)
        try {
            const data = await getQuotes(pageNum, 10)
            setQuotes(data.items)
            setTotalPages(data.total_pages)
            setPage(data.page)
        } catch (error) {
            console.error('Failed to fetch quotes list:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (isModalOpen) {
            fetchQuotesList(page)
        }
    }, [isModalOpen, page])

    const handleAdd = async () => {
        if (!newContent.trim()) return
        try {
            await createQuote(newContent, 0)
            setNewContent('')
            setNewIsFixed(0)
            fetchQuotesList(page)
            fetchDisplayQuote() // Refresh display
        } catch (error) {
            console.error('Failed to create quote:', error)
        }
    }

    const handleUpdate = async (id) => {
        if (!editContent.trim()) return
        try {
            await updateQuote(id, editContent, editIsFixed)
            setEditingId(null)
            fetchQuotesList(page)
            fetchDisplayQuote() // Refresh display
        } catch (error) {
            console.error('Failed to update quote:', error)
        }
    }

    const handleDelete = async (id) => {
        try {
            await deleteQuote(id)
            setDeleteConfirmId(null)
            fetchQuotesList(page)
            fetchDisplayQuote() // Refresh display
        } catch (error) {
            console.error('Failed to delete quote:', error)
        }
    }

    const handleToggleFixed = async (quote) => {
        try {
            const newStatus = quote.is_fixed === 1 ? 0 : 1
            await updateQuote(quote.id, quote.content, newStatus)
            fetchQuotesList(page)
            fetchDisplayQuote()
        } catch (error) {
            console.error('Failed to toggle fixed status:', error)
        }
    }

    const startEdit = (quote) => {
        setEditingId(quote.id)
        setEditContent(quote.content)
        setEditIsFixed(quote.is_fixed)
    }

    const cancelEdit = () => {
        setEditingId(null)
        setEditContent('')
        setEditIsFixed(0)
    }

    return (
        <>
            {/* Display Area */}
            <div
                className={`relative group flex items-center mb-8 transition-opacity duration-800 ${visible ? 'opacity-100' : 'opacity-0'}`}
            >
                {/* Logo Component - Fixed size, centered content */}
                <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center mr-10">
                    <img
                        src="/images/logo.png"
                        alt="金山云"
                        className="w-full h-full object-contain"
                    />
                </div>

                {/* Quote Component - Centered content */}
                <div
                    className={`flex items-center justify-center text-2xl text-gray-800 font-medium transition-all ${isTransitioning
                            ? 'opacity-0 transform scale-95 duration-700'
                            : 'opacity-100 transform scale-100 duration-500'
                        }`}
                >
                    {currentQuote?.content || '创造知识   共享知识'}
                </div>

                {/* Edit Icon */}
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="absolute -right-8 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-gray-400 hover:text-primary p-2"
                    title="管理语录"
                >
                    <i className="fa fa-pencil" aria-hidden="true"></i>
                </button>
            </div>

            {/* Management Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-2xl w-[600px] max-h-[80vh] flex flex-col overflow-hidden">
                        {/* Header */}
                        <div className="flex items-center justify-between p-4 border-b border-gray-100">
                            <h3 className="text-lg font-semibold text-gray-800">语录管理</h3>
                            <button
                                onClick={() => setIsModalOpen(false)}
                                className="text-gray-400 hover:text-gray-600 transition-colors"
                            >
                                <i className="fa fa-times text-xl"></i>
                            </button>
                        </div>

                        {/* List */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                            {loading ? (
                                <div className="text-center py-8 text-gray-500">加载中...</div>
                            ) : (
                                quotes.map(quote => (
                                    <div key={quote.id} className="p-3 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors group">
                                        {editingId === quote.id ? (
                                            <div className="space-y-3">
                                                <textarea
                                                    value={editContent}
                                                    onChange={(e) => setEditContent(e.target.value)}
                                                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary/50 outline-none resize-none"
                                                    rows="2"
                                                />
                                                <div className="flex items-center justify-between">

                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={cancelEdit}
                                                            className="px-3 py-1 text-sm text-gray-500 hover:text-gray-700"
                                                        >
                                                            取消
                                                        </button>
                                                        <button
                                                            onClick={() => handleUpdate(quote.id)}
                                                            className="px-3 py-1 text-sm bg-primary text-white rounded-md hover:bg-primary/90"
                                                        >
                                                            保存
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex-1">
                                                    <div className="text-gray-800">{quote.content}</div>

                                                </div>
                                                <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        onClick={() => handleDelete(quote.id)}
                                                        className="text-gray-400 hover:text-red-500 p-1"
                                                        title="删除"
                                                    >
                                                        <i className="fa fa-trash"></i>
                                                    </button>
                                                    <button
                                                        onClick={() => startEdit(quote)}
                                                        className="text-gray-400 hover:text-primary p-1"
                                                        title="编辑"
                                                    >
                                                        <i className="fa fa-pencil"></i>
                                                    </button>
                                                    <button
                                                        onClick={() => handleToggleFixed(quote)}
                                                        className={`p-1 ${quote.is_fixed === 1 ? 'text-primary' : 'text-gray-400 hover:text-primary'}`}
                                                        title={quote.is_fixed === 1 ? "取消固定" : "设为固定"}
                                                    >
                                                        <i className="fa fa-thumb-tack"></i>
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <div className="flex justify-center gap-2 p-2 border-t border-gray-100 bg-gray-50">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    className="px-2 py-1 text-sm text-gray-600 disabled:opacity-50 hover:bg-gray-200 rounded"
                                >
                                    上一页
                                </button>
                                <span className="text-sm text-gray-500 self-center">{page} / {totalPages}</span>
                                <button
                                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                    disabled={page === totalPages}
                                    className="px-2 py-1 text-sm text-gray-600 disabled:opacity-50 hover:bg-gray-200 rounded"
                                >
                                    下一页
                                </button>
                            </div>
                        )}

                        {/* Add New */}
                        <div className="p-4 border-t border-gray-100 bg-gray-50">
                            <div className="space-y-3">
                                <textarea
                                    value={newContent}
                                    onChange={(e) => setNewContent(e.target.value)}
                                    placeholder="添加新语录..."
                                    className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary/50 outline-none resize-none bg-white"
                                    rows="2"
                                />
                                <div className="flex items-center justify-between">

                                    <button
                                        onClick={handleAdd}
                                        disabled={!newContent.trim()}
                                        className="px-4 py-1.5 bg-primary text-white rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    >
                                        添加
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}

export default QuoteDisplay
