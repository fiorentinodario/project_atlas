import { CheckCircle2, CircleDot, FolderKanban, ListTodo } from 'lucide-react'

export const stats = [
  { label: 'Active projects', value: '6', change: '+2 this month', icon: FolderKanban, tone: 'bg-violet-50 text-violet-700' },
  { label: 'Total tasks', value: '48', change: 'Across all projects', icon: ListTodo, tone: 'bg-sky-50 text-sky-700' },
  { label: 'In progress', value: '12', change: '25% of all tasks', icon: CircleDot, tone: 'bg-amber-50 text-amber-700' },
  { label: 'Completed', value: '29', change: '+8 this week', icon: CheckCircle2, tone: 'bg-emerald-50 text-emerald-700' },
]

export const projects = [
  { name: 'Merchant Portal', description: 'Self-service platform for retail partners and account teams.', progress: 72, tasks: 18, updated: '12 min ago', tag: 'Product' },
  { name: 'Mobile Redesign', description: 'Research and delivery plan for the next mobile experience.', progress: 46, tasks: 11, updated: 'Yesterday', tag: 'Design' },
  { name: 'API Migration', description: 'Move core integrations to the versioned public API.', progress: 88, tasks: 24, updated: '2 days ago', tag: 'Engineering' },
]

export const activities = [
  { initials: 'DF', text: 'uploaded requirements-v2.pdf', project: 'Merchant Portal', time: '12 minutes ago', color: 'bg-amber-100 text-amber-800' },
  { initials: 'AI', text: 'generated 4 suggested tasks', project: 'API Migration', time: '1 hour ago', color: 'bg-violet-100 text-violet-700' },
  { initials: 'DF', text: 'completed “Create authentication API”', project: 'Merchant Portal', time: '3 hours ago', color: 'bg-emerald-100 text-emerald-700' },
  { initials: 'AI', text: 'finished document analysis', project: 'Mobile Redesign', time: 'Yesterday', color: 'bg-sky-100 text-sky-700' },
]
