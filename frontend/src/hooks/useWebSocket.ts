import { useEffect, useState, useRef } from 'react'

interface WebSocketMessage {
  type: string
  data?: any
  [key: string]: any
}

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<number | undefined>()

  const connect = () => {
    try {
      ws.current = new WebSocket(url)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
      }

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          setLastMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)

        // Attempt to reconnect after 5 seconds
        reconnectTimeout.current = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connect()
        }, 5000)
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
    }
  }

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current)
      }
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [url])

  return {
    isConnected,
    lastMessage,
    sendMessage: (message: any) => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify(message))
      }
    },
  }
}
