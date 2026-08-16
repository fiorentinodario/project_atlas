import { apiRequest } from '../lib/api'
import type { DashboardData } from './types'

export function getDashboard(accessToken: string) {
  return apiRequest<{ data: DashboardData }>('/dashboard', {}, accessToken)
}
