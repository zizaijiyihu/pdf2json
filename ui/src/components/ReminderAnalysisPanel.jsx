import React, { useEffect, useState } from 'react'
import { getReminders } from '../services/api'
import ReminderAnalysisCard from './ReminderAnalysisCard'

function ReminderAnalysisPanel() {
    const [reminders, setReminders] = useState([])
    const [closedReminders, setClosedReminders] = useState(new Set())
    const [isLoading, setIsLoading] = useState(true)

    // 页面加载时获取所有提醒
    useEffect(() => {
        loadReminders()
    }, [])

    const loadReminders = async () => {
        setIsLoading(true)
        try {
            const response = await getReminders()
            setReminders(response.data || [])
        } catch (error) {
            console.error('Failed to load reminders:', error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleCloseReminder = (reminderId) => {
        setClosedReminders(prev => new Set([...prev, reminderId]))
    }

    // 过滤掉已关闭的提醒
    const visibleReminders = reminders.filter(r => !closedReminders.has(r.id))

    // 如果没有可见的提醒，不渲染面板
    if (!isLoading && visibleReminders.length === 0) {
        return null
    }

    return (
        <div
            className="fixed left-0 top-1/2 transform -translate-y-1/2 w-80 max-h-[80vh] overflow-y-auto scrollbar-thin bg-white/30 backdrop-blur-sm p-4 space-y-3 z-20"
            style={{
                borderTopRightRadius: '16px',
                borderBottomRightRadius: '16px'
            }}
        >
            {/* 标题 */}
            <div className="flex items-center justify-between mb-2 pb-2 border-b border-gray-50">
                <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <i className="fa fa-bell-o text-primary"></i>
                    <span>智能提醒</span>
                </h3>
                {isLoading && (
                    <i className="fa fa-circle-o-notch fa-spin text-xs text-gray-400"></i>
                )}
            </div>

            {/* 提醒卡片列表 */}
            {isLoading ? (
                <div className="flex flex-col items-center justify-center py-8 text-gray-400">
                    <i className="fa fa-circle-o-notch fa-spin text-xl mb-2"></i>
                    <span className="text-xs">加载中...</span>
                </div>
            ) : (
                visibleReminders.map(reminder => (
                    <ReminderAnalysisCard
                        key={reminder.id}
                        reminder={reminder}
                        onClose={handleCloseReminder}
                    />
                ))
            )}
        </div>
    )
}

export default ReminderAnalysisPanel
