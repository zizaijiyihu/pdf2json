import React from 'react'
import ChatView from './components/ChatView'
import KnowledgeSidebar from './components/KnowledgeSidebar'
import InstructionSidebar from './components/InstructionSidebar'
import PdfViewer from './components/PdfViewer'
import ConversationSidebar from './components/ConversationSidebar'

function App() {
  return (
    <div className="bg-white min-h-screen flex items-center justify-center p-4">
      {/* 历史会话侧边栏 */}
      <ConversationSidebar />

      {/* 主容器 - 包含主视图、知识侧边栏和PDF浏览器 */}
      <div className="flex space-x-4">
        {/* 主聊天视图 */}
        <ChatView />

        {/* 知识文档侧边栏 */}
        <KnowledgeSidebar />

        {/* 指示侧边栏 */}
        <InstructionSidebar />

        {/* PDF浏览器 */}
        <PdfViewer />
      </div>
    </div>
  )
}

export default App
