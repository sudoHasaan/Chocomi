'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  parts: Array<{ type: 'text'; text: string }>
}

export interface Chat {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: number
  updatedAt: number
}

interface ChatContextType {
  chats: Chat[]
  activeChat: Chat | null
  createChat: () => Chat
  deleteChat: (id: string) => void
  setActiveChat: (id: string) => void
  updateChatMessages: (id: string, messages: ChatMessage[]) => void
  updateChatTitle: (id: string, title: string) => void
}

const ChatContext = createContext<ChatContextType | undefined>(undefined)

const areMessagesEqual = (a: ChatMessage[], b: ChatMessage[]) => {
  if (a === b) return true
  if (a.length !== b.length) return false

  // Compare serialized payloads to avoid unnecessary state writes.
  return JSON.stringify(a) === JSON.stringify(b)
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const [chats, setChats] = useState<Chat[]>([])
  const [activeChat, setActiveChatState] = useState<Chat | null>(null)
  const [isMounted, setIsMounted] = useState(false)

  // Initialize on mount
  useEffect(() => {
    const stored = localStorage.getItem('chats')
    let storedChats: Chat[] = []
    
    // Load chat history from localStorage
    if (stored) {
      try {
        storedChats = JSON.parse(stored) as Chat[]
      } catch (e) {
        console.error('Failed to parse stored chats:', e)
      }
    }
    
    // Always create a new fresh chat on page load
    const newChat = createNewChat()
    // Keep stored chats for history sidebar, but new chat is active
    const allChats = [newChat, ...storedChats]
    setChats(allChats)
    setActiveChatState(newChat)
    setIsMounted(true)
  }, [])

  // Save chats to localStorage whenever they change
  useEffect(() => {
    if (isMounted && chats.length > 0) {
      localStorage.setItem('chats', JSON.stringify(chats))
    }
  }, [chats, isMounted])

  const createNewChat = (): Chat => {
    const id = Date.now().toString()
    return {
      id,
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    }
  }

  const createChat = (): Chat => {
    const newChat = createNewChat()
    setChats((prev) => [newChat, ...prev])
    setActiveChatState(newChat)
    return newChat
  }

  const deleteChat = (id: string) => {
    setChats((prev) => prev.filter((chat) => chat.id !== id))
    if (activeChat?.id === id) {
      const remaining = chats.filter((chat) => chat.id !== id)
      if (remaining.length > 0) {
        setActiveChatState(remaining[0])
      } else {
        const newChat = createNewChat()
        setChats([newChat])
        setActiveChatState(newChat)
      }
    }
  }

  const setActiveChat = (id: string) => {
    const chat = chats.find((c) => c.id === id)
    if (chat) {
      setActiveChatState(chat)
    }
  }

  const updateChatMessages = (id: string, messages: ChatMessage[]) => {
    setChats((prev) => {
      let hasChanged = false

      const next = prev.map((chat) => {
        if (chat.id !== id) return chat
        if (areMessagesEqual(chat.messages, messages)) return chat

        hasChanged = true
        return { ...chat, messages, updatedAt: Date.now() }
      })

      return hasChanged ? next : prev
    })

    setActiveChatState((prev) => {
      if (!prev || prev.id !== id) return prev
      if (areMessagesEqual(prev.messages, messages)) return prev

      return { ...prev, messages, updatedAt: Date.now() }
    })
  }

  const updateChatTitle = (id: string, title: string) => {
    setChats((prev) =>
      prev.map((chat) =>
        chat.id === id ? { ...chat, title } : chat
      )
    )
    if (activeChat?.id === id) {
      setActiveChatState((prev) =>
        prev ? { ...prev, title } : null
      )
    }
  }

  return (
    <ChatContext.Provider
      value={{
        chats,
        activeChat: isMounted ? activeChat : null,
        createChat,
        deleteChat,
        setActiveChat,
        updateChatMessages,
        updateChatTitle,
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const context = useContext(ChatContext)
  if (context === undefined) {
    throw new Error('useChat must be used within ChatProvider')
  }
  return context
}
