export default function ChatLoading() {
  return (
    <div className="min-h-dvh bg-[radial-gradient(circle_at_top,rgba(196,52,35,0.15),transparent_45%),linear-gradient(180deg,var(--background),var(--background))] px-4 py-6 sm:px-8">
      <div className="mx-auto w-full max-w-5xl">
        <div className="mb-5 h-16 rounded-2xl border border-border/70 bg-background/70" />
        <div className="space-y-3 rounded-2xl border border-border/70 bg-background/70 p-4">
          <div className="h-12 w-2/3 animate-pulse rounded-xl bg-muted/70" />
          <div className="h-12 w-4/5 animate-pulse rounded-xl bg-muted/60" />
          <div className="h-12 w-1/2 animate-pulse rounded-xl bg-muted/70" />
          <div className="h-10 animate-pulse rounded-xl bg-muted/60" />
        </div>
      </div>
    </div>
  )
}
