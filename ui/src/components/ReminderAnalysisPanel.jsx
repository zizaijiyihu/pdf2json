import React from 'react'
import useStore from '../store/useStore'
import ReminderAnalysisCard from './ReminderAnalysisCard'

function ReminderAnalysisPanel() {
    // 从 store 获取数据
    const reminders = useStore(state => state.reminders)
    const isLoading = useStore(state => state.isRemindersLoading)
    const closedReminders = useStore(state => state.closedReminders)
    const closeReminder = useStore(state => state.closeReminder)

    // 过滤掉已关闭的提醒(检查过期时间)
    const now = Date.now()
    const visibleReminders = reminders.filter(r => {
        const closedRecord = closedReminders[r.id]
        // 如果没有关闭记录,或者已过期,则显示
        return !closedRecord || closedRecord.expiresAt <= now
    })

    // 如果没有可见的提醒，不渲染面板
    if (!isLoading && visibleReminders.length === 0) {
        return null
    }

    return (
        <div
            className="fixed right-0 top-1/2 transform -translate-y-1/2 w-80 max-h-[80vh] overflow-y-auto scrollbar-thin bg-white/30 backdrop-blur-sm p-4 space-y-3 z-20"
            style={{
                borderTopLeftRadius: '16px',
                borderBottomLeftRadius: '16px'
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
                        onClose={closeReminder}
                    />
                ))
            )}
        </div>
    )
}

export default ReminderAnalysisPanel
