import React from 'react'
import ReminderTileCard from './ReminderTileCard'
import useStore from '../store/useStore'

function ReminderTilesPanel() {
    // 从 store 获取数据
    const reminders = useStore(state => state.reminders)
    const isLoading = useStore(state => state.isRemindersLoading)
    const closedReminders = useStore(state => state.closedReminders)
    const closeReminder = useStore(state => state.closeReminder)
    const analyzedIds = useStore(state => state.analyzedIds)

    // 过滤掉已关闭的提醒(检查过期时间)
    const now = Date.now()
    const visibleReminders = reminders.filter(r => {
        const closedRecord = closedReminders[r.id]
        // 如果没有关闭记录,或者已过期,则显示
        return !closedRecord || closedRecord.expiresAt <= now
    })

    // 计算哪些卡片可以开始分析
    // 规则：严格按照行顺序，第一行全部完成后，第二行才能开始
    // 每行2个
    const canAnalyzeMap = {}
    let foundActiveRow = false

    // 按每行2个分组
    const rows = []
    for (let i = 0; i < visibleReminders.length; i += 2) {
        rows.push(visibleReminders.slice(i, i + 2))
    }

    rows.forEach(row => {
        if (foundActiveRow) {
            // 前面已经有正在进行的行，当前行必须等待
            row.forEach(r => canAnalyzeMap[r.id] = false)
            return
        }

        // 检查当前行是否全部完成
        // 注意：我们需要检查 store 中的 analyzedIds，这是最准确的状态
        const isRowComplete = row.every(r => analyzedIds[r.id])

        if (isRowComplete) {
            // 当前行已完成，继续检查下一行
            // 标记为 false 也没关系，因为组件内部状态已经是 done
            row.forEach(r => canAnalyzeMap[r.id] = false)
        } else {
            // 当前行未完成，这就是"活动行"
            // 允许该行中所有未完成的卡片开始分析
            foundActiveRow = true
            row.forEach(r => canAnalyzeMap[r.id] = true)
        }
    })

    // 准备两列数据 (用于瀑布流布局)
    const leftReminders = []
    const rightReminders = []
    visibleReminders.forEach((r, index) => {
        if (index % 2 === 0) {
            leftReminders.push(r)
        } else {
            rightReminders.push(r)
        }
    })

    if (!isLoading && visibleReminders.length === 0) {
        return null
    }

    return (
        <div className="w-full max-w-[760px] mx-auto mt-12 px-2 animate-fade-in-up max-h-[600px] overflow-y-auto scrollbar-thin">
            <div className="flex items-center gap-2 mb-4 px-2 text-gray-500 sticky top-0 bg-white z-10 pb-2">
                <i className="fa fa-bell-o"></i>
                <span className="text-sm font-medium">智能提醒</span>
            </div>

            {isLoading ? (
                <div className="flex justify-center py-8">
                    <i className="fa fa-circle-o-notch fa-spin text-gray-400"></i>
                </div>
            ) : (
                <>
                    {/* 移动端单列布局 */}
                    <div className="flex flex-col gap-4 md:hidden pb-8">
                        {visibleReminders.map(reminder => (
                            <div key={reminder.id}>
                                <ReminderTileCard
                                    reminder={reminder}
                                    onClose={closeReminder}
                                    canAnalyze={canAnalyzeMap[reminder.id]}
                                />
                            </div>
                        ))}
                    </div>

                    {/* 桌面端双列瀑布流布局 */}
                    <div className="hidden md:flex gap-4 items-start pb-8">
                        {/* 左列 */}
                        <div className="flex-1 flex flex-col gap-4">
                            {leftReminders.map(reminder => (
                                <div key={reminder.id}>
                                    <ReminderTileCard
                                        reminder={reminder}
                                        onClose={closeReminder}
                                        canAnalyze={canAnalyzeMap[reminder.id]}
                                    />
                                </div>
                            ))}
                        </div>
                        {/* 右列 */}
                        <div className="flex-1 flex flex-col gap-4">
                            {rightReminders.map(reminder => (
                                <div key={reminder.id}>
                                    <ReminderTileCard
                                        reminder={reminder}
                                        onClose={closeReminder}
                                        canAnalyze={canAnalyzeMap[reminder.id]}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default ReminderTilesPanel
