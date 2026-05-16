import { create } from 'zustand'

export interface CopilotMessage {
  id:            string
  role:          'user' | 'assistant'
  content:       string
  actions_taken: ActionRecord[]
  data:          any
  timestamp:     string
  loading?:      boolean
}

export interface ActionRecord {
  action:      string
  args?:       Record<string, any>
  result?:     string
  position_id?: number
}

interface CopilotStore {
  messages:  CopilotMessage[]
  loading:   boolean
  inputText: string

  addMessage:    (msg: CopilotMessage) => void
  updateMessage: (id: string, update: Partial<CopilotMessage>) => void
  setLoading:    (loading: boolean) => void
  setInputText:  (text: string) => void
  clearMessages: () => void
}

let msgCounter = 0
function genId() {
  return `msg_${Date.now()}_${++msgCounter}`
}

export const useCopilotStore = create<CopilotStore>((set) => ({
  messages:  [],
  loading:   false,
  inputText: '',

  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),

  updateMessage: (id, update) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, ...update } : m
      ),
    })),

  setLoading:    (loading)   => set({ loading }),
  setInputText:  (inputText) => set({ inputText }),
  clearMessages: () => set({ messages: [] }),
}))

export { genId }
