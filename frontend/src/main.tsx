import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { RoleSelectLanding } from './pages/RoleSelectLanding.tsx'
import { CandidateApplyPage } from './pages/CandidateApplyPage.tsx'
import { RecruiterGate } from './pages/RecruiterGate.tsx'
import { RecruiterDashboard } from './pages/RecruiterDashboard.tsx'
import { RecruiterJobWorkspace } from './pages/RecruiterJobWorkspace.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RoleSelectLanding />} />
        <Route path="/apply" element={<CandidateApplyPage />} />
        <Route path="/quick-demo" element={<App />} />
        <Route element={<RecruiterGate />}>
          <Route path="/recruiter" element={<RecruiterDashboard />} />
          <Route path="/recruiter/:jobId" element={<RecruiterJobWorkspace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
