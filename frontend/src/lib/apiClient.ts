import axios from 'axios'
import type {
  ApplicationRecord,
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

export async function listJobs(): Promise<JobPosting[]> {
  const { data } = await apiClient.get<JobPosting[]>('/v1/jobs')
  return data
}

export async function getJob(jobId: string): Promise<JobPosting> {
  const { data } = await apiClient.get<JobPosting>(`/v1/jobs/${jobId}`)
  return data
}

export async function createJob(title: string, description: string): Promise<JobPosting> {
  const { data } = await apiClient.post<JobPosting>('/v1/jobs', { title, description })
  return data
}

export async function submitApplication(
  jobId: string,
  candidateName: string,
  declaredGroup: string | null,
  file: File,
): Promise<ApplicationSubmitResult> {
  const form = new FormData()
  form.append('candidate_name', candidateName)
  if (declaredGroup) form.append('declared_group', declaredGroup)
  form.append('file', file)
  const { data } = await apiClient.post<ApplicationSubmitResult>(
    `/v1/jobs/${jobId}/applications`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

export async function listApplications(jobId: string): Promise<ApplicationRecord[]> {
  const { data } = await apiClient.get<ApplicationRecord[]>(`/v1/jobs/${jobId}/applications`)
  return data
}
