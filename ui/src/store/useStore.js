import { create } from 'zustand'

const useStore = create((set, get) => ({
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
  isPdfViewerOpen: false,
  currentPdf: null, // { filename, owner, pageNumber }
  pdfOpenedFromKnowledge: false, // 标记PDF是否从知识文档列表打开

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
    isInstructionSidebarOpen: false // 互斥
  })),

  setKnowledgeSidebarOpen: (open) => set({ isKnowledgeSidebarOpen: open }),

  toggleInstructionSidebar: () => set((state) => ({
    isInstructionSidebarOpen: !state.isInstructionSidebarOpen,
    isKnowledgeSidebarOpen: false // 互斥
  })),

  setInstructionSidebarOpen: (open) => set({ isInstructionSidebarOpen: open }),

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
  }))
}))

export default useStore
