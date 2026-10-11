import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AuthProvider, useAuth } from './context/AuthContext'
import { Layout } from './components/Layout'
import {
  AnalyticsPage,
  Guard,
  Landing,
  Login,
  ManageSubjects,
  QuizGenerate,
  QuizPlayer,
  QuizResults,
  RecsPage,
  ResourcesPage,
  ReviewPage,
  StudentDashboard,
  SubjectDetail,
  SubjectsPage,
  TopicDetail,
  TrainerHome,
  TwinPage,
  TutorPage,
  UploadPage,
} from './pages/Pages'

const qc = new QueryClient()

function RoleHome() {
  const { user } = useAuth()
  return <Navigate to={user?.role === 'trainer' ? '/app/trainer' : '/app/dashboard'} replace />
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <BrowserRouter>
          <Toaster position="top-right" />
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route
              path="/app"
              element={
                <Guard>
                  <Layout />
                </Guard>
              }
            >
              <Route index element={<RoleHome />} />
              <Route path="dashboard" element={<StudentDashboard />} />
              <Route path="subjects" element={<SubjectsPage />} />
              <Route path="subjects/:id" element={<SubjectDetail />} />
              <Route path="topics/:id" element={<TopicDetail />} />
              <Route path="tutor" element={<TutorPage />} />
              <Route path="quiz/generate" element={<QuizGenerate />} />
              <Route path="quiz/:id" element={<QuizPlayer />} />
              <Route path="results/:id" element={<QuizResults />} />
              <Route path="twin" element={<TwinPage />} />
              <Route path="recommendations" element={<RecsPage />} />
              <Route path="resources" element={<ResourcesPage />} />
              <Route path="trainer" element={<TrainerHome />} />
              <Route path="manage" element={<ManageSubjects />} />
              <Route path="upload" element={<UploadPage />} />
              <Route path="review" element={<ReviewPage />} />
              <Route path="analytics" element={<AnalyticsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
