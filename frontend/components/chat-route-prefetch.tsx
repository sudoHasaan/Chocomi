'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export function ChatRoutePrefetch() {
  const router = useRouter()

  useEffect(() => {
    router.prefetch('/chat')
  }, [router])

  return null
}
