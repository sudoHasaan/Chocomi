'use client'

import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useEffect, useRef } from 'react'
import { ChatMessage } from '@/components/chat-message'
import { ChatInput } from '@/components/chat-input'
import { ThemeToggle } from '@/components/theme-toggle'
import { MessageCircle } from 'lucide-react'

export default function ChatPage() {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({ api: '/api/chat' }),
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = (text: string) => {
    sendMessage({ text })
  }

  const isLoading = status === 'streaming' || status === 'submitted'

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-background via-background to-background">
      {/* Header */}
      <div className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="flex items-center justify-between px-6 py-4 max-w-4xl mx-auto w-full">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <MessageCircle className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-foreground">Chocomi</h1>
              <p className="text-sm text-muted-foreground">
                {messages.length === 0
                  ? 'Chat with our support team'
                  : 'Customer support assistant'}
              </p>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto w-full px-6 py-8">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center py-16">
              <div className="p-4 rounded-full bg-primary/10 mb-4">
                <MessageCircle className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-2xl font-semibold text-foreground mb-2">
                Hi, I'm Chocomi
              </h2>
              <p className="text-muted-foreground max-w-md">
                I'm here to help with any questions about our products or services. 
                Feel free to ask me anything!
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}

          {isLoading && messages.length > 0 && (
            <div className="flex gap-4 mb-6">
              <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0 bg-primary/20 text-primary">
                Co
              </div>
              <div className="flex-1 max-w-2xl px-4 py-3 rounded-lg bg-card border border-border rounded-bl-none">
                <div className="flex gap-2 items-center">
                  <div className="w-2 h-2 rounded-full bg-muted-foreground animate-pulse" />
                  <div className="w-2 h-2 rounded-full bg-muted-foreground animate-pulse delay-100" />
                  <div className="w-2 h-2 rounded-full bg-muted-foreground animate-pulse delay-200" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Container */}
      <ChatInput onSend={handleSendMessage} isLoading={isLoading} />
    </div>
  )
}
