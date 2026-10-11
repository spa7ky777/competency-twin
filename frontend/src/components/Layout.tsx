import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, Brain, ChartColumn, FileUp, GraduationCap, LayoutDashboard, LogOut, MessageSquare, Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'

type AiHealth = { status: string; message?: string | null; model?: string; ok?: boolean }

export function Layout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const ai = useQuery({
    queryKey: ['ai'],
    queryFn: () => api<AiHealth>('/health/ai'),
    refetchInterval: 15000,
  })
  const status = ai.data?.status || (ai.isError ? 'down' : 'unknown')
  const color = status === 'ok' ? 'bg-teal-500' : status === 'model_missing' ? 'bg-amber-500' : 'bg-red-500'
  const student = [
    { to: '/app/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/app/subjects', label: 'Subjects', icon: BookOpen },
    { to: '/app/tutor', label: 'AI Tutor', icon: MessageSquare },
    { to: '/app/twin', label: 'Competency Twin', icon: Brain },
    { to: '/app/recommendations', label: 'Recommendations', icon: Sparkles },
    { to: '/app/resources', label: 'Resources', icon: FileUp },
    { to: '/app/quiz/generate', label: 'Practice quiz', icon: GraduationCap },
  ]
  const trainer = [
    { to: '/app/trainer', label: 'Trainer home', icon: LayoutDashboard },
    { to: '/app/manage', label: 'Manage subjects', icon: BookOpen },
    { to: '/app/upload', label: 'Documents', icon: FileUp },
    { to: '/app/review', label: 'Question review', icon: GraduationCap },
    { to: '/app/analytics', label: 'Analytics', icon: ChartColumn },
    { to: '/app/tutor', label: 'AI Tutor', icon: MessageSquare },
  ]
  const links = user?.role === 'trainer' ? trainer : student
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-indigo-950 p-4 text-indigo-50 md:block">
        <div className="mb-8 px-2 text-lg font-semibold tracking-tight">Competency Twin</div>
        <nav className="space-y-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-xl px-3 py-2 text-sm ${isActive ? 'bg-indigo-800 text-white' : 'text-indigo-200 hover:bg-indigo-900'}`
              }
            >
              <l.icon size={16} />
              {l.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3">
          <div className="text-sm text-slate-500 md:hidden">Competency Twin</div>
          <div className="ml-auto flex items-center gap-3">
            <div
              className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1 text-xs"
              title={ai.data?.message || `Ollama ${status} (${ai.data?.model || ''})`}
            >
              <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
              Local AI: {status === 'ok' ? 'ready' : status === 'model_missing' ? 'model missing' : 'unavailable'}
            </div>
            <span className="text-sm text-slate-600">
              {user?.name} · {user?.role}
            </span>
            <button
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
              type="button"
              onClick={() => {
                logout()
                nav('/')
              }}
            >
              <LogOut size={16} />
            </button>
          </div>
        </header>
        <main className="flex-1 p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
