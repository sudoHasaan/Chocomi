import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import { ThemeProvider } from '@/providers/theme-provider'
import { ChatProvider } from '@/context/chat-context'
import { Sidebar } from '@/components/sidebar'
import './globals.css'

const _geist = Geist({ subsets: ["latin"] });
const _geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'Chocomi | Customer Support Chat',
  description:
    'Chat with Chocomi, our friendly customer support assistant. Get quick answers to your questions and resolve issues with help from our support team.',
  generator: 'v0.app',
  icons: {
    icon: [
      {
        url: '/icon-light-32x32.png',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: '/icon-dark-32x32.png',
        media: '(prefers-color-scheme: dark)',
      },
      {
        url: '/icon.svg',
        type: 'image/svg+xml',
      },
    ],
    apple: '/apple-icon.png',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ThemeProvider>
          <ChatProvider>
            <div className="flex h-screen">
              <Sidebar />
              <main className="flex-1 flex flex-col">
                {children}
              </main>
            </div>
            <Analytics />
          </ChatProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
