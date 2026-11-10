import { create } from 'zustand'
import { setRecruiterCode } from '../lib/apiClient'

const STORAGE_KEY = 'fairrank_recruiter_code'

interface AuthStore {
  isAuthed: boolean
  login: (code: string) => void
  logout: () => void
}

const storedCode = (() => {
  try {
    return sessionStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
})()

if (storedCode) {
  setRecruiterCode(storedCode)
}

export const useAuthStore = create<AuthStore>((set) => ({
  isAuthed: Boolean(storedCode),
  login: (code) => {
    setRecruiterCode(code)
    try {
      sessionStorage.setItem(STORAGE_KEY, code)
    } catch {
      /* sessionStorage unavailable (private window, blocked storage) — session-only auth still works */
    }
    set({ isAuthed: true })
  },
  logout: () => {
    setRecruiterCode(null)
    try {
      sessionStorage.removeItem(STORAGE_KEY)
    } catch {
      /* ignore */
    }
    set({ isAuthed: false })
  },
}))
