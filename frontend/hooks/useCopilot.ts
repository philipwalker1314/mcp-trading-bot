'use client'

import { useCallback } from 'react'
import { useCopilotStore, CopilotMessage, genId } from '@/store/copilot'
import { api } from '@/lib/api'

export function useCopilot() {
  const {
    messages,
    loading,
    inputText,
    addMessage,
    updateMessage,
    setLoading,
    setInputText,
    clearMessages,
  } = useCopilotStore()

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || loading) return

    const userMsgId = genId()
    const userMsg: CopilotMessage = {
      id:            userMsgId,
      role:          'user',
      content:       text.trim(),
      actions_taken: [],
      data:          null,
      timestamp:     new Date().toISOString(),
    }
    addMessage(userMsg)
    setInputText('')
    setLoading(true)

    // Placeholder assistant message while waiting
    const asstMsgId = genId()
    const loadingMsg: CopilotMessage = {
      id:            asstMsgId,
      role:          'assistant',
      content:       '',
      actions_taken: [],
      data:          null,
      timestamp:     new Date().toISOString(),
      loading:       true,
    }
    addMessage(loadingMsg)

    // Build conversation history for context (exclude the loading placeholder)
    const history = messages
      .filter((m) => !m.loading)
      .map((m) => ({ role: m.role, content: m.content }))

    try {
      const res = await api.copilot.chat(text.trim(), history)
      const result = res.data

      updateMessage(asstMsgId, {
        content:       result?.response      ?? 'No response.',
        actions_taken: result?.actions_taken ?? [],
        data:          result?.data          ?? null,
        loading:       false,
      })
    } catch (e: any) {
      updateMessage(asstMsgId, {
        content: `Error: ${e.message ?? 'Request failed'}`,
        loading: false,
      })
    } finally {
      setLoading(false)
    }
  }, [messages, loading, addMessage, updateMessage, setLoading, setInputText])

  return {
    messages,
    loading,
    inputText,
    setInputText,
    sendMessage,
    clearMessages,
  }
}
