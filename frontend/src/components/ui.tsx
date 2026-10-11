import type { ReactNode } from 'react'

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-slate-200 bg-white p-5 ${className}`}>{children}</div>
}

export function Badge({ label, tone }: { label: string; tone?: string }) {
  const map: Record<string, string> = {
    'Critical Gap': 'bg-red-100 text-red-800',
    'Needs Improvement': 'bg-orange-100 text-orange-800',
    Developing: 'bg-amber-100 text-amber-800',
    Proficient: 'bg-teal-100 text-teal-800',
    Strong: 'bg-indigo-100 text-indigo-800',
    ready: 'bg-teal-100 text-teal-800',
    failed: 'bg-red-100 text-red-800',
    processing: 'bg-amber-100 text-amber-800',
    pending: 'bg-slate-100 text-slate-700',
    approved: 'bg-teal-100 text-teal-800',
    needs_review: 'bg-orange-100 text-orange-800',
    rejected: 'bg-red-100 text-red-800',
  }
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${map[tone || label] || 'bg-slate-100 text-slate-700'}`}>
      {label}
    </span>
  )
}

export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div className="h-full rounded-full bg-indigo-600" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
    </div>
  )
}

export function Skeleton({ className = 'h-6' }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-slate-200 ${className}`} />
}

export function EmptyState({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return (
    <Card className="text-center">
      <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
      <p className="mt-2 text-sm text-slate-500">{body}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </Card>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Card className="border-red-200 bg-red-50">
      <p className="text-sm text-red-800">{message}</p>
      {onRetry ? (
        <button className="mt-3 rounded-lg bg-red-700 px-3 py-1.5 text-sm text-white" onClick={onRetry} type="button">
          Try again
        </button>
      ) : null}
    </Card>
  )
}

export function Button({
  children,
  onClick,
  type = 'button',
  disabled,
  variant = 'primary',
}: {
  children: ReactNode
  onClick?: () => void
  type?: 'button' | 'submit'
  disabled?: boolean
  variant?: 'primary' | 'ghost' | 'danger'
}) {
  const cls =
    variant === 'primary'
      ? 'bg-indigo-700 text-white hover:bg-indigo-800'
      : variant === 'danger'
        ? 'bg-red-600 text-white'
        : 'bg-slate-100 text-slate-800'
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`rounded-xl px-4 py-2 text-sm font-medium disabled:opacity-50 ${cls}`}
    >
      {children}
    </button>
  )
}
