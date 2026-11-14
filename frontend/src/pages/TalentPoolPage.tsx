import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { searchTalentPool } from '../lib/apiClient'
import { CandidateDetailDrawer } from '../components/ats/CandidateDetailDrawer'
import type { CandidateApplicationFull } from '../types/ats'
import { ATS_STAGES } from '../types/ats'

export function TalentPoolPage() {
  const [candidates, setCandidates] = useState<CandidateApplicationFull[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [searchQuery, setSearchQuery] = useState('')
  const [skillFilter, setSkillFilter] = useState('')
  const [minExp, setMinExp] = useState<number | ''>('')
  const [stageFilter, setStageFilter] = useState('all')

  // Drawer
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateApplicationFull | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  function loadCandidates() {
    setLoading(true)
    setError(null)
    searchTalentPool({
      query: searchQuery.trim() || undefined,
      skill: skillFilter.trim() || undefined,
      min_exp: minExp !== '' ? Number(minExp) : undefined,
      stage: stageFilter !== 'all' ? stageFilter : undefined,
    })
      .then(setCandidates)
      .catch((err) => setError(err instanceof Error ? err.message : 'Không tải được kho tài năng.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadCandidates()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stageFilter])

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault()
    loadCandidates()
  }

  function handleOpenCandidate(cand: CandidateApplicationFull) {
    setSelectedCandidate(cand)
    setDrawerOpen(true)
  }

  return (
    <div className="min-h-screen bg-[#f6f5fb] px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">👥</span>
              <h1 className="text-2xl font-bold text-gray-900">Kho Tài Năng Toàn Cục (Central Talent Pool)</h1>
            </div>
            <p className="text-sm text-gray-500 mt-0.5">
              Tra cứu, tìm kiếm và tái tương tác với toàn bộ ứng viên đã từng nộp hồ sơ trên mọi chiến dịch tuyển dụng.
            </p>
          </div>
          <Link
            to="/recruiter"
            className="rounded-lg border border-gray-300 bg-white px-3.5 py-1.5 text-xs font-semibold text-gray-700 shadow-xs hover:bg-gray-50"
          >
            ← Bảng điều khiển Jobs
          </Link>
        </header>

        {/* Search & Filter Toolbar */}
        <form
          onSubmit={handleSearchSubmit}
          className="mb-6 grid grid-cols-1 sm:grid-cols-5 gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-xs text-xs"
        >
          <div className="sm:col-span-2">
            <label className="block text-gray-500 mb-1">Tìm theo Tên, Chức danh, Email:</label>
            <input
              type="text"
              placeholder="VD: Nguyen, Developer..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-gray-300 p-2"
            />
          </div>

          <div>
            <label className="block text-gray-500 mb-1">Kỹ năng cốt lõi:</label>
            <input
              type="text"
              placeholder="VD: Python, React..."
              value={skillFilter}
              onChange={(e) => setSkillFilter(e.target.value)}
              className="w-full rounded-lg border border-gray-300 p-2"
            />
          </div>

          <div>
            <label className="block text-gray-500 mb-1">Kinh nghiệm tối thiểu:</label>
            <input
              type="number"
              min={0}
              placeholder="Số năm"
              value={minExp}
              onChange={(e) => setMinExp(e.target.value ? Number(e.target.value) : '')}
              className="w-full rounded-lg border border-gray-300 p-2"
            />
          </div>

          <div className="flex items-end gap-2">
            <div className="flex-1">
              <label className="block text-gray-500 mb-1">Giai đoạn:</label>
              <select
                value={stageFilter}
                onChange={(e) => setStageFilter(e.target.value)}
                className="w-full rounded-lg border border-gray-300 p-2"
              >
                <option value="all">Tất cả giai đoạn</option>
                {ATS_STAGES.map((st) => (
                  <option key={st.id} value={st.id}>
                    {st.label}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              className="rounded-lg bg-brand-600 px-4 py-2 font-semibold text-white hover:bg-brand-700 shadow-xs"
            >
              Tìm
            </button>
          </div>
        </form>

        {error && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

        {/* Results List */}
        {loading && <p className="text-center py-10 text-sm text-gray-500">Đang tìm kiếm trong kho tài năng…</p>}

        {!loading && candidates.length === 0 && (
          <div className="rounded-2xl border border-gray-200 bg-white p-10 text-center">
            <span className="text-4xl">🔍</span>
            <h3 className="mt-2 text-base font-bold text-gray-900">Không tìm thấy ứng viên phù hợp</h3>
            <p className="mt-1 text-sm text-gray-500">Hãy thử nới lỏng từ khóa hoặc bộ lọc kinh nghiệm.</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {candidates.map((cand) => {
            const stageDef = ATS_STAGES.find((s) => s.id === cand.stage) || ATS_STAGES[0]
            return (
              <div
                key={cand.id}
                onClick={() => handleOpenCandidate(cand)}
                className="group cursor-pointer rounded-2xl border border-gray-200 bg-white p-4 shadow-xs transition-all hover:border-brand-500 hover:shadow-md flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="text-base font-bold text-gray-900 group-hover:text-brand-600 transition-colors">
                        {cand.candidate_name}
                      </h3>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {cand.current_title || 'Ứng viên'} · {cand.years_of_experience ? `${cand.years_of_experience} năm kn` : 'N/A'}
                      </p>
                    </div>
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${stageDef.badge}`}>
                      {stageDef.label}
                    </span>
                  </div>

                  <div className="mt-2 text-xs text-gray-500">
                    <p>🎯 Đã nộp vào: <span className="font-medium text-gray-700">{cand.job_title}</span></p>
                    {cand.email && <p>✉️ {cand.email}</p>}
                    {cand.location && <p>📍 {cand.location}</p>}
                  </div>

                  {cand.skills && cand.skills.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {cand.skills.slice(0, 4).map((s, idx) => (
                        <span key={idx} className="rounded-md bg-gray-100 px-2 py-0.5 text-[11px] text-gray-600">
                          {s}
                        </span>
                      ))}
                      {cand.skills.length > 4 && (
                        <span className="text-[11px] text-gray-400 self-center">+{cand.skills.length - 4}</span>
                      )}
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                  <span className="text-amber-500 font-semibold">
                    {cand.overall_rating && cand.overall_rating > 0 ? `★ ${cand.overall_rating}` : 'Chưa chấm'}
                  </span>
                  <span className="font-semibold text-brand-600 group-hover:translate-x-0.5 transition-transform">
                    Xem chi tiết →
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Candidate Detail Slide-Over Drawer */}
      <CandidateDetailDrawer
        candidate={selectedCandidate}
        jobTitle={selectedCandidate?.job_title || 'Kho Tài Năng'}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onUpdated={loadCandidates}
      />
    </div>
  )
}
