export type SessionUser = {
  id: string
  identification?: string | null
  first_name: string
  last_name: string
  email: string
  roles: string[]
  permissions: string[]
}
