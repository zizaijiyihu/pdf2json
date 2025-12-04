import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { getReminders } from '../services/api'

// Fisher-Yates 洗牌算法
const shuffleArray = (array) => {
  const shuffled = [...array]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

// 常量
const CLOSED_REMINDERS_DURATION = 5 * 60 * 60 * 1000 // 5小时(毫秒)
const STORAGE_VERSION = 1 // 用于数据结构版本控制

const useStore = create(
  persist(
    (set, get) => ({
      // 聊天相关状态
      messages: [],
      chatHistory: [],
      isLoading: false,

      // 文档相关状态
      documents: [],
      isDocumentsLoading: false,

      // 指示相关状态
      instructions: [],
      isInstructionsLoading: false,

      // 提醒相关状态
      reminders: [],
      isRemindersLoading: false,
      closedReminders: {}, // 已关闭的提醒: { id: { closedAt: timestamp, expiresAt: timestamp } }

      // AI 分析队列状态
      analysisQueue: [], // 等待分析的提醒 ID 队列
      currentAnalyzingId: null, // 当前正在分析的提醒 ID
      analyzedIds: {}, // 已完成分析的提醒 ID: { [id]: true }

      // 轮播相关状态
      carouselQuestions: [
        '帮我看看AI资讯',
        '制定OKR需要注意什么',
        '管理者怎么做规划',
        '最近我团队谁比较辛苦',
        '如何办理北京市异地就医备案'
      ],
      carouselQueue: [], // 当前轮次的洗牌队列
      carouselIndex: 0, // 当前在队列中的位置
      currentCarouselQuestion: '', // 当前显示的问题

      // 上传相关状态
      uploadProgress: {
        isUploading: false,
        filename: '',
        progress: 0,
        stage: '',
        message: '',
        currentPage: 0,
        totalPages: 0
      },

      // 侧边栏状态
      isKnowledgeSidebarOpen: false,
      isInstructionSidebarOpen: false,
      isReminderSidebarOpen: false,
      isConversationSidebarOpen: false,
      isPdfViewerOpen: false,
      currentPdf: null, // { filename, owner, pageNumber }
      pdfOpenedFromKnowledge: false, // 标记PDF是否从知识文档列表打开

      // 会话相关状态
      conversations: [],
      currentConversationId: null,
      isConversationsLoading: false,

      // Actions - 聊天
      addMessage: (message) => set((state) => ({
        messages: [...state.messages, message]
      })),

      updateLastMessage: (content) => set((state) => {
        const messages = [...state.messages]
        if (messages.length > 0) {
          messages[messages.length - 1] = {
            ...messages[messages.length - 1],
            content
          }
        }
        return { messages }
      }),

      setMessages: (messages) => set({ messages }),

      setChatHistory: (history) => set({ chatHistory: history }),

      setIsLoading: (loading) => set({ isLoading: loading }),

      clearMessages: () => set({ messages: [], chatHistory: [] }),

      // Actions - 文档
      setDocuments: (documents) => set({ documents }),

      setIsDocumentsLoading: (loading) => set({ isDocumentsLoading: loading }),

      // Actions - 指示
      setInstructions: (instructions) => set({ instructions }),

      setIsInstructionsLoading: (loading) => set({ isInstructionsLoading: loading }),

      addInstruction: (instruction) => set((state) => ({
        instructions: [instruction, ...state.instructions]
      })),

      updateInstructionInList: (id, data) => set((state) => ({
        instructions: state.instructions.map(inst =>
          inst.id === id ? { ...inst, ...data } : inst
        )
      })),

      removeInstruction: (id) => set((state) => ({
        instructions: state.instructions.filter(inst => inst.id !== id)
      })),

      // Actions - 提醒
      setReminders: (reminders) => set({ reminders }),

      setIsRemindersLoading: (loading) => set({ isRemindersLoading: loading }),

      // 获取提醒列表(不缓存,每次都重新获取)
      fetchReminders: async () => {
        set({ isRemindersLoading: true })
        try {
          const response = await getReminders()
          const reminders = response.data || []
          set({
            reminders,
            isRemindersLoading: false
          })
          return reminders
        } catch (error) {
          console.error('Failed to fetch reminders:', error)
          set({ isRemindersLoading: false })
          throw error
        }
      },

      // 获取可见的提醒(过滤已关闭且未过期的)
      getVisibleReminders: () => {
        const state = get()
        const now = Date.now()

        // 清理过期的关闭记录
        const validClosedReminders = {}
        Object.entries(state.closedReminders).forEach(([id, record]) => {
          if (record.expiresAt > now) {
            validClosedReminders[id] = record
          }
        })

        // 如果有过期的,更新 store
        if (Object.keys(validClosedReminders).length !== Object.keys(state.closedReminders).length) {
          set({ closedReminders: validClosedReminders })
        }

        return state.reminders.filter(r => !validClosedReminders[r.id])
      },

      addReminder: (reminder) => set((state) => ({
        reminders: [reminder, ...state.reminders]
      })),

      updateReminderInList: (id, data) => set((state) => ({
        reminders: state.reminders.map(reminder =>
          reminder.id === id ? { ...reminder, ...data } : reminder
        )
      })),

      removeReminder: (id) => set((state) => ({
        reminders: state.reminders.filter(reminder => reminder.id !== id)
      })),

      closeReminder: (id) => set((state) => {
        const now = Date.now()
        return {
          closedReminders: {
            ...state.closedReminders,
            [id]: {
              closedAt: now,
              expiresAt: now + CLOSED_REMINDERS_DURATION
            }
          }
        }
      }),

      // 清空所有已关闭的提醒记录（用于刷新）
      clearClosedReminders: () => set({ closedReminders: {} }),

      // AI 分析队列管理
      // 添加到分析队列
      addToAnalysisQueue: (reminderId) => {
        const state = get()
        // 如果已经在队列中或已分析，不重复添加
        if (state.analysisQueue.includes(reminderId) || state.analyzedIds[reminderId]) {
          return
        }

        const newQueue = [...state.analysisQueue, reminderId]
        set({ analysisQueue: newQueue })

        // 如果当前没有正在分析的，且新加入的是队列第一个，标记应该开始
        if (state.currentAnalyzingId === null && newQueue.length === 1) {
          console.log('🎬 队列空闲，可以开始第一个:', reminderId)
        }
      },

      // 开始分析某个提醒
      startAnalyzing: (reminderId) => set((state) => ({
        currentAnalyzingId: reminderId,
        analysisQueue: state.analysisQueue.filter(id => id !== reminderId)
      })),

      // 完成分析
      finishAnalyzing: (reminderId) => set((state) => ({
        currentAnalyzingId: null,
        analyzedIds: { ...state.analyzedIds, [reminderId]: true }
      })),

      // 标记为已分析 (用于缓存命中或外部完成的情况)
      markAnalyzed: (reminderId) => set((state) => ({
        analyzedIds: { ...state.analyzedIds, [reminderId]: true }
      })),

      // 获取下一个待分析的提醒 ID
      getNextReminderId: () => {
        const state = get()
        return state.analysisQueue[0] || null
      },

      // 重置分析队列（刷新时使用）
      resetAnalysisQueue: () => set({
        analysisQueue: [],
        currentAnalyzingId: null,
        analyzedIds: {}
      }),

      addDocument: (document) => set((state) => ({
        documents: [document, ...state.documents]
      })),

      removeDocument: (filename, owner) => set((state) => ({
        documents: state.documents.filter(
          doc => !(doc.filename === filename && doc.owner === owner)
        )
      })),

      updateDocumentVisibility: (filename, owner, isPublic) => set((state) => ({
        documents: state.documents.map(doc =>
          (doc.filename === filename && doc.owner === owner)
            ? { ...doc, is_public: isPublic }
            : doc
        )
      })),

      // Actions - 上传
      setUploadProgress: (progress) => set((state) => ({
        uploadProgress: { ...state.uploadProgress, ...progress }
      })),

      resetUploadProgress: () => set({
        uploadProgress: {
          isUploading: false,
          filename: '',
          progress: 0,
          stage: '',
          message: '',
          currentPage: 0,
          totalPages: 0
        }
      }),

      // Actions - 侧边栏
      toggleKnowledgeSidebar: () => set((state) => ({
        isKnowledgeSidebarOpen: !state.isKnowledgeSidebarOpen,
        isInstructionSidebarOpen: false, // 互斥
        isReminderSidebarOpen: false // 互斥
      })),

      setKnowledgeSidebarOpen: (open) => set({ isKnowledgeSidebarOpen: open }),

      toggleInstructionSidebar: () => set((state) => ({
        isInstructionSidebarOpen: !state.isInstructionSidebarOpen,
        isKnowledgeSidebarOpen: false, // 互斥
        isReminderSidebarOpen: false // 互斥
      })),

      setInstructionSidebarOpen: (open) => set({ isInstructionSidebarOpen: open }),

      toggleReminderSidebar: () => set((state) => ({
        isReminderSidebarOpen: !state.isReminderSidebarOpen,
        isKnowledgeSidebarOpen: false, // 互斥
        isInstructionSidebarOpen: false // 互斥
      })),

      setReminderSidebarOpen: (open) => set({ isReminderSidebarOpen: open }),

      toggleConversationSidebar: () => set((state) => ({
        isConversationSidebarOpen: !state.isConversationSidebarOpen,
        isKnowledgeSidebarOpen: false, // 互斥
        isInstructionSidebarOpen: false, // 互斥
        isReminderSidebarOpen: false // 互斥
      })),

      setConversationSidebarOpen: (open) => set({ isConversationSidebarOpen: open }),

      // Actions - 会话
      setConversations: (conversations) => set({ conversations }),

      setCurrentConversationId: (id) => set({ currentConversationId: id }),

      setIsConversationsLoading: (loading) => set({ isConversationsLoading: loading }),

      addConversation: (conversation) => set((state) => ({
        conversations: [conversation, ...state.conversations]
      })),

      updateConversationInList: (id, data) => set((state) => ({
        conversations: state.conversations.map(conv =>
          conv.conversation_id === id ? { ...conv, ...data } : conv
        )
      })),

      removeConversation: (id) => set((state) => ({
        conversations: state.conversations.filter(conv => conv.conversation_id !== id),
        // 如果删除的是当前会话，清空当前会话ID
        currentConversationId: state.currentConversationId === id ? null : state.currentConversationId
      })),

      // Actions - PDF浏览器
      openPdfViewer: (pdfInfo, fromKnowledge = false) => set({
        isPdfViewerOpen: true,
        currentPdf: pdfInfo,
        pdfOpenedFromKnowledge: fromKnowledge,
        // 如果从知识文档列表打开，先关闭知识文档列表
        isKnowledgeSidebarOpen: fromKnowledge ? false : get().isKnowledgeSidebarOpen
      }),

      closePdfViewer: () => set((state) => ({
        isPdfViewerOpen: false,
        currentPdf: null,
        // 如果是从知识文档列表打开的，关闭PDF时重新打开知识文档列表
        isKnowledgeSidebarOpen: state.pdfOpenedFromKnowledge ? true : state.isKnowledgeSidebarOpen,
        pdfOpenedFromKnowledge: false
      })),

      setPdfPage: (pageNumber) => set((state) => ({
        currentPdf: state.currentPdf ? { ...state.currentPdf, pageNumber } : null
      })),

      // Actions - 轮播
      initCarousel: () => {
        const state = get()
        const shuffled = shuffleArray(state.carouselQuestions)
        set({
          carouselQueue: shuffled,
          carouselIndex: 0,
          currentCarouselQuestion: shuffled[0]
        })
      },

      nextCarouselQuestion: () => {
        const state = get()
        const nextIndex = state.carouselIndex + 1

        // 如果到达当前轮次的末尾，重新洗牌开始新一轮
        if (nextIndex >= state.carouselQueue.length) {
          const shuffled = shuffleArray(state.carouselQuestions)
          set({
            carouselQueue: shuffled,
            carouselIndex: 0,
            currentCarouselQuestion: shuffled[0]
          })
        } else {
          set({
            carouselIndex: nextIndex,
            currentCarouselQuestion: state.carouselQueue[nextIndex]
          })
        }
      }

    }),
    {
      name: 'km-agent-storage', // localStorage key
      version: STORAGE_VERSION,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // 只持久化关闭记录(带时间戳)
        closedReminders: state.closedReminders,

        // 持久化其他需要的数据
        currentConversationId: state.currentConversationId,
      }),
    }
  )
)

export default useStore
