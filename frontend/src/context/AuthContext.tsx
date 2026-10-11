import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, getStoredUser, storeUser, type User } from '../lib/api'

type Auth = {
  user: User | null
  login: (id: number) => Promise<void>
  logout: () => void
}

const Ctx = createContext<Auth | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(getStoredUser())
  useEffect(() => {
    storeUser(user)
  }, [user])
  const value = useMemo<Auth>(
    () => ({
      user,
      login: async (id: number) => {
        const u = await api<User>('/auth/login', { method: 'POST', body: JSON.stringify({ user_id: id }) })
        setUser(u)
      },
      logout: () => setUser(null),
    }),
    [user],
  )
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useAuth() {
  const v = useContext(Ctx)
  if (!v) throw new Error('auth')
  return v
}
