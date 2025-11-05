// API configuration - uses VITE_API_URL from Heroku config vars
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8888'

// Convert HTTP(S) URL to WebSocket URL
export const getWebSocketURL = () => {
  const url = API_URL.replace(/^http/, 'ws')
  return `${url}/ws`
}
