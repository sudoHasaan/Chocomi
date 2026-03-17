'use client'

import { useCallback, useRef, useState } from 'react'

export function useVoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstart = () => {
        setIsRecording(true)
        setError(null)
      }

      mediaRecorder.onstop = () => {
        setIsRecording(false)
        // Clean up stream tracks
        stream.getTracks().forEach((track) => track.stop())
      }

      mediaRecorder.start()
    } catch (err) {
      console.error('Failed to start recording:', err)
      setError('Microphone access denied or not available')
      setIsRecording(false)
    }
  }, [])

  const stopRecording = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
        resolve(null)
        return
      }

      mediaRecorderRef.current.onstop = () => {
        setIsRecording(false)
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        resolve(audioBlob)
      }

      mediaRecorderRef.current.stop()
    })
  }, [])

  return {
    isRecording,
    error,
    startRecording,
    stopRecording,
  }
}
