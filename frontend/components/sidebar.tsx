'use client'

import { useState } from 'react'
import { useChat } from '@/context/chat-context'
import { MessageCircle, Plus, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'

export function Sidebar() {
  const { chats, activeChat, createChat, deleteChat, setActiveChat } = useChat()
  const [isOpen, setIsOpen] = useState(true)

  const handleNewChat = () => {
    createChat()
  }

  const handleDeleteChat = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    deleteChat(id)
  }

  return (
    <>
      {/* Sidebar */}
      <aside
        className={`bg-sidebar border-r border-sidebar-border transition-all duration-300 ease-in-out flex flex-col ${
          isOpen ? 'w-64' : 'w-0'
        } overflow-hidden`}
      >
        {/* New Chat Button */}
        <div className="p-4 border-b border-sidebar-border">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-sidebar-primary text-sidebar-primary-foreground font-medium hover:bg-sidebar-primary/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-2 space-y-2">
            {chats.map((chat) => (
              <div
                key={chat.id}
                onClick={() => setActiveChat(chat.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    setActiveChat(chat.id)
                  }
                }}
                role="button"
                tabIndex={0}
                className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center justify-between group ${
                  activeChat?.id === chat.id
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'text-sidebar-foreground hover:bg-sidebar-accent/50'
                }`}
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <MessageCircle className="w-4 h-4 flex-shrink-0" />
                  <span className="text-sm truncate">{chat.title}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteChat(e, chat.id)}
                  type="button"
                  className="ml-2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-sidebar-accent/70 transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed left-0 top-1/2 -translate-y-1/2 z-40 p-2 rounded-r-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        aria-label={isOpen ? 'Close sidebar' : 'Open sidebar'}
      >
        {isOpen ? (
          <ChevronLeft className="w-5 h-5" />
        ) : (
          <ChevronRight className="w-5 h-5" />
        )}
      </button>
    </>
  )
}
