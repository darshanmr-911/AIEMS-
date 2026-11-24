import type { ReactNode } from 'react'
import { motion } from 'framer-motion'

export const pageMotion = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.32, ease: 'easeOut' as const },
}

export function GlassCard({
  children,
  className = '',
  interactive = false,
}: {
  children: ReactNode
  className?: string
  interactive?: boolean
}) {
  return (
    <motion.article
      className={`glass-card ${className}`}
      {...(interactive ? { whileHover: { y: -3 } } : {})}
      transition={{ duration: 0.18 }}
    >
      {children}
    </motion.article>
  )
}

export function GlassStatCard({
  label,
  value,
  detail,
  icon,
  tone = 'blue',
}: {
  label: string
  value: string | number
  detail: string
  icon: ReactNode
  tone?: 'blue' | 'green' | 'amber' | 'red'
}) {
  return (
    <motion.article className="glass-card glass-stat" whileHover={{ y: -3 }} transition={{ duration: 0.18 }}>
      <div className={`glass-stat-icon ${tone}`}>{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </motion.article>
  )
}

export function GlassButton({
  children,
  className = '',
  type = 'button',
  onClick,
  disabled,
}: {
  children: ReactNode
  className?: string
  type?: 'button' | 'submit'
  onClick?: () => void
  disabled?: boolean
}) {
  return (
    <motion.button
      type={type}
      className={`glass-button ${className}`}
      onClick={onClick}
      disabled={disabled}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.12 }}
    >
      {children}
    </motion.button>
  )
}

export function GlassModal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
}) {
  if (!open) return null
  return (
    <motion.div
      className="glass-modal-backdrop"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onMouseDown={onClose}
    >
      <motion.div
        className="glass-modal"
        initial={{ opacity: 0, scale: 0.96, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.22, ease: 'easeOut' }}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onMouseDown={(event) => event.stopPropagation()}
      >
        {children}
      </motion.div>
    </motion.div>
  )
}
