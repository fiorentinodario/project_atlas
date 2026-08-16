import { Navigate, Route, Routes } from 'react-router-dom'
import { GuestRoute, ProtectedRoute } from './auth/RouteGuards'
import { AppLayout } from './components/layout/AppLayout'
import { ComingSoonPage } from './pages/ComingSoonPage'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/auth/LoginPage'
import { RegisterPage } from './pages/auth/RegisterPage'

export function App() {
  return (
    <Routes>
      <Route path="login" element={<GuestRoute><LoginPage /></GuestRoute>} />
      <Route path="register" element={<GuestRoute><RegisterPage /></GuestRoute>} />
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<DashboardPage />} />
        <Route path="projects" element={<ComingSoonPage title="Projects" />} />
        <Route path="tasks" element={<ComingSoonPage title="My tasks" />} />
        <Route path="knowledge" element={<ComingSoonPage title="Knowledge base" />} />
        <Route path="settings" element={<ComingSoonPage title="Settings" />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
