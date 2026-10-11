import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link, Navigate, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Markdown from 'react-markdown'
import { toast } from 'sonner'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api, ApiError, apiUrl, getStoredUser } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { Badge, Button, Card, EmptyState, ErrorState, ProgressBar, Skeleton } from '../components/ui'

function catchErr(e: unknown) {
  const msg = e instanceof ApiError ? e.message : 'Network error. Check that the backend is running.'
  toast.error(msg)
  return msg
}

export function Landing() {
  return (
    <div className="mx-auto max-w-3xl py-16 text-center">
      <p className="text-sm font-medium uppercase tracking-wide text-teal-700">Local-first adaptive learning</p>
      <h1 className="mt-3 text-4xl font-semibold text-indigo-950">Competency Twin</h1>
      <p className="mt-4 text-slate-600">
        Upload course material, ask a local AI tutor, take quizzes, and watch your competency profile update from real scores — all on your laptop with Ollama.
      </p>
      <Link to="/login" className="mt-8 inline-block rounded-xl bg-indigo-700 px-6 py-3 text-white">
        Continue
      </Link>
    </div>
  )
}

export function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const users = useQuery({ queryKey: ['users'], queryFn: () => api<{ id: number; name: string; role: string }[]>('/auth/users') })
  if (users.isLoading) return <Skeleton className="mx-auto mt-24 h-40 max-w-md" />
  return (
    <div className="mx-auto mt-16 max-w-lg">
      <Card>
        <h1 className="text-2xl font-semibold text-indigo-950">Choose a demo user</h1>
        <p className="mt-2 text-sm text-slate-500">No passwords. Pick Student or Trainer to start.</p>
        <div className="mt-6 space-y-2">
          {(users.data || []).map((u) => (
            <button
              key={u.id}
              type="button"
              className="flex w-full items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-left hover:bg-slate-50"
              onClick={async () => {
                try {
                  await login(u.id)
                  nav(u.role === 'trainer' ? '/app/trainer' : '/app/dashboard')
                } catch (e) {
                  catchErr(e)
                }
              }}
            >
              <span className="font-medium">{u.name}</span>
              <Badge label={u.role} />
            </button>
          ))}
        </div>
      </Card>
    </div>
  )
}

export function Guard({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  if (!user && !getStoredUser()) return <Navigate to="/login" replace />
  return <>{children}</>
}

type Subject = { id: number; name: string; code: string; description: string }

export function StudentDashboard() {
  const { user } = useAuth()
  const subjects = useQuery({ queryKey: ['subjects'], queryFn: () => api<Subject[]>('/subjects') })
  const attempts = useQuery({
    queryKey: ['attempts', user?.id],
    queryFn: () => api<{ id: number; title: string; score_percent: number; submitted_at: string | null }[]>(`/students/${user!.id}/attempts`),
    enabled: !!user,
  })
  const twin = useQuery({
    queryKey: ['twin', user?.id],
    queryFn: () => api<{ overall: number | null; overall_status: string | null; items: unknown[] }>(`/students/${user!.id}/competencies`),
    enabled: !!user,
  })
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-indigo-950">Welcome back, {user?.name}</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <p className="text-sm text-slate-500">Overall twin score</p>
          <p className="mt-2 text-3xl font-semibold">{twin.data?.overall != null ? `${twin.data.overall.toFixed(0)}%` : '—'}</p>
          {twin.data?.overall_status ? <Badge label={twin.data.overall_status} /> : null}
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Subjects</p>
          <p className="mt-2 text-3xl font-semibold">{subjects.data?.length ?? 0}</p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Assessments</p>
          <p className="mt-2 text-3xl font-semibold">{attempts.data?.length ?? 0}</p>
        </Card>
      </div>
      {!twin.data?.items?.length ? (
        <EmptyState
          title="Take your diagnostic to build your Competency Twin"
          body="Pick a subject, load demo material (trainer) or use uploaded notes, then start a diagnostic quiz."
          action={
            <Link to="/app/subjects" className="text-indigo-700">
              Browse subjects
            </Link>
          }
        />
      ) : null}
    </div>
  )
}

export function SubjectsPage() {
  const subjects = useQuery({ queryKey: ['subjects'], queryFn: () => api<Subject[]>('/subjects') })
  if (subjects.isLoading) return <Skeleton className="h-40" />
  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Subjects</h1>
      <div className="grid gap-4 md:grid-cols-2">
        {(subjects.data || []).map((s) => (
          <Link key={s.id} to={`/app/subjects/${s.id}`}>
            <Card className="hover:border-indigo-200">
              <p className="text-xs text-teal-700">{s.code}</p>
              <h2 className="text-lg font-semibold">{s.name}</h2>
              <p className="mt-1 text-sm text-slate-500">{s.description}</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}

export function SubjectDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const nav = useNavigate()
  const tree = useQuery({
    queryKey: ['tree', id],
    queryFn: () => api<{ name: string; units: { id: number; title: string; topics: { id: number; title: string; competencies: { id: number; name: string }[] }[] }[] }>(
      `/subjects/${id}/tree`,
    ),
  })
  const docs = useQuery({
    queryKey: ['docs', id],
    queryFn: () => api<{ id: number; original_filename: string; status: string }[]>(`/documents?subject_id=${id}`),
  })
  const startDiag = useMutation({
    mutationFn: () => api<{ id: number }>(`/diagnostic/start`, { method: 'POST', body: JSON.stringify({ subject_id: Number(id) }) }),
    onSuccess: (d) => nav(`/app/quiz/${d.id}`),
    onError: catchErr,
  })
  if (tree.isLoading) return <Skeleton className="h-64" />
  if (tree.error) return <ErrorState message={catchErr(tree.error)} onRetry={() => tree.refetch()} />
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">{tree.data?.name}</h1>
        <div className="flex gap-2">
          <Button onClick={() => nav(`/app/tutor?subject=${id}`)}>Open AI Tutor</Button>
          <Button onClick={() => startDiag.mutate()} disabled={startDiag.isPending}>
            Take diagnostic
          </Button>
        </div>
      </div>
      {(docs.data || []).length === 0 ? (
        <EmptyState
          title="No learning material yet"
          body={user?.role === 'trainer' ? 'Upload documents or load the demo dataset.' : 'Ask a trainer to upload notes for this subject.'}
          action={
            user?.role === 'trainer' ? (
              <Link to="/app/upload" className="text-indigo-700">
                Go to uploads
              </Link>
            ) : null
          }
        />
      ) : (
        <p className="text-sm text-slate-500">{docs.data?.length} document(s) available</p>
      )}
      {(tree.data?.units || []).map((u) => (
        <Card key={u.id}>
          <h2 className="font-semibold">{u.title}</h2>
          <ul className="mt-3 space-y-2">
            {u.topics.map((t) => (
              <li key={t.id}>
                <Link className="text-indigo-700" to={`/app/topics/${t.id}`}>
                  {t.title}
                </Link>
                <span className="ml-2 text-xs text-slate-400">{t.competencies.length} competencies</span>
              </li>
            ))}
          </ul>
        </Card>
      ))}
    </div>
  )
}

export function TopicDetail() {
  const { id } = useParams()
  const topic = useQuery({
    queryKey: ['topic', id],
    queryFn: () => api<{ title: string; description: string; competencies: { id: number; name: string }[] }>(`/topics/${id}`),
  })
  if (topic.isLoading) return <Skeleton className="h-40" />
  return (
    <div>
      <h1 className="text-2xl font-semibold">{topic.data?.title}</h1>
      <p className="mt-2 text-slate-600">{topic.data?.description}</p>
      <div className="mt-4 grid gap-3">
        {(topic.data?.competencies || []).map((c) => (
          <Card key={c.id}>{c.name}</Card>
        ))}
      </div>
    </div>
  )
}

export function TutorPage() {
  const [params] = useSearchParams()
  const subjects = useQuery({ queryKey: ['subjects'], queryFn: () => api<Subject[]>('/subjects') })
  const [subjectId, setSubjectId] = useState(Number(params.get('subject') || 0))
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<{ role: 'user' | 'ai'; text: string; sources?: unknown[]; grounded?: boolean }[]>([])
  useEffect(() => {
    if (!subjectId && subjects.data?.[0]) setSubjectId(subjects.data[0].id)
  }, [subjects.data, subjectId])
  const send = async (e: FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return
    const q = question
    setQuestion('')
    setMessages((m) => [...m, { role: 'user', text: q }])
    try {
      const res = await api<{ answer: string; sources: unknown[]; grounded: boolean }>('/rag/query', {
        method: 'POST',
        body: JSON.stringify({ subject_id: subjectId, question: q }),
      })
      setMessages((m) => [...m, { role: 'ai', text: res.answer, sources: res.sources, grounded: res.grounded }])
    } catch (err) {
      const msg = catchErr(err)
      setMessages((m) => [...m, { role: 'ai', text: msg }])
    }
  }
  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-semibold">AI Tutor</h1>
      <select className="rounded-xl border px-3 py-2" value={subjectId} onChange={(e) => setSubjectId(Number(e.target.value))}>
        {(subjects.data || []).map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
      <div className="space-y-3">
        {messages.length === 0 ? (
          <EmptyState title="Ask a question" body="Answers are grounded in uploaded course material when possible." />
        ) : null}
        {messages.map((m, i) => (
          <Card key={i} className={m.role === 'user' ? 'bg-indigo-50' : ''}>
            <p className="text-xs uppercase text-slate-400">{m.role}</p>
            {m.role === 'ai' ? <Markdown>{m.text}</Markdown> : <p>{m.text}</p>}
            {m.grounded != null ? (
              <div className="mt-2">
                <Badge label={m.grounded ? 'Answered from course material' : 'Not found in material / general reasoning'} />
              </div>
            ) : null}
            {Array.isArray(m.sources) && m.sources.length > 0 ? (
              <details className="mt-3 text-sm">
                <summary>Sources used</summary>
                {(m.sources as { filename?: string; page?: number; excerpt?: string }[]).map((s, j) => (
                  <p key={j} className="mt-2 rounded-lg bg-slate-50 p-2">
                    {s.filename} {s.page ? `p.${s.page}` : ''} — {s.excerpt}
                  </p>
                ))}
              </details>
            ) : null}
          </Card>
        ))}
      </div>
      <form onSubmit={send} className="flex gap-2">
        <input className="flex-1 rounded-xl border px-3 py-2" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="What is overfitting?" />
        <Button type="submit">Ask</Button>
      </form>
    </div>
  )
}

export function QuizGenerate() {
  const subjects = useQuery({ queryKey: ['subjects'], queryFn: () => api<Subject[]>('/subjects') })
  const nav = useNavigate()
  const [subjectId, setSubjectId] = useState(0)
  const [n, setN] = useState(10)
  const [difficulty, setDifficulty] = useState('medium')
  useEffect(() => {
    if (!subjectId && subjects.data?.[0]) setSubjectId(subjects.data[0].id)
  }, [subjects.data, subjectId])
  const gen = useMutation({
    mutationFn: () =>
      api<{ id: number }>('/quizzes/generate', {
        method: 'POST',
        body: JSON.stringify({ subject_id: subjectId, num_questions: n, difficulty, quiz_type: 'regular' }),
      }),
    onSuccess: (d) => nav(`/app/quiz/${d.id}`),
    onError: catchErr,
  })
  return (
    <Card className="max-w-lg">
      <h1 className="text-xl font-semibold">Generate a practice quiz</h1>
      <label className="mt-4 block text-sm">Subject</label>
      <select className="mt-1 w-full rounded-xl border px-3 py-2" value={subjectId} onChange={(e) => setSubjectId(Number(e.target.value))}>
        {(subjects.data || []).map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
      <label className="mt-3 block text-sm">Questions</label>
      <input className="mt-1 w-full rounded-xl border px-3 py-2" type="number" min={3} max={15} value={n} onChange={(e) => setN(Number(e.target.value))} />
      <label className="mt-3 block text-sm">Difficulty</label>
      <select className="mt-1 w-full rounded-xl border px-3 py-2" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
        <option value="easy">easy</option>
        <option value="medium">medium</option>
        <option value="hard">hard</option>
      </select>
      <div className="mt-4">
        <Button onClick={() => gen.mutate()} disabled={gen.isPending}>
          {gen.isPending ? 'Generating…' : 'Generate'}
        </Button>
      </div>
    </Card>
  )
}

type Q = { id: number; question_text: string; options: string[]; position: number }

export function QuizPlayer() {
  const { id } = useParams()
  const nav = useNavigate()
  const quiz = useQuery({
    queryKey: ['quiz', id],
    queryFn: () => api<{ id: number; title: string; attempt_id: number; questions: Q[] }>(`/quizzes/${id}`),
  })
  const [idx, setIdx] = useState(0)
  const [answers, setAnswers] = useState<Record<number, number>>({})
  useEffect(() => {
    const raw = sessionStorage.getItem(`quiz-${id}`)
    if (raw) setAnswers(JSON.parse(raw) as Record<number, number>)
  }, [id])
  useEffect(() => {
    sessionStorage.setItem(`quiz-${id}`, JSON.stringify(answers))
  }, [answers, id])
  if (quiz.isLoading) return <Skeleton className="h-64" />
  if (quiz.error) return <ErrorState message={catchErr(quiz.error)} onRetry={() => quiz.refetch()} />
  const qs = quiz.data?.questions || []
  const q = qs[idx]
  const unanswered = qs.filter((x) => answers[x.id] === undefined).length
  const submit = async () => {
    if (unanswered && !confirm(`${unanswered} unanswered. Submit anyway?`)) return
    try {
      const res = await api<{ attempt_id: number }>(`/quizzes/${id}/submit`, {
        method: 'POST',
        body: JSON.stringify({
          attempt_id: quiz.data?.attempt_id,
          answers: qs.map((x) => ({ question_id: x.id, selected_option: answers[x.id] ?? null })),
        }),
      })
      sessionStorage.removeItem(`quiz-${id}`)
      nav(`/app/results/${res.attempt_id}`)
    } catch (e) {
      catchErr(e)
    }
  }
  if (!q) return <EmptyState title="No questions" body="This quiz is empty." />
  return (
    <div className="grid gap-4 md:grid-cols-[220px_1fr]">
      <Card>
        <p className="text-sm font-medium">{quiz.data?.title}</p>
        <ProgressBar value={((idx + 1) / qs.length) * 100} />
        <div className="mt-3 grid grid-cols-5 gap-1">
          {qs.map((item, i) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setIdx(i)}
              className={`h-8 rounded text-xs ${answers[item.id] !== undefined ? 'bg-teal-600 text-white' : 'bg-slate-100'} ${i === idx ? 'ring-2 ring-indigo-500' : ''}`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      </Card>
      <Card>
        <p className="text-sm text-slate-500">
          Question {idx + 1} of {qs.length}
        </p>
        <h2 className="mt-2 text-lg font-medium">{q.question_text}</h2>
        <div className="mt-4 space-y-2">
          {q.options.map((opt, i) => (
            <label key={i} className={`flex cursor-pointer gap-2 rounded-xl border p-3 ${answers[q.id] === i ? 'border-indigo-500 bg-indigo-50' : ''}`}>
              <input type="radio" name="opt" checked={answers[q.id] === i} onChange={() => setAnswers({ ...answers, [q.id]: i })} />
              {opt}
            </label>
          ))}
        </div>
        <div className="mt-6 flex justify-between">
          <Button variant="ghost" disabled={idx === 0} onClick={() => setIdx(idx - 1)}>
            Previous
          </Button>
          {idx < qs.length - 1 ? <Button onClick={() => setIdx(idx + 1)}>Next</Button> : <Button onClick={() => void submit()}>Submit</Button>}
        </div>
      </Card>
    </div>
  )
}

export function QuizResults() {
  const { id } = useParams()
  const nav = useNavigate()
  const res = useQuery({
    queryKey: ['attempt', id],
    queryFn: () =>
      api<{
        score_percent: number
        correct_count: number
        total_count: number
        review: {
          questions: {
            id: number
            question_text: string
            options: string[]
            selected_option: number | null
            correct_option: number
            is_correct: boolean
            explanation: string
            competency_id: number
            source?: { filename?: string; excerpt?: string }
          }[]
        }
      }>(`/attempts/${id}`),
  })
  const { user } = useAuth()
  const twin = useQuery({
    queryKey: ['twin-after', user?.id],
    queryFn: () => api<{ items: { competency_id: number; name: string; current_score: number; previous_score: number | null }[] }>(`/students/${user!.id}/competencies`),
    enabled: !!user,
  })
  if (res.isLoading) return <Skeleton className="h-64" />
  const qs = res.data?.review.questions || []
  const byComp: Record<string, { c: number; t: number }> = {}
  for (const q of qs) {
    const k = String(q.competency_id || 'general')
    byComp[k] = byComp[k] || { c: 0, t: 0 }
    byComp[k].t += 1
    if (q.is_correct) byComp[k].c += 1
  }
  const chart = Object.entries(byComp).map(([k, v]) => ({ name: k, score: (v.c / v.t) * 100 }))
  const weak = twin.data?.items.slice().sort((a, b) => a.current_score - b.current_score)[0]
  return (
    <div className="space-y-4">
      <Card>
        <h1 className="text-2xl font-semibold">Score {res.data?.score_percent?.toFixed(0)}%</h1>
        <p className="text-slate-500">
          {res.data?.correct_count} / {res.data?.total_count} correct
        </p>
      </Card>
      <Card className="h-64">
        <p className="mb-2 text-sm font-medium">Competency breakdown (this quiz)</p>
        <ResponsiveContainer>
          <BarChart data={chart}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="score" fill="#4338ca" />
          </BarChart>
        </ResponsiveContainer>
      </Card>
      {qs.map((q) => (
        <Card key={q.id} className={q.is_correct ? '' : 'border-orange-200'}>
          <p className="font-medium">{q.question_text}</p>
          <p className="mt-1 text-sm">Your answer: {q.options[q.selected_option ?? -1] || '—'}</p>
          <p className="text-sm">Correct: {q.options[q.correct_option]}</p>
          <p className="mt-2 text-sm text-slate-600">{q.explanation}</p>
          {q.source?.filename ? (
            <p className="mt-1 text-xs text-slate-400">
              Generated from: {q.source.filename}
            </p>
          ) : null}
        </Card>
      ))}
      <div className="flex flex-wrap gap-2">
        {weak ? (
          <Button
            onClick={async () => {
              try {
                const qz = await api<{ id: number }>(`/competencies/${weak.competency_id}/targeted-quiz`, { method: 'POST' })
                nav(`/app/quiz/${qz.id}`)
              } catch (e) {
                catchErr(e)
              }
            }}
          >
            Practice Weak Area
          </Button>
        ) : null}
        <Button variant="ghost" onClick={() => nav('/app/twin')}>
          View Twin
        </Button>
        <Button variant="ghost" onClick={() => nav('/app/subjects')}>
          Back to subject
        </Button>
      </div>
    </div>
  )
}

export function TwinPage() {
  const { user } = useAuth()
  const subjects = useQuery({ queryKey: ['subjects'], queryFn: () => api<Subject[]>('/subjects') })
  const [sid, setSid] = useState(0)
  useEffect(() => {
    if (!sid && subjects.data?.[0]) setSid(subjects.data[0].id)
  }, [subjects.data, sid])
  const profile = useQuery({
    queryKey: ['profile', user?.id, sid],
    queryFn: () =>
      api<{
        overall: number | null
        overall_status: string | null
        coverage: { assessed: number; total: number } | null
        items: { competency_id: number; name: string; current_score: number; attempts: number; status: string; previous_score: number | null }[]
        gaps: { weak: { competency_id: number; name: string; current_score: number }[]; strong: { name: string; current_score: number }[] }
      }>(`/students/${user!.id}/competencies?subject_id=${sid}`),
    enabled: !!user && !!sid,
  })
  const history = useQuery({
    queryKey: ['hist', user?.id],
    queryFn: () => api<{ competency_id: number; score_after: number; recorded_at: string }[]>(`/students/${user!.id}/progress`),
    enabled: !!user,
  })
  const recs = useQuery({
    queryKey: ['recs', user?.id],
    queryFn: () => api<{ competency_id: number; competency_name: string; reason_text: string }[]>(`/students/${user!.id}/recommendations`),
    enabled: !!user,
  })
  const items = profile.data?.items || []
  if (profile.isLoading) return <Skeleton className="h-64" />
  if (!items.length) {
    return (
      <EmptyState
        title="Take your diagnostic to build your Competency Twin"
        body="Scores appear only after you submit a real quiz. Nothing is faked."
        action={<Link to="/app/subjects">Go to subjects</Link>}
      />
    )
  }
  const radar = items.slice(0, 8).map((i) => ({ name: i.name.slice(0, 18), score: i.current_score }))
  const bars = (subjects.data || []).map((s) => ({ name: s.name, score: s.id === sid ? profile.data?.overall || 0 : 0 }))
  const line = (history.data || []).map((h) => ({ t: h.recorded_at?.slice(5, 16), score: h.score_after }))
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Competency Twin</h1>
        <select className="rounded-xl border px-3 py-2" value={sid} onChange={(e) => setSid(Number(e.target.value))}>
          {(subjects.data || []).map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <p className="text-sm text-slate-500">Overall</p>
          <p className="text-3xl font-semibold">{profile.data?.overall?.toFixed(0)}%</p>
          {profile.data?.overall_status ? <Badge label={profile.data.overall_status} /> : null}
          {profile.data?.coverage ? (
            <p className="mt-2 text-xs text-slate-500">
              assessed {profile.data.coverage.assessed} of {profile.data.coverage.total} competencies
            </p>
          ) : null}
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Strongest</p>
          <p className="font-medium">{profile.data?.gaps.strong[0]?.name || '—'}</p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Weakest</p>
          <p className="font-medium">{profile.data?.gaps.weak[0]?.name || '—'}</p>
        </Card>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="h-72">
          <p className="mb-2 text-sm font-medium">Subject score</p>
          <ResponsiveContainer>
            <BarChart data={bars}>
              <XAxis dataKey="name" hide />
              <YAxis />
              <Tooltip />
              <Bar dataKey="score" fill="#0f766e" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        {radar.length >= 3 ? (
          <Card className="h-72">
            <p className="mb-2 text-sm font-medium">Profile radar</p>
            <ResponsiveContainer>
              <RadarChart data={radar}>
                <PolarGrid />
                <PolarAngleAxis dataKey="name" />
                <Radar dataKey="score" stroke="#4338ca" fill="#4338ca" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </Card>
        ) : (
          <Card>Need at least 3 assessed competencies for a radar chart.</Card>
        )}
      </div>
      <Card>
        <p className="mb-3 text-sm font-medium">Heatmap</p>
        <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
          {items.map((i) => (
            <div key={i.competency_id} className="rounded-xl border p-2 text-xs" title={`${i.current_score}% · ${i.attempts} attempts`}>
              <Badge label={i.status} />
              <p className="mt-1 font-medium">{i.name}</p>
              <p>
                {i.current_score.toFixed(0)}% {i.previous_score != null ? `(was ${i.previous_score.toFixed(0)}%)` : ''}
              </p>
            </div>
          ))}
        </div>
      </Card>
      <Card className="h-72">
        <p className="mb-2 text-sm font-medium">Score over time</p>
        <ResponsiveContainer>
          <LineChart data={line}>
            <XAxis dataKey="t" />
            <YAxis />
            <Tooltip />
            <Line dataKey="score" stroke="#4338ca" />
          </LineChart>
        </ResponsiveContainer>
      </Card>
      <Card>
        <h2 className="font-semibold">Recommendations</h2>
        {(recs.data || []).map((r) => (
          <p key={r.competency_id} className="mt-2 text-sm">
            {r.reason_text}
          </p>
        ))}
      </Card>
    </div>
  )
}

export function RecsPage() {
  const { user } = useAuth()
  const nav = useNavigate()
  const recs = useQuery({
    queryKey: ['recs', user?.id],
    queryFn: () =>
      api<{ competency_id: number; competency_name: string; reason_text: string; filename?: string; chunk_preview?: string }[]>(
        `/students/${user!.id}/recommendations`,
      ),
    enabled: !!user,
  })
  if (!recs.data?.length) return <EmptyState title="No recommendations yet" body="Complete a quiz so weak areas can be identified." />
  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-semibold">Recommended learning</h1>
      {recs.data.map((r) => (
        <Card key={r.competency_id}>
          <p className="font-medium">{r.competency_name}</p>
          <p className="text-sm text-slate-600">{r.reason_text}</p>
          {r.filename ? <p className="mt-1 text-xs text-slate-400">{r.filename}</p> : null}
          {r.chunk_preview ? <p className="mt-2 text-sm">{r.chunk_preview}</p> : null}
          <div className="mt-3">
            <Button
              onClick={async () => {
                try {
                  const q = await api<{ id: number }>(`/competencies/${r.competency_id}/targeted-quiz`, { method: 'POST' })
                  nav(`/app/quiz/${q.id}`)
                } catch (e) {
                  catchErr(e)
                }
              }}
            >
              Practice Weak Area
            </Button>
          </div>
        </Card>
      ))}
    </div>
  )
}

export function ResourcesPage() {
  const docs = useQuery({
    queryKey: ['alldocs'],
    queryFn: () => api<{ id: number; original_filename: string; status: string; subject_id: number }[]>('/documents'),
  })
  const [open, setOpen] = useState<number | null>(null)
  const detail = useQuery({
    queryKey: ['doc', open],
    queryFn: () => api<{ chunks: { id: number; text: string; page_number?: number }[] }>(`/documents/${open}`),
    enabled: open != null,
  })
  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Learning resources</h1>
      {(docs.data || []).map((d) => (
        <Card key={d.id} className="mb-3">
          <button type="button" className="flex w-full justify-between" onClick={() => setOpen(d.id)}>
            <span>{d.original_filename}</span>
            <Badge label={d.status} tone={d.status} />
          </button>
          {open === d.id
            ? (detail.data?.chunks || []).map((c) => (
                <p key={c.id} className="mt-2 rounded bg-slate-50 p-2 text-sm">
                  {c.page_number ? `p.${c.page_number} ` : ''}
                  {c.text}
                </p>
              ))
            : null}
        </Card>
      ))}
    </div>
  )
}

export function TrainerHome() {
  const data = useQuery({ queryKey: ['tov'], queryFn: () => api<{ student_count: number; subject_count: number; question_stats: Record<string, number> }>('/trainer/analytics/overview') })
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <p className="text-sm text-slate-500">Students</p>
        <p className="text-3xl">{data.data?.student_count}</p>
      </Card>
      <Card>
        <p className="text-sm text-slate-500">Subjects</p>
        <p className="text-3xl">{data.data?.subject_count}</p>
      </Card>
      <Card>
        <p className="text-sm text-slate-500">Questions flagged</p>
        <p className="text-3xl">{data.data?.question_stats?.needs_review || 0}</p>
      </Card>
    </div>
  )
}

export function ManageSubjects() {
  const qc = useQueryClient()
  const subjects = useQuery({ queryKey: ['subjects'], queryFn: () => api<Subject[]>('/subjects') })
  const [name, setName] = useState('')
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Manage subjects</h1>
      <Card>
        <form
          className="flex gap-2"
          onSubmit={async (e) => {
            e.preventDefault()
            try {
              await api('/subjects', { method: 'POST', body: JSON.stringify({ name, code: name.toUpperCase().replace(/\s+/g, '_') }) })
              setName('')
              qc.invalidateQueries({ queryKey: ['subjects'] })
            } catch (err) {
              catchErr(err)
            }
          }}
        >
          <input className="flex-1 rounded-xl border px-3 py-2" value={name} onChange={(e) => setName(e.target.value)} placeholder="New subject name" />
          <Button type="submit">Create</Button>
        </form>
      </Card>
      {(subjects.data || []).map((s) => (
        <Card key={s.id} className="flex items-center justify-between gap-3">
          <input
            className="flex-1 rounded-lg border px-2 py-1"
            defaultValue={s.name}
            onBlur={async (e) => {
              try {
                await api(`/subjects/${s.id}`, { method: 'PUT', body: JSON.stringify({ name: e.target.value, code: s.code, description: s.description }) })
                toast.success('Renamed')
                qc.invalidateQueries({ queryKey: ['subjects'] })
              } catch (err) {
                catchErr(err)
              }
            }}
          />
          <Button
            variant="danger"
            onClick={async () => {
              if (!confirm('Delete subject and its curriculum?')) return
              try {
                await api(`/subjects/${s.id}`, { method: 'DELETE' })
                qc.invalidateQueries({ queryKey: ['subjects'] })
              } catch (err) {
                catchErr(err)
              }
            }}
          >
            Delete
          </Button>
        </Card>
      ))}
    </div>
  )
}

export function UploadPage() {
  const subjects = useQuery({ queryKey: ['subjects'], queryFn: () => api<Subject[]>('/subjects') })
  const [sid, setSid] = useState(0)
  const docs = useQuery({
    queryKey: ['docs', sid],
    queryFn: () => api<{ id: number; original_filename: string; status: string; error_message?: string }[]>(`/documents?subject_id=${sid}`),
    enabled: !!sid,
    refetchInterval: 2000,
  })
  useEffect(() => {
    if (!sid && subjects.data?.[0]) setSid(subjects.data[0].id)
  }, [subjects.data, sid])
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Documents</h1>
      <select className="rounded-xl border px-3 py-2" value={sid} onChange={(e) => setSid(Number(e.target.value))}>
        {(subjects.data || []).map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
      <Card className="border-dashed">
        <input
          type="file"
          onChange={async (e) => {
            const f = e.target.files?.[0]
            if (!f) return
            const fd = new FormData()
            fd.append('file', f)
            fd.append('subject_id', String(sid))
            try {
              const user = getStoredUser()
              const res = await fetch(apiUrl('/documents/upload'), { method: 'POST', body: fd, headers: user ? { 'X-User-Id': String(user.id) } : {} })
              const data = await res.json()
              if (!res.ok) throw new ApiError(data?.error?.code, data?.error?.message, res.status)
              toast.success('Uploaded')
            } catch (err) {
              catchErr(err)
            }
          }}
        />
        <p className="mt-2 text-sm text-slate-500">PDF, DOCX, PPTX, TXT, MD. Max 25 MB.</p>
        <div className="mt-3">
          <Button
            onClick={async () => {
              try {
                await api('/demo/load', { method: 'POST', body: JSON.stringify({ subject_id: sid }) })
                toast.success('Demo material queued')
              } catch (e) {
                catchErr(e)
              }
            }}
          >
            Load demo material
          </Button>
        </div>
      </Card>
      {(docs.data || []).map((d) => (
        <Card key={d.id}>
          {d.original_filename} <Badge label={d.status} tone={d.status} />
          {d.error_message ? <p className="text-sm text-red-700">{d.error_message}</p> : null}
        </Card>
      ))}
    </div>
  )
}

export function ReviewPage() {
  const qs = useQuery({
    queryKey: ['qrev'],
    queryFn: () =>
      api<{ id: number; question_text: string; options: string[]; review_status: string; grounding_score: number; source: { excerpt?: string; filename?: string } }[]>(
        '/questions',
      ),
  })
  const qc = useQueryClient()
  if (qs.isLoading) return <Skeleton className="h-40" />
  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-semibold">Question review</h1>
      {(qs.data || []).map((q) => (
        <Card key={q.id} className="grid gap-3 md:grid-cols-2">
          <div>
            <Badge label={q.review_status} tone={q.review_status} />
            <p className="mt-2 font-medium">{q.question_text}</p>
            <ul className="mt-2 list-disc pl-5 text-sm">
              {q.options.map((o) => (
                <li key={o}>{o}</li>
              ))}
            </ul>
            <div className="mt-3 flex gap-2">
              <Button
                onClick={async () => {
                  await api(`/questions/${q.id}/approve`, { method: 'POST' })
                  qc.invalidateQueries({ queryKey: ['qrev'] })
                }}
              >
                Approve
              </Button>
              <Button
                variant="danger"
                onClick={async () => {
                  await api(`/questions/${q.id}/reject`, { method: 'POST' })
                  qc.invalidateQueries({ queryKey: ['qrev'] })
                }}
              >
                Reject
              </Button>
            </div>
          </div>
          <div className="rounded-xl bg-slate-50 p-3 text-sm">
            <p className="text-xs text-slate-500">Source · grounding {q.grounding_score ?? '—'}</p>
            <p className="mt-2">{q.source?.filename}</p>
            <p className="mt-2">{q.source?.excerpt}</p>
          </div>
        </Card>
      ))}
    </div>
  )
}

export function AnalyticsPage() {
  const weak = useQuery({
    queryKey: ['weak'],
    queryFn: () => api<{ competency_id: number; name: string; students_below_threshold: number; class_average: number }[]>('/trainer/analytics/weak-areas'),
  })
  const overview = useQuery({ queryKey: ['tov'], queryFn: () => api<{ students: { id: number; name: string }[] }>('/trainer/analytics/overview') })
  const chart = (weak.data || []).map((w) => ({ name: w.name.slice(0, 16), n: w.students_below_threshold }))
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Class analytics</h1>
      <Card className="h-72">
        <ResponsiveContainer>
          <BarChart data={chart}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="n" fill="#b45309" />
          </BarChart>
        </ResponsiveContainer>
      </Card>
      <Card>
        <h2 className="font-medium">Students</h2>
        {(overview.data?.students || []).map((s) => (
          <p key={s.id} className="text-sm">
            {s.name}
          </p>
        ))}
      </Card>
    </div>
  )
}
