import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getJob } from '../lib/apiClient'
import { useRankingStore, type WizardStep } from '../store/useRankingStore'
import { useAuthStore } from '../store/useAuthStore'
import { Stepper } from '../components/Stepper'
import { JobApplicationsStep } from '../components/steps/JobApplicationsStep'
import { ConfigureRunStep } from '../components/steps/ConfigureRunStep'
import { ResultsCompareStep } from '../components/steps/ResultsCompareStep'
import type { JobPosting } from '../types/api'

export function RecruiterJobWorkspace() {
  const { jobId } = useParams<{ jobId: string }>()
  const logout = useAuthStore((s) => s.logout)

  const step = useRankingStore((s) => s.step)
  const setStep = useRankingStore((s) => s.setStep)
  const candidatesPool = useRankingStore((s) => s.candidatesPool)
  const lastRun = useRankingStore((s) => s.lastRun)
  const startJobWorkflow = useRankingStore((s) => s.startJobWorkflow)

  const [job, setJob] = useState<JobPosting | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) return
    getJob(jobId)
      .then((data) => {
        setJob(data)
        startJobWorkflow(data.title, data.description)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Không tải được job.'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId])

  function canNavigateTo(target: WizardStep) {
    if (target === 1) return true
    if (target === 2) return candidatesPool.length > 0
    if (target === 3) return lastRun !== null
    return false
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f6f5fb] px-4">
        <p className="text-sm text-red-600">{error}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#f6f5fb] px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <Link to="/recruiter" className="text-sm font-medium text-brand-700 underline">
              ← Danh sách job
            </Link>
            <h1 className="mt-1 text-2xl font-bold text-gray-900">{job?.title ?? 'Đang tải…'}</h1>
          </div>
          <button type="button" className="text-sm font-medium text-red-600 hover:text-red-700" onClick={logout}>
            Đăng xuất
          </button>
        </header>

        <Stepper currentStep={step} canNavigateTo={canNavigateTo} onNavigate={setStep} />

        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          {step === 1 && jobId && <JobApplicationsStep jobId={jobId} />}
          {step === 2 && <ConfigureRunStep />}
          {step === 3 && <ResultsCompareStep />}
        </section>
      </div>
    </div>
  )
}
