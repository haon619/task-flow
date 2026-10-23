import { useCallback, useEffect, useState } from 'react'
import { ApiError, login, logout, me, register } from './api'
import type { User } from './api'
import BoardScreen from './BoardScreen'

function AuthForm({ onDone }: { onDone: (user: User) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try {
      const fn = mode === 'login' ? login : register
      onDone(await fn(username, password))
    } catch (err) {
      if (err instanceof ApiError && err.kind === 'unauthorized') {
        setError('아이디 또는 비밀번호가 맞지 않습니다.')
      } else if (err instanceof ApiError && err.kind === 'invalid') {
        setError('아이디는 1~50자, 비밀번호는 8자 이상이어야 합니다.')
      } else {
        setError(err instanceof Error ? err.message : '처리하지 못했습니다.')
      }
    }
  }

  return (
    <main>
      <h1>Task Flow</h1>
      <form onSubmit={submit}>
        <h2>{mode === 'login' ? '로그인' : '가입'}</h2>
        <input
          aria-label="아이디"
          placeholder="아이디"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          aria-label="비밀번호"
          type="password"
          placeholder="비밀번호 (8자 이상)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit">{mode === 'login' ? '로그인' : '가입하고 시작'}</button>
        <button
          type="button"
          onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
        >
          {mode === 'login' ? '계정 만들기' : '로그인으로'}
        </button>
        {error && (
          <p className="notice error" role="alert">
            {error}
          </p>
        )}
      </form>
    </main>
  )
}

function App() {
  // undefined: 확인 중, null: 로그인 안 됨
  const [user, setUser] = useState<User | null | undefined>(undefined)

  useEffect(() => {
    me()
      .then(setUser)
      .catch(() => setUser(null))
  }, [])

  const handleUnauthorized = useCallback(() => setUser(null), [])

  async function handleLogout() {
    await logout().catch(() => undefined)
    setUser(null)
  }

  if (user === undefined) return <p className="notice">불러오는 중…</p>
  if (user === null) return <AuthForm onDone={setUser} />
  return (
    <>
      <p className="notice">
        {user.username}님 ·{' '}
        <button type="button" onClick={handleLogout}>
          로그아웃
        </button>
      </p>
      <BoardScreen key={user.id} onUnauthorized={handleUnauthorized} />
    </>
  )
}

export default App
