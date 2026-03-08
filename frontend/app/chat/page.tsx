import { ThemeToggle } from '@/components/theme-toggle'
import { SupportChatShell } from '@/components/support-chat-shell'

export default function ChatPage() {
  return (
    <div className="min-h-dvh bg-[radial-gradient(circle_at_top,rgba(196,52,35,0.15),transparent_45%),linear-gradient(180deg,var(--background),var(--background))] px-4 py-6 sm:px-8">
      <div className="mx-auto w-full max-w-5xl">
        <header className="mb-5 flex items-center justify-between rounded-2xl border border-border/70 bg-background/80 px-4 py-3 backdrop-blur">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">ByteBodega</p>
            <h1 className="text-lg font-semibold sm:text-xl">Support Assistant</h1>
          </div>
          <ThemeToggle />
        </header>

        <div className="h-[calc(100dvh-9.5rem)] min-h-[28rem] rounded-2xl shadow-xl">
          <SupportChatShell mode="full" />
        </div>
      </div>
    </div>
  )
}
