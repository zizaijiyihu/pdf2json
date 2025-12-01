import React, { useEffect, useState } from 'react'
import useStore from '../store/useStore'
import { getReminders, createReminder } from '../services/api'
import ReminderItem from './ReminderItem'

function ReminderSidebar() {
    const isOpen = useStore(state => state.isReminderSidebarOpen)
    const setReminderSidebarOpen = useStore(state => state.setReminderSidebarOpen)
    const reminders = useStore(state => state.reminders)
    const setReminders = useStore(state => state.setReminders)
    const addReminder = useStore(state => state.addReminder)

    const [isCreating, setIsCreating] = useState(false)
    const [newContent, setNewContent] = useState('')
    const [isSaving, setIsSaving] = useState(false)

    // 加载提醒列表
    useEffect(() => {
        if (isOpen && reminders.length === 0) {
            loadReminders()
        }
    }, [isOpen])

    const loadReminders = async () => {
        try {
            const response = await getReminders()
            setReminders(response.data || [])
        } catch (error) {
            console.error('Failed to load reminders:', error)
        }
    }

    const handleCreate = async () => {
        if (!newContent.trim() || isSaving) return

        setIsSaving(true)
        try {
            const result = await createReminder(newContent)
            if (result.success) {
                const newReminder = {
                    id: result.reminder_id,
                    content: newContent,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                }
                addReminder(newReminder)
                setNewContent('')
                setIsCreating(false)
            }
        } catch (error) {
            console.error('Failed to create reminder:', error)
            alert('创建失败: ' + error.message)
        } finally {
            setIsSaving(false)
        }
    }

    return (
        <div
            className={`${isOpen ? 'w-80 border-l border-gray-100' : 'w-0'
                } overflow-hidden transition-all duration-300 bg-white`}
        >
            <div className="w-80 h-[calc(100vh-200px)] my-[100px] p-6 overflow-y-auto scrollbar-thin">
                {/* 头部 */}
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-semibold text-gray-800">我的提醒</h2>
                    <button
                        onClick={() => setReminderSidebarOpen(false)}
                        className="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-700 rounded-full transition-colors"
                    >
                        <i className="fa fa-times" aria-hidden="true"></i>
                    </button>
                </div>

                {/* 创建新提醒 */}
                <div className="mb-6">
                    {isCreating ? (
                        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                            <textarea
                                value={newContent}
                                onChange={(e) => setNewContent(e.target.value)}
                                placeholder="请输入提醒内容，例如：今天谁比较辛苦..."
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
                            className="w-full py-3 border-2 border-dashed border-gray-300/50 rounded-lg text-gray-500 hover:border-primary/50 hover:text-primary transition-colors flex items-center justify-center gap-2"
                        >
                            <i className="fa fa-plus"></i>
                            <span>新建提醒</span>
                        </button>
                    )}
                </div>

                {/* 提醒列表 */}
                <div className="space-y-4">
                    {reminders.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                            <i className="fa fa-bell-o text-4xl mb-2" aria-hidden="true"></i>
                            <p className="text-sm">暂无提醒</p>
                        </div>
                    ) : (
                        reminders.map((reminder) => (
                            <ReminderItem key={reminder.id} reminder={reminder} />
                        ))
                    )}
                </div>
            </div>
        </div>
    )
}

export default ReminderSidebar
