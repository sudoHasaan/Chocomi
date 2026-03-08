'use client'

import Link from 'next/link'
import { useEffect, useMemo, useRef } from 'react'
import { useChat as useAIChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { Maximize2, MessageCircle, Plus, ShieldCheck, Trash2 } from 'lucide-react'
import { useChat as useStoredChats } from '@/context/chat-context'

type ChatMode = 'full' | 'widget'

interface SupportChatShellProps {
  mode: ChatMode
}

const quickPrompts = [
  'Do you have RTX 4060 in stock?',
  'What PSU do I need for this build?',
  'How do I return a faulty GPU?',
  'My PC does not POST. What should I check?',
]

function getMessageText(message: {
  parts?: Array<{ type: string; text?: string }>
}) {
  if (!message.parts) return ''
  return message.parts
    .filter((part): part is { type: 'text'; text: string } => part.type === 'text' && typeof part.text === 'string')
    .map((part) => part.text)
    .join('')
}

export function SupportChatShell({ mode }: SupportChatShellProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const {
    chats,
    activeChat,
    createChat,
    deleteChat,
    setActiveChat,
    updateChatMessages,
    updateChatTitle,
  } = useStoredChats()

  const { messages, sendMessage, status, setMessages } = useAIChat({
    id: activeChat?.id,
    messages: activeChat?.messages ?? [],
    transport: new DefaultChatTransport({ api: '/api/chat' }),
  })

  const isLoading = status === 'streaming' || status === 'submitted'
  const containerHeight = mode === 'full' ? 'min-h-[62dvh]' : 'h-[24rem]'

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!activeChat) return
    setMessages(activeChat.messages)
  }, [activeChat?.id, activeChat?.updatedAt, activeChat?.messages, setMessages])

  useEffect(() => {
    if (!activeChat) return

    updateChatMessages(activeChat.id, messages)

    if (activeChat.title !== 'New Chat') return
    const firstUserMessage = messages.find((message) => message.role === 'user')
    if (!firstUserMessage) return

    const nextTitle = getMessageText(firstUserMessage).trim()
    if (!nextTitle) return

    updateChatTitle(
      activeChat.id,
      nextTitle.length > 42 ? `${nextTitle.slice(0, 42).trimEnd()}...` : nextTitle
    )
  }, [messages, activeChat, updateChatMessages, updateChatTitle])

  const promptCards = useMemo(
    () =>
      quickPrompts.map((prompt) => (
        <button
          key={prompt}
          type="button"
          onClick={() => {
            if (!activeChat || isLoading) return
            sendMessage({ text: prompt })
          }}
          className="rounded-xl border border-border/80 bg-card px-3 py-2 text-left text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
        >
          {prompt}
        </button>
      )),
    [activeChat, isLoading, sendMessage]
  )

  if (!activeChat) {
    return (
      <section className="flex h-full min-h-[24rem] items-center justify-center rounded-2xl border border-border/70 bg-background/95 text-sm text-muted-foreground">
        Preparing chat...
      </section>
    )
  }

  const isFullMode = mode === 'full'

  return (
    <section className="flex h-full overflow-hidden rounded-2xl border border-border/70 bg-background/95 backdrop-blur">
      {isFullMode ? (
        <aside className="hidden w-72 flex-col border-r border-border/70 bg-card/40 lg:flex">
          <div className="border-b border-border/70 p-3">
            <button
              type="button"
              onClick={createChat}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
            >
              <Plus className="h-4 w-4" />
              New Chat
            </button>
          </div>
          <div className="flex-1 space-y-1 overflow-y-auto p-2">
            {chats.map((chat) => (
              <button
                key={chat.id}
                type="button"
                onClick={() => setActiveChat(chat.id)}
                className={`group flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                  activeChat.id === chat.id
                    ? 'bg-primary/12 text-foreground'
                    : 'text-muted-foreground hover:bg-muted/70 hover:text-foreground'
                }`}
              >
                <span className="truncate">{chat.title}</span>
                {chats.length > 1 ? (
                  <span
                    role="button"
                    tabIndex={0}
                    onClick={(event) => {
                      event.stopPropagation()
                      deleteChat(chat.id)
                    }}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        event.stopPropagation()
                        deleteChat(chat.id)
                      }
                    }}
                    className="rounded p-1 text-muted-foreground opacity-0 transition hover:bg-muted group-hover:opacity-100"
                    aria-label={`Delete ${chat.title}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </span>
                ) : null}
              </button>
            ))}
          </div>
        </aside>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border/70 px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/15 text-primary">
              <ShieldCheck className="h-5 w-5" />
            </span>
            <div>
              <h3 className="text-sm font-semibold">Chocomi Assistant</h3>
              <p className="text-xs text-muted-foreground">Live support for hardware, builds, and returns</p>
            </div>
          </div>
          {mode === 'widget' ? (
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 rounded-lg border border-border/70 px-2.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              <Maximize2 className="h-3.5 w-3.5" />
              Expand
            </Link>
          ) : (
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-lg border border-border/70 px-2.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              <MessageCircle className="h-3.5 w-3.5" />
              Back to Store
            </Link>
          )}
        </header>

        <div className={`flex-1 overflow-y-auto px-4 py-4 ${containerHeight}`}>
          {messages.length === 0 ? (
            <div className="space-y-4">
              <div className="rounded-xl border border-dashed border-border bg-muted/30 p-4">
                <p className="text-sm font-medium">Ask Chocomi anything about ByteBodega</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Product availability, pricing, compatibility, warranties, and troubleshooting.
                </p>
              </div>
              <div className="grid gap-2">{promptCards}</div>
            </div>
          ) : (
            <div className="space-y-3">
              {messages.map((message) => {
                const user = message.role === 'user'
                const text = getMessageText(message)
                return (
                  <article
                    key={message.id}
                    className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-relaxed ${
                      user
                        ? 'ml-auto bg-primary text-primary-foreground'
                        : 'border border-border/70 bg-card text-foreground'
                    }`}
                  >
                    {text}
                  </article>
                )
              })}
              {isLoading ? (
                <div className="inline-flex items-center gap-1 rounded-xl border border-border/70 bg-card px-3 py-2">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground" />
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:120ms]" />
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted-foreground [animation-delay:240ms]" />
                </div>
              ) : null}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <form
          onSubmit={(event) => {
            event.preventDefault()
            const form = event.currentTarget
            const input = form.elements.namedItem('message') as HTMLInputElement | null
            const value = input?.value?.trim() ?? ''
            if (!value || isLoading) return
            sendMessage({ text: value })
            if (input) input.value = ''
          }}
          className="border-t border-border/70 p-3"
        >
          <div className="flex items-center gap-2">
            <input
              name="message"
              type="text"
              disabled={isLoading}
              placeholder="Ask about stock, pricing, returns..."
              className="h-10 flex-1 rounded-xl border border-border/70 bg-background px-3 text-sm outline-none transition-colors focus:border-primary"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="h-10 rounded-xl bg-primary px-3 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </section>
  )
}
