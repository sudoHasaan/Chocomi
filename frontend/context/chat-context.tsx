'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { UIMessage } from 'ai'

export interface Chat {
  id: string
  title: string
  messages: UIMessage[]
  createdAt: number
  updatedAt: number
}

interface ChatContextType {
  chats: Chat[]
  activeChat: Chat | null
  createChat: () => Chat
  deleteChat: (id: string) => void
  setActiveChat: (id: string) => void
  updateChatMessages: (id: string, messages: UIMessage[]) => void
  updateChatTitle: (id: string, title: string) => void
}

const ChatContext = createContext<ChatContextType | undefined>(undefined)

export function ChatProvider({ children }: { children: ReactNode }) {
  const [chats, setChats] = useState<Chat[]>([])
  const [activeChat, setActiveChatState] = useState<Chat | null>(null)
  const [isMounted, setIsMounted] = useState(false)

  // Initialize on mount
  useEffect(() => {
    const stored = localStorage.getItem('chats')
    if (stored) {
      try {
        const parsedChats = JSON.parse(stored) as Chat[]
        setChats(parsedChats)
        if (parsedChats.length > 0) {
          setActiveChatState(parsedChats[0])
        }
      } catch (e) {
        console.error('Failed to parse stored chats:', e)
        const newChat = createNewChat()
        setChats([newChat])
        setActiveChatState(newChat)
      }
    } else {
      const newChat = createNewChat()
      setChats([newChat])
      setActiveChatState(newChat)
    }
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

  const updateChatMessages = (id: string, messages: UIMessage[]) => {
    setChats((prev) =>
      prev.map((chat) =>
        chat.id === id
          ? { ...chat, messages, updatedAt: Date.now() }
          : chat
      )
    )
    if (activeChat?.id === id) {
      setActiveChatState((prev) =>
        prev ? { ...prev, messages, updatedAt: Date.now() } : null
      )
    }
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
