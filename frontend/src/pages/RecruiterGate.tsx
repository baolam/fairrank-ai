import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { recruiterLogin } from '../lib/apiClient'
import { useAuthStore } from '../store/useAuthStore'

export function RecruiterGate() {
  const isAuthed = useAuthStore((s) => s.isAuthed)
  const login = useAuthStore((s) => s.login)

  const [code, setCode] = useState('')
  const [checking, setChecking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (isAuthed) {
    return <Outlet />
  }

  async function handleSubmit() {
    if (!code.trim()) return
    setChecking(true)
    setError(null)
    const ok = await recruiterLogin(code.trim())
    setChecking(false)
    if (ok) {
      login(code.trim())
    } else {
      setError('Mã truy cập không đúng.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f6f5fb] px-4">
      <div className="w-full max-w-sm rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <h1 className="text-lg font-semibold text-gray-900">🔒 Khu vực Nhà tuyển dụng</h1>
        <p className="mt-1 text-sm text-gray-500">Nhập mã truy cập để xem hồ sơ ứng viên đã nộp.</p>
        <input
          type="password"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          placeholder="Mã truy cập"
          className="mt-4 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <button
          type="button"
          disabled={checking || !code.trim()}
          onClick={handleSubmit}
          className="mt-4 w-full rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {checking ? 'Đang kiểm tra…' : 'Đăng nhập'}
        </button>
      </div>
    </div>
  )
}
