'use client'

import Link from 'next/link'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Maximize2, MessageCircle, Mic, MicOff, PanelLeft, Plus, ShieldCheck, Trash2, Volume2, X } from 'lucide-react'
import { useChat as useStoredChats } from '@/context/chat-context'
import type { ChatMessage } from '@/context/chat-context'
import { useVoiceRecorder } from '@/hooks/use-voice-recorder'

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
  const scrollContainerRef = useRef<HTMLDivElement>(null)
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

  const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000/ws/chat'

  const wsRef = useRef<WebSocket | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>(activeChat?.messages ?? [])
  const [isLoading, setIsLoading] = useState(false)
  const [isSocketReady, setIsSocketReady] = useState(false)
  const [messageInput, setMessageInput] = useState('')
  const [socketSession, setSocketSession] = useState(0)
  const [stickToBottom, setStickToBottom] = useState(true)
  const [isMobileHistoryOpen, setIsMobileHistoryOpen] = useState(false)
  // Buffer incoming tokens and flush to state in batches to reduce re-renders
  const tokenBufferRef = useRef('')
  const flushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const { isRecording, startRecording, stopRecording } = useVoiceRecorder()

  const handleScroll = useCallback(() => {
    const node = scrollContainerRef.current
    if (!node) return

    const threshold = 96
    const distanceToBottom = node.scrollHeight - node.scrollTop - node.clientHeight
    setStickToBottom(distanceToBottom <= threshold)
  }, [])

  const flushTokenBuffer = useCallback(() => {
    if (!tokenBufferRef.current) return
    const buffered = tokenBufferRef.current
    tokenBufferRef.current = ''
    setMessages((prev) => {
      const last = prev[prev.length - 1]
      if (last?.role === 'assistant') {
        return [
          ...prev.slice(0, -1),
          { ...last, parts: [{ type: 'text' as const, text: last.parts[0].text + buffered }] },
        ]
      }
      return [...prev, { id: Date.now().toString(), role: 'assistant' as const, parts: [{ type: 'text' as const, text: buffered }] }]
    })
  }, [])

  // Reconnect WebSocket when active chat changes (new session per chat)
  useEffect(() => {
    if (!activeChat) return
    setMessages(activeChat.messages)
    setIsSocketReady(false)

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws
    ws.onopen = () => setIsSocketReady(true)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as { type: string; content?: string; message?: string }
      if (data.type === 'token') {
        tokenBufferRef.current += data.content ?? ''
        if (flushTimerRef.current) clearTimeout(flushTimerRef.current)
        flushTimerRef.current = setTimeout(flushTokenBuffer, 30)
      } else if (data.type === 'transcript') {
        // Replace or update the last user message with the transcript
        setMessages((prev) => {
          const last = prev[prev.length - 1]
          if (last?.role === 'user') {
            return [
              ...prev.slice(0, -1),
              { ...last, parts: [{ type: 'text' as const, text: data.content ?? '' }] },
            ]
          }
          return prev
        })
      } else if (data.type === 'audio') {
        // Play the received audio bytes
        if (data.content) {
          const audioBlob = new Blob([Uint8Array.from(atob(data.content), (c) => c.charCodeAt(0))], { type: 'audio/wav' })
          const url = URL.createObjectURL(audioBlob)
          if (audioRef.current) {
            audioRef.current.src = url
            audioRef.current.play().catch(console.error)
          } else {
            const audio = new Audio(url)
            audioRef.current = audio
            audio.play().catch(console.error)
          }
        }
      } else if (data.type === 'done') {
        if (flushTimerRef.current) clearTimeout(flushTimerRef.current)
        flushTokenBuffer()
        setIsLoading(false)
      } else if (data.type === 'error') {
        setIsLoading(false)
      }
    }

    ws.onerror = () => {
      setIsSocketReady(false)
      setIsLoading(false)
    }
    ws.onclose = () => setIsSocketReady(false)

    return () => {
      if (flushTimerRef.current) clearTimeout(flushTimerRef.current)
      ws.close()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeChat?.id, socketSession])

  // Scroll only if user is near the bottom. Avoid locking the viewport while streaming.
  useEffect(() => {
    if (!stickToBottom) return
    bottomRef.current?.scrollIntoView({ behavior: isLoading ? 'auto' : 'smooth', block: 'end' })
  }, [messages, stickToBottom, isLoading])

  // Sync messages to context and auto-generate title
  useEffect(() => {
    if (!activeChat) return
    updateChatMessages(activeChat.id, messages)

    if (activeChat.title !== 'New Chat') return
    const firstUserMessage = messages.find((message) => message.role === 'user')
    if (!firstUserMessage) return
    const nextTitle = getMessageText(firstUserMessage).trim()
    if (!nextTitle) return
    updateChatTitle(activeChat.id, nextTitle.length > 42 ? `${nextTitle.slice(0, 42).trimEnd()}...` : nextTitle)
  }, [messages, activeChat, updateChatMessages, updateChatTitle])

  useEffect(() => {
    setIsMobileHistoryOpen(false)
  }, [activeChat?.id])

  const sendMessage = useCallback(
    ({ text }: { text: string }) => {
      if (!text.trim() || isLoading || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
      const userMsg: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        parts: [{ type: 'text', text }],
      }
      setStickToBottom(true)
      setMessages((prev) => [...prev, userMsg])
      setIsLoading(true)
      wsRef.current.send(JSON.stringify({ type: 'text', message: text }))
    },
    [isLoading]
  )

  const sendVoiceMessage = useCallback(
    async (audioBlob: Blob) => {
      if (isLoading || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
      
      const userMsg: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        parts: [{ type: 'text', text: '...' }], // Placeholder until transcript arrives
      }
      setStickToBottom(true)
      setMessages((prev) => [...prev, userMsg])
      setIsLoading(true)

      const reader = new FileReader()
      reader.onloadend = () => {
        const base64Audio = (reader.result as string).split(',')[1]
        wsRef.current?.send(JSON.stringify({ type: 'voice', audio: base64Audio }))
      }
      reader.readAsDataURL(audioBlob)
    },
    [isLoading]
  )

  const handleMicClick = useCallback(async () => {
    if (isRecording) {
      const blob = await stopRecording()
      if (blob) {
        sendVoiceMessage(blob)
      }
    } else {
      await startRecording()
    }
  }, [isRecording, startRecording, stopRecording, sendVoiceMessage])

  const cancelStreaming = useCallback(() => {
    if (!isLoading) return
    if (flushTimerRef.current) clearTimeout(flushTimerRef.current)
    flushTokenBuffer()
    setIsLoading(false)
    wsRef.current?.close(4000, 'cancelled-by-user')
    setSocketSession((prev) => prev + 1)
  }, [flushTokenBuffer, isLoading])

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
    <section className="flex h-full min-h-0 overflow-hidden rounded-2xl border border-border/70 bg-background/95 backdrop-blur">
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

      <div className="relative flex min-w-0 min-h-0 flex-1 flex-col">
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
          <div className="flex items-center gap-2">
            {isFullMode ? (
              <button
                type="button"
                onClick={() => setIsMobileHistoryOpen(true)}
                className="inline-flex items-center gap-2 rounded-lg border border-border/70 px-2.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground lg:hidden"
              >
                <PanelLeft className="h-3.5 w-3.5" />
                History
              </button>
            ) : null}

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
          </div>
        </header>

        {isFullMode && isMobileHistoryOpen ? (
          <div className="absolute inset-0 z-40 flex lg:hidden" role="dialog" aria-modal="true" aria-label="Chat history">
            <button
              type="button"
              onClick={() => setIsMobileHistoryOpen(false)}
              className="flex-1 bg-black/45"
              aria-label="Close chat history"
            />
            <aside className="flex h-full w-[min(82vw,20rem)] flex-col border-l border-border/70 bg-background shadow-2xl">
              <div className="flex items-center justify-between border-b border-border/70 p-3">
                <p className="text-sm font-semibold">Chat history</p>
                <button
                  type="button"
                  onClick={() => setIsMobileHistoryOpen(false)}
                  className="inline-flex items-center justify-center rounded-md border border-border/70 p-1.5 text-muted-foreground transition-colors hover:text-foreground"
                  aria-label="Close history panel"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

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
                    onClick={() => {
                      setActiveChat(chat.id)
                      setIsMobileHistoryOpen(false)
                    }}
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
                        className="rounded p-1 text-muted-foreground opacity-100 transition hover:bg-muted"
                        aria-label={`Delete ${chat.title}`}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </span>
                    ) : null}
                  </button>
                ))}
              </div>
            </aside>
          </div>
        ) : null}

        <div
          ref={scrollContainerRef}
          onScroll={handleScroll}
          className="flex-1 min-h-0 overflow-y-auto px-4 py-4"
        >
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
                        : 'border border-border/70 bg-card text-foreground prose prose-sm dark:prose-invert max-w-none'
                    }`}
                  >
                    {user ? text : <ReactMarkdown>{text}</ReactMarkdown>}
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
            const value = messageInput.trim()
            if (!value || isLoading) return
            sendMessage({ text: value })
            setMessageInput('')
          }}
          className="border-t border-border/70 p-3"
        >
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleMicClick}
              disabled={isLoading && !isRecording}
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-border/70 bg-background transition-colors hover:bg-muted ${
                isRecording ? 'text-destructive bg-destructive/10 animate-pulse-red border-destructive/50' : 'text-muted-foreground'
              } disabled:cursor-not-allowed disabled:opacity-60`}
              title={isRecording ? 'Stop recording' : 'Start voice chat'}
            >
              {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
            </button>
            <input
              name="message"
              type="text"
              value={messageInput}
              onChange={(event) => setMessageInput(event.target.value)}
              placeholder={isRecording ? 'Listening...' : "Ask about stock, pricing, returns..."}
              disabled={isRecording}
              className="h-10 flex-1 rounded-xl border border-border/70 bg-background px-3 text-sm outline-none transition-colors focus:border-primary disabled:opacity-80"
            />
            {isLoading ? (
              <button
                type="button"
                onClick={cancelStreaming}
                className="h-10 rounded-xl border border-border/70 bg-background px-3 text-sm font-medium transition-colors hover:bg-muted font-sans"
              >
                Cancel
              </button>
            ) : (
              <button
                type="submit"
                disabled={!messageInput.trim() || !isSocketReady || isRecording}
                className="h-10 rounded-xl bg-primary px-3 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60 font-sans"
              >
                Send
              </button>
            )}
          </div>
        </form>
      </div>
    </section>
  )
}
