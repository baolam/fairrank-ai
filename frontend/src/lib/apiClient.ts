import axios from 'axios'
import type {
  ApplicationSubmitResult,
  CounterfactualAuditRequestPayload,
  CounterfactualAuditResponse,
  JobPosting,
  ParetoPoint,
  ParetoSweepRequestPayload,
  ParsedResume,
  RankingRequestPayload,
  RankingResponse,
  ReportExportRequestPayload,
} from '../types/api'
import type {
  AICriteria,
  ApplicationStage,
  CandidateApplicationFull,
  EmailLogRecord,
  InterviewRecord,
  JobFunnelAnalytics,
  JobPostingFull,
  RecruiterNoteRecord,
  ScorecardRecord,
} from '../types/ats'

const baseURL = import.meta.env.VITE_API_BASE_URL ?? '/api'

export const apiClient = axios.create({ baseURL })

let recruiterCode: string | null = null

export function setRecruiterCode(code: string | null) {
  recruiterCode = code
}

apiClient.interceptors.request.use((config) => {
  if (recruiterCode) {
    config.headers['X-Recruiter-Code'] = recruiterCode
  }
  return config
})

// =============================================================================
// Document Parsing & Algorithmic Ranking / Audit
// =============================================================================

export async function parseResumeFile(file: File): Promise<ParsedResume> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<ParsedResume>(
    '/v1/ingestion/parse-file',
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

export async function parseResumeFiles(files: File[]): Promise<ParsedResume[]> {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  const { data } = await apiClient.post<ParsedResume[]>(
    '/v1/ingestion/parse-files',
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

export async function executeRanking(
  payload: RankingRequestPayload,
): Promise<RankingResponse> {
  const { data } = await apiClient.post<RankingResponse>(
    '/v1/ranking/execute',
    payload,
  )
  return data
}

export async function computeParetoSweep(
  payload: ParetoSweepRequestPayload,
): Promise<ParetoPoint[]> {
  const { data } = await apiClient.post<ParetoPoint[]>(
    '/v1/audit/pareto-sweep',
    payload,
  )
  return data
}

export async function runCounterfactualAudit(
  payload: CounterfactualAuditRequestPayload,
): Promise<CounterfactualAuditResponse> {
  const { data } = await apiClient.post<CounterfactualAuditResponse>(
    '/v1/audit/counterfactual',
    payload,
  )
  return data
}

export async function exportMarkdownReport(
  payload: ReportExportRequestPayload,
): Promise<string> {
  const { data } = await apiClient.post<string>('/v1/report/markdown', payload, {
    responseType: 'text',
  })
  return data
}

export async function exportHtmlReport(
  payload: ReportExportRequestPayload,
): Promise<string> {
  const { data } = await apiClient.post<string>('/v1/report/html', payload, {
    responseType: 'text',
  })
  return data
}

export async function recruiterLogin(code: string): Promise<boolean> {
  try {
    await apiClient.post('/v1/auth/recruiter-login', { code })
    return true
  } catch {
    return false
  }
}

// =============================================================================
// Enterprise Job Postings CRUD
// =============================================================================

export async function listJobs(params?: {
  status?: string
  department?: string
  search?: string
}): Promise<JobPostingFull[]> {
  const { data } = await apiClient.get<JobPostingFull[]>('/v1/jobs', { params })
  return data
}

export async function getJob(jobId: string): Promise<JobPostingFull> {
  const { data } = await apiClient.get<JobPostingFull>(`/v1/jobs/${jobId}`)
  return data
}

export async function createJob(title: string, description: string): Promise<JobPosting> {
  const { data } = await apiClient.post<JobPosting>('/v1/jobs', { title, description })
  return data
}

export async function createJobFull(jobData: Partial<JobPostingFull>): Promise<JobPostingFull> {
  const { data } = await apiClient.post<JobPostingFull>('/v1/jobs', jobData)
  return data
}

export async function updateJob(jobId: string, jobData: Partial<JobPostingFull>): Promise<JobPostingFull> {
  const { data } = await apiClient.patch<JobPostingFull>(`/v1/jobs/${jobId}`, jobData)
  return data
}

export async function deleteJob(jobId: string): Promise<void> {
  await apiClient.delete(`/v1/jobs/${jobId}`)
}

// =============================================================================
// Candidate Application & ATS Workflows
// =============================================================================

export async function submitApplication(
  jobId: string,
  candidateName: string,
  declaredGroup: string | null,
  file: File,
  extra?: {
    email?: string
    phone?: string
    currentTitle?: string
    location?: string
    linkedinUrl?: string
  },
): Promise<ApplicationSubmitResult> {
  const form = new FormData()
  form.append('candidate_name', candidateName)
  if (declaredGroup) form.append('declared_group', declaredGroup)
  if (extra?.email) form.append('email', extra.email)
  if (extra?.phone) form.append('phone', extra.phone)
  if (extra?.currentTitle) form.append('current_title', extra.currentTitle)
  if (extra?.location) form.append('location', extra.location)
  if (extra?.linkedinUrl) form.append('linkedin_url', extra.linkedinUrl)
  form.append('file', file)

  const { data } = await apiClient.post<ApplicationSubmitResult>(
    `/v1/jobs/${jobId}/applications`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

export async function listApplications(
  jobId: string,
  params?: { stage?: string; search?: string },
): Promise<CandidateApplicationFull[]> {
  const { data } = await apiClient.get<CandidateApplicationFull[]>(`/v1/jobs/${jobId}/applications`, {
    params,
  })
  return data
}

export async function getApplication(
  jobId: string,
  appId: string,
): Promise<CandidateApplicationFull> {
  const { data } = await apiClient.get<CandidateApplicationFull>(`/v1/jobs/${jobId}/applications/${appId}`)
  return data
}

export async function updateApplicationStage(
  jobId: string,
  appId: string,
  stage: ApplicationStage,
  rejectionReason?: string,
): Promise<CandidateApplicationFull> {
  const { data } = await apiClient.patch<CandidateApplicationFull>(
    `/v1/jobs/${jobId}/applications/${appId}/stage`,
    { stage, rejection_reason: rejectionReason },
  )
  return data
}

export async function updateApplicationRating(
  jobId: string,
  appId: string,
  rating: number,
): Promise<CandidateApplicationFull> {
  const { data } = await apiClient.patch<CandidateApplicationFull>(
    `/v1/jobs/${jobId}/applications/${appId}/rating`,
    { rating },
  )
  return data
}

// =============================================================================
// Scorecards, Notes, Interviews, and Emails
// =============================================================================

export async function createScorecard(
  jobId: string,
  appId: string,
  scorecard: {
    evaluator_name: string
    overall_recommendation: string
    technical_score: number
    communication_score: number
    experience_score: number
    notes?: string
  },
): Promise<ScorecardRecord> {
  const { data } = await apiClient.post<ScorecardRecord>(
    `/v1/jobs/${jobId}/applications/${appId}/scorecards`,
    scorecard,
  )
  return data
}

export async function listScorecards(jobId: string, appId: string): Promise<ScorecardRecord[]> {
  const { data } = await apiClient.get<ScorecardRecord[]>(
    `/v1/jobs/${jobId}/applications/${appId}/scorecards`,
  )
  return data
}

export async function createNote(
  jobId: string,
  appId: string,
  authorName: string,
  content: string,
): Promise<RecruiterNoteRecord> {
  const { data } = await apiClient.post<RecruiterNoteRecord>(
    `/v1/jobs/${jobId}/applications/${appId}/notes`,
    { author_name: authorName, content },
  )
  return data
}

export async function listNotes(jobId: string, appId: string): Promise<RecruiterNoteRecord[]> {
  const { data } = await apiClient.get<RecruiterNoteRecord[]>(
    `/v1/jobs/${jobId}/applications/${appId}/notes`,
  )
  return data
}

export async function scheduleInterview(
  jobId: string,
  appId: string,
  interviewData: {
    round_type: string
    scheduled_at: string
    interviewer_name: string
    duration_minutes?: number
    meeting_link?: string
    location?: string
    notes?: string
  },
): Promise<InterviewRecord> {
  const { data } = await apiClient.post<InterviewRecord>(
    `/v1/jobs/${jobId}/applications/${appId}/interviews`,
    interviewData,
  )
  return data
}

export async function listJobInterviews(jobId: string): Promise<InterviewRecord[]> {
  const { data } = await apiClient.get<InterviewRecord[]>(`/v1/jobs/${jobId}/interviews`)
  return data
}

export async function listCandidateInterviews(jobId: string, appId: string): Promise<InterviewRecord[]> {
  const { data } = await apiClient.get<InterviewRecord[]>(`/v1/jobs/${jobId}/applications/${appId}/interviews`)
  return data
}

export async function updateInterviewStatus(
  jobId: string,
  interviewId: string,
  status: string,
): Promise<InterviewRecord> {
  const { data } = await apiClient.patch<InterviewRecord>(
    `/v1/jobs/${jobId}/interviews/${interviewId}`,
    { status },
  )
  return data
}

export async function sendCandidateEmail(
  jobId: string,
  appId: string,
  payload: {
    template_type: string
    recipient_email: string
    subject: string
    body: string
  },
): Promise<EmailLogRecord> {
  const { data } = await apiClient.post<EmailLogRecord>(
    `/v1/jobs/${jobId}/applications/${appId}/send-email`,
    payload,
  )
  return data
}

export async function listEmailLogs(jobId: string, appId: string): Promise<EmailLogRecord[]> {
  const { data } = await apiClient.get<EmailLogRecord[]>(
    `/v1/jobs/${jobId}/applications/${appId}/emails`,
  )
  return data
}

export async function getJobAnalytics(jobId: string): Promise<JobFunnelAnalytics> {
  const { data } = await apiClient.get<JobFunnelAnalytics>(`/v1/jobs/${jobId}/analytics`)
  return data
}

export async function searchTalentPool(params?: {
  query?: string
  skill?: string
  min_exp?: number
  stage?: string
}): Promise<CandidateApplicationFull[]> {
  const { data } = await apiClient.get<CandidateApplicationFull[]>('/v1/candidates', { params })
  return data
}

export async function runFairScreening(
  jobId: string,
  payload?: {
    model_name?: string
    redaction_enabled?: boolean
    lambda_penalty?: number
    cutoff_k?: number
    target_stage?: string
    from_stage?: string
  },
): Promise<{ processed_count: number; target_stage: string; message: string }> {
  const { data } = await apiClient.post<{ processed_count: number; target_stage: string; message: string }>(
    `/v1/jobs/${jobId}/run-fair-screening`,
    payload || {},
  )
  return data
}

export async function advanceTopCandidates(
  jobId: string,
  params?: {
    topK?: number
    minScore?: number
    candidateIds?: string[]
    targetStage?: string
    fromStage?: string
  } | number,
  legacyTargetStage: string = 'shortlisted',
): Promise<{ advanced_count: number; target_stage: string }> {
  const payload = typeof params === 'number'
    ? { top_k: params, target_stage: legacyTargetStage }
    : {
        top_k: params?.topK,
        min_score: params?.minScore,
        candidate_ids: params?.candidateIds,
        target_stage: params?.targetStage ?? 'shortlisted',
        from_stage: params?.fromStage ?? 'screening',
      }
  const { data } = await apiClient.post<{ advanced_count: number; target_stage: string }>(
    `/v1/jobs/${jobId}/advance-top-candidates`,
    payload,
  )
  return data
}

export async function getJobAICriteria(jobId: string): Promise<AICriteria> {
  const { data } = await apiClient.get<AICriteria>(`/v1/jobs/${jobId}/ai-criteria`)
  return data
}

export async function updateJobAICriteria(
  jobId: string,
  criteria: AICriteria,
  reScore: boolean = true,
): Promise<AICriteria> {
  const { data } = await apiClient.put<AICriteria>(
    `/v1/jobs/${jobId}/ai-criteria`,
    criteria,
    { params: { re_score: reScore } },
  )
  return data
}

export async function reScoreJobApplications(
  jobId: string,
): Promise<{ job_id: string; rescored_count: number; message: string }> {
  const { data } = await apiClient.post<{ job_id: string; rescored_count: number; message: string }>(
    `/v1/jobs/${jobId}/re-score`,
  )
  return data
}

