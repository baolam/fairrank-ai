import { create } from 'zustand'
import { DEFAULT_JOB_DESCRIPTION, DEFAULT_JOB_TITLE, SAMPLE_CANDIDATES } from '../data/sampleCandidates'
import type { CandidateRecord, LastRunState, ParetoPoint } from '../types/api'

export type WizardStep = 1 | 2 | 3

interface RankingStore {
  step: WizardStep
  jobTitle: string
  jobDescription: string
  candidatesPool: CandidateRecord[]
  lastRun: LastRunState | null
  paretoCache: ParetoPoint[] | null
  setStep: (step: WizardStep) => void
  setJobInputs: (title: string, description: string) => void
  setCandidatesPool: (pool: CandidateRecord[]) => void
  setLastRun: (run: LastRunState) => void
  setParetoCache: (points: ParetoPoint[]) => void
  restartAtStep1: () => void
  startJobWorkflow: (jobTitle: string, jobDescription: string) => void
}

export const useRankingStore = create<RankingStore>((set) => ({
  step: 1,
  jobTitle: DEFAULT_JOB_TITLE,
  jobDescription: DEFAULT_JOB_DESCRIPTION,
  candidatesPool: SAMPLE_CANDIDATES,
  lastRun: null,
  paretoCache: null,
  setStep: (step) => set({ step }),
  setJobInputs: (jobTitle, jobDescription) => set({ jobTitle, jobDescription }),
  setCandidatesPool: (candidatesPool) => set({ candidatesPool }),
  setLastRun: (run) => set({ lastRun: run, paretoCache: null }),
  setParetoCache: (points) => set({ paretoCache: points }),
  restartAtStep1: () => set({ step: 1, lastRun: null, paretoCache: null }),
  startJobWorkflow: (jobTitle, jobDescription) =>
    set({
      step: 1,
      jobTitle,
      jobDescription,
      candidatesPool: [],
      lastRun: null,
      paretoCache: null,
    }),
}))
