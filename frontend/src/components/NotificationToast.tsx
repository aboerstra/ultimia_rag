import { useEffect } from 'react'
import './NotificationToast.css'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
}

interface NotificationToastProps {
  notification: Notification
  onClose: (id: string) => void
}

function NotificationToast({ notification, onClose }: NotificationToastProps) {
  useEffect(() => {
    const duration = notification.duration || 5000
    const timer = setTimeout(() => {
      onClose(notification.id)
    }, duration)

    return () => clearTimeout(timer)
  }, [notification, onClose])

  const getIcon = () => {
    switch (notification.type) {
      case 'success': return '✅'
      case 'error': return '❌'
      case 'warning': return '⚠️'
      case 'info': return 'ℹ️'
    }
  }

  return (
    <div className={`notification-toast ${notification.type}`}>
      <div className="toast-icon">{getIcon()}</div>
      <div className="toast-message">{notification.message}</div>
      <button 
        className="toast-close"
        onClick={() => onClose(notification.id)}
        aria-label="Close notification"
      >
        ×
      </button>
    </div>
  )
}

export default NotificationToast
