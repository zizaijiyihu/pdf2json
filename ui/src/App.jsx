import React, { useEffect } from 'react'
import useStore from './store/useStore'
import ReminderTilesPanel from './components/ReminderTilesPanel'
import ChatView from './components/ChatView'
import KnowledgeSidebar from './components/KnowledgeSidebar'
import InstructionSidebar from './components/InstructionSidebar'
import ReminderSidebar from './components/ReminderSidebar'
import PdfViewer from './components/PdfViewer'
import ConversationSidebar from './components/ConversationSidebar'
import ReminderAnalysisPanel from './components/ReminderAnalysisPanel'

function App() {
  const messages = useStore(state => state.messages)
  const fetchReminders = useStore(state => state.fetchReminders)
  const hasMessages = messages.length > 0

  // 初始化时获取提醒数据(带缓存判断)
  useEffect(() => {
    fetchReminders()
  }, [])

  return (
    <div className="bg-white min-h-screen flex items-center justify-center p-4">
      {/* 历史会话侧边栏 - 固定在左侧 */}
      <ConversationSidebar />

      {/* 提醒分析面板 - 固定在右侧，仅在聊天态显示 */}
      {hasMessages && <ReminderAnalysisPanel />}

      {/* 主容器 - 包含主视图、知识侧边栏、提醒侧边栏和PDF浏览器 */}
      <div className="flex space-x-4">
        {/* 主聊天视图区域 */}
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-2rem)]">
          {!hasMessages && <div className="flex-grow min-h-[25vh]"></div>}
          <div className="flex-shrink-0">
            <ChatView />
            {!hasMessages && (
              <ReminderTilesPanel />
            )}
          </div>
          {!hasMessages && <div className="flex-grow min-h-[15vh]"></div>}
        </div>

        {/* 知识文档侧边栏 */}
        <KnowledgeSidebar />

        {/* 指示侧边栏 */}
        <InstructionSidebar />

        {/* 提醒侧边栏 */}
        <ReminderSidebar />

        {/* PDF浏览器 */}
        <PdfViewer />
      </div>
    </div>
  )
}

export default App
