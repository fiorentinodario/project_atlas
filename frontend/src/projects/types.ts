export type ProjectRole = 'OWNER' | 'ADMIN' | 'MEMBER' | 'VIEWER'
export type ProjectStatus = 'ACTIVE' | 'ARCHIVED'

export type Project = {
  id: string
  name: string
  description: string | null
  status: ProjectStatus
  role: ProjectRole
  owner: {
    id: string
    display_name: string
  }
  created_at: string
  updated_at: string
}

export type ProjectListResponse = {
  data: {
    items: Project[]
    pagination: {
      page: number
      per_page: number
      total: number
      pages: number
    }
  }
}
