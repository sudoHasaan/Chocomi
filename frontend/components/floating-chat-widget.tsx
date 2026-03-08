'use client'

import { useState } from 'react'
import { MessageCircle, X } from 'lucide-react'
import { SupportChatShell } from '@/components/support-chat-shell'

export function FloatingChatWidget() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="fixed bottom-4 right-4 z-50 sm:bottom-6 sm:right-6">
      {isOpen ? (
        <div className="relative h-[min(78dvh,36rem)] w-[min(92vw,24rem)] overflow-hidden rounded-2xl shadow-2xl ring-1 ring-black/5">
          <SupportChatShell mode="widget" />
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="absolute right-3 top-3 grid h-7 w-7 place-items-center rounded-lg border border-border/70 bg-background/90 text-muted-foreground transition-colors hover:text-foreground"
            aria-label="Close chat widget"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="group inline-flex items-center gap-2 rounded-full bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-lg transition-transform hover:-translate-y-0.5"
          aria-label="Open support chat"
        >
          <MessageCircle className="h-4 w-4 transition-transform group-hover:scale-110" />
          Chat with TechShop
        </button>
      )}
    </div>
  )
}
