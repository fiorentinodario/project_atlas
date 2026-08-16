export type User = {
  id: string
  email: string
  display_name: string
}

export type AuthResponse = {
  data: {
    access_token: string
    user: User
  }
}

export type Credentials = {
  email: string
  password: string
}

export type Registration = Credentials & {
  display_name: string
}
