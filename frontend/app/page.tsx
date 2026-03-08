import Link from 'next/link'
import {
  BadgeCheck,
  Cpu,
  LifeBuoy,
  MapPin,
  Phone,
  Shield,
  ShoppingCart,
  Store,
  Wrench,
} from 'lucide-react'
import { ThemeToggle } from '@/components/theme-toggle'
import { FloatingChatWidget } from '@/components/floating-chat-widget'
import { ChatRoutePrefetch } from '@/components/chat-route-prefetch'

const capabilities = [
  {
    title: 'Product Inquiries',
    description:
      'Check stock and pricing for GPUs, CPUs, RAM, SSDs, motherboards, and accessories instantly.',
    validation:
      'Try: "Do you have RTX 4060 or RX 7700 XT in stock under $400?"',
    icon: ShoppingCart,
  },
  {
    title: 'PC Build Advice',
    description:
      'Get guidance on compatibility, power requirements, cooling, and upgrade paths.',
    validation:
      'Try: "Is a 650W PSU enough for Ryzen 7 7700 + RTX 4070 Super?"',
    icon: Cpu,
  },
  {
    title: 'Warranty & Returns',
    description:
      'Understand return windows, warranty terms, and replacement flow before visiting.',
    validation:
      'Try: "My motherboard failed after 7 months. Is this warranty-covered?"',
    icon: Shield,
  },
  {
    title: 'Troubleshooting',
    description:
      'Quick diagnostics for no-POST issues, overheating, crashes, and unstable hardware behavior.',
    validation:
      'Try: "Fans spin but no display after RAM upgrade. What should I check?"',
    icon: Wrench,
  },
  {
    title: 'Store Information',
    description:
      'Get location, hours, contact details, and what services are available in-store.',
    validation:
      'Try: "Are you open on Sunday and do you do BIOS updates in-store?"',
    icon: Store,
  },
  {
    title: 'Support Handoff',
    description:
      'When a case needs manual review, Chocomi clearly directs you to in-store or phone support.',
    validation:
      'Try: "Can you approve my RMA now?" and see escalation guidance.',
    icon: LifeBuoy,
  },
]

const stockItems = [
  { name: 'NVIDIA RTX 4060 8GB', qty: '12', tag: 'Good', price: '$329', notes: 'ASUS Dual / MSI Ventus' },
  { name: 'NVIDIA RTX 4070 Super', qty: '6', tag: 'Limited', price: '$589', notes: 'Gigabyte Windforce' },
  { name: 'AMD RX 7700 XT 12GB', qty: '9', tag: 'Good', price: '$419', notes: 'Sapphire Pulse' },
  { name: 'Intel Core i5-14400F', qty: '19', tag: 'Good', price: '$209', notes: 'Boxed with cooler' },
  { name: 'AMD Ryzen 7 7700', qty: '11', tag: 'Good', price: '$299', notes: 'AM5 platform' },
  { name: 'MSI B650 Tomahawk WiFi', qty: '7', tag: 'Limited', price: '$219', notes: 'DDR5 / PCIe Gen4' },
  { name: 'Corsair Vengeance DDR5 32GB', qty: '16', tag: 'Good', price: '$109', notes: '6000MHz CL30' },
  { name: 'WD Black SN850X 1TB', qty: '26', tag: 'Good', price: '$99', notes: 'PCIe Gen4 NVMe' },
  { name: 'Samsung 990 Pro 2TB', qty: '8', tag: 'Limited', price: '$169', notes: 'Heatsink included' },
  { name: 'Corsair RM750e PSU', qty: '5', tag: 'Limited', price: '$109', notes: 'ATX 3.0, 80+ Gold' },
  { name: 'DeepCool AK620 Cooler', qty: '14', tag: 'Good', price: '$59', notes: 'Dual-tower air cooling' },
  { name: 'Arctic P12 Fan 5-Pack', qty: '22', tag: 'Good', price: '$34', notes: '120mm PWM' },
]

export default function HomePage() {
  return (
    <div className="min-h-dvh bg-[radial-gradient(circle_at_15%_10%,rgba(220,68,48,0.22),transparent_35%),radial-gradient(circle_at_85%_20%,rgba(13,148,136,0.2),transparent_30%),linear-gradient(180deg,var(--background),var(--background))]">
      <ChatRoutePrefetch />
      <header className="sticky top-0 z-40 border-b border-border/70 bg-background/85 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary text-primary-foreground">
              <Store className="h-5 w-5" />
            </span>
            <div>
              <p className="text-base font-semibold">ByteBodega</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/chat"
              prefetch
              className="rounded-lg border border-border/70 px-3 py-2 text-sm font-medium transition-colors hover:bg-muted"
            >
              Open Full Chat
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main>
        <section className="mx-auto grid w-full max-w-7xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:py-24">
          <div className="space-y-6">
            <p className="inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-primary">
              ByteBodega Hardware Store
            </p>
            <h1 className="text-4xl font-semibold leading-tight sm:text-5xl">
              Performance parts, real stock,
              <span className="block text-primary">local experts who actually build PCs.</span>
            </h1>
            <p className="max-w-2xl text-base text-muted-foreground sm:text-lg">
              ByteBodega is your neighborhood computer hardware store for gaming rigs, workstation
              upgrades, and reliable replacement parts. Check live inventory, store policies, and
              in-store service options from one page.
            </p>
            <div className="flex flex-wrap gap-3">
              <a
                href="#stock"
                className="rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
              >
                Browse In-Stock Parts
              </a>
              <Link
                href="/chat"
                prefetch
                className="rounded-xl border border-border/70 px-5 py-3 text-sm font-semibold transition-colors hover:bg-muted"
              >
                Chat with Chocomi
              </Link>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-border/70 bg-card/80 p-3">
                <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Inventory Board</p>
                <p className="mt-1 text-lg font-semibold">{stockItems.length} active listings</p>
              </div>
              <div className="rounded-xl border border-border/70 bg-card/80 p-3">
                <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Build Counter</p>
                <p className="mt-1 text-lg font-semibold">Custom assembly help</p>
              </div>
              <div className="rounded-xl border border-border/70 bg-card/80 p-3">
                <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Local Service</p>
                <p className="mt-1 text-lg font-semibold">In-store + phone support</p>
              </div>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-3xl border border-border/70 bg-card/70 p-6 shadow-xl backdrop-blur">
            <div className="absolute -right-10 -top-10 h-28 w-28 rounded-full bg-primary/20 blur-2xl" />
            <div className="absolute -bottom-10 -left-10 h-28 w-28 rounded-full bg-emerald-500/20 blur-2xl" />
            <div className="relative space-y-4">
              <h2 className="text-xl font-semibold">Store highlights today</h2>
              <p className="text-sm text-muted-foreground">
                Fast look at popular components currently moving through the counter.
              </p>
              <div className="space-y-2 text-sm">
                {stockItems.slice(0, 4).map((item) => (
                  <article
                    key={item.name}
                    className="rounded-xl border border-border/70 bg-background/80 p-3"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium">{item.name}</p>
                      <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                        {item.price}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">{item.qty} in stock | {item.notes}</p>
                  </article>
                ))}
              </div>
              <a
                href="#stock"
                className="inline-flex rounded-lg border border-border/70 px-3 py-2 text-xs font-medium transition-colors hover:bg-muted"
              >
                View full stock board
              </a>
            </div>
          </div>
        </section>

        <section id="capabilities" className="mx-auto w-full max-w-7xl px-4 pb-8 sm:px-6">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-2xl font-semibold sm:text-3xl">Chocomi, your AI support assistant</h2>
            <Link
              href="/chat"
              prefetch
              className="rounded-lg border border-border/70 px-3 py-2 text-xs font-medium transition-colors hover:bg-muted"
            >
              Test in Full Chat
            </Link>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {capabilities.map((item) => (
              <article
                key={item.title}
                className="rounded-2xl border border-border/70 bg-card/80 p-5 shadow-sm backdrop-blur"
              >
                <item.icon className="mb-3 h-5 w-5 text-primary" />
                <h3 className="text-lg font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{item.description}</p>
                <div className="mt-3 rounded-lg border border-border/70 bg-background/70 p-3">
                  <p className="text-xs font-medium text-foreground">Validation Prompt</p>
                  <p className="mt-1 text-xs text-muted-foreground">{item.validation}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="stock" className="mx-auto w-full max-w-7xl px-4 py-12 sm:px-6">
          <div className="rounded-3xl border border-border/70 bg-card/60 p-5 shadow-sm backdrop-blur sm:p-6">
            <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="text-2xl font-semibold sm:text-3xl">In-stock board</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Larger inventory preview so users can validate product inquiry coverage directly on homepage.
                </p>
              </div>
              <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                {stockItems.length} listed items
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {stockItems.map((item) => (
                <article
                  key={item.name}
                  className="rounded-xl border border-border/70 bg-background/85 p-3"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold">{item.name}</p>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                        item.tag === 'Limited'
                          ? 'bg-amber-500/15 text-amber-500'
                          : 'bg-emerald-500/15 text-emerald-500'
                      }`}
                    >
                      {item.tag}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{item.notes}</p>
                  <div className="mt-3 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">{item.qty} in stock</span>
                    <span className="font-semibold">{item.price}</span>
                  </div>
                </article>
              ))}
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              Online preview may lag by a few minutes. Final stock is confirmed at checkout or by phone.
            </p>
          </div>
        </section>

        <section id="policy" className="mx-auto w-full max-w-7xl px-4 pb-10 sm:px-6">
          <h2 className="mb-4 text-2xl font-semibold sm:text-3xl">Policy and support details</h2>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <article className="rounded-2xl border border-border/70 bg-card/80 p-4">
              <Shield className="mb-2 h-4 w-4 text-primary" />
              <p className="text-sm font-semibold">Returns Window</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Most unopened items can be returned within 14 days with receipt and original packaging.
              </p>
            </article>
            <article className="rounded-2xl border border-border/70 bg-card/80 p-4">
              <BadgeCheck className="mb-2 h-4 w-4 text-primary" />
              <p className="text-sm font-semibold">Warranty Claims</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Chocomi explains warranty flow, but final approval requires in-store diagnostics.
              </p>
            </article>
            <article className="rounded-2xl border border-border/70 bg-card/80 p-4">
              <Wrench className="mb-2 h-4 w-4 text-primary" />
              <p className="text-sm font-semibold">Troubleshooting Scope</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Covers no-POST checks, compatibility errors, thermal issues, and basic stability steps.
              </p>
            </article>
            <article className="rounded-2xl border border-border/70 bg-card/80 p-4">
              <LifeBuoy className="mb-2 h-4 w-4 text-primary" />
              <p className="text-sm font-semibold">Escalation Policy</p>
              <p className="mt-1 text-xs text-muted-foreground">
                If data is missing or action requires verification, support escalates to phone or store desk.
              </p>
            </article>
          </div>
        </section>

        <section id="store-info" className="border-t border-border/70 bg-card/50">
          <div className="mx-auto grid w-full max-w-7xl gap-4 px-4 py-12 sm:px-6 md:grid-cols-3">
            <article className="rounded-2xl border border-border/70 bg-background/80 p-4">
              <MapPin className="mb-2 h-4 w-4 text-primary" />
              <p className="text-sm font-semibold">Location</p>
              <p className="text-sm text-muted-foreground">127 Byte Street, Downtown Tech District</p>
            </article>
            <article className="rounded-2xl border border-border/70 bg-background/80 p-4">
              <Phone className="mb-2 h-4 w-4 text-primary" />
              <p className="text-sm font-semibold">Contact</p>
              <p className="text-sm text-muted-foreground">+1 (555) 010-4090</p>
            </article>
            <article className="rounded-2xl border border-border/70 bg-background/80 p-4">
              <Store className="mb-2 h-4 w-4 text-primary" />
              <p className="text-sm font-semibold">Store Hours</p>
              <p className="text-sm text-muted-foreground">
                Mon-Sat: 10:00 AM - 8:00 PM | Sun: 11:00 AM - 5:00 PM
              </p>
            </article>
          </div>
        </section>
      </main>

      <FloatingChatWidget />
    </div>
  )
}
