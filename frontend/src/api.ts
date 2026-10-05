const API_URL = import.meta.env.VITE_API_URL || '/api'

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem('sgv_token')
  const headers = new Headers(options.headers)
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', 'Bearer ' + token)
  const response = await fetch(API_URL + path, { ...options, headers })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || 'Error de comunicación con el servidor')
  }
  return response.json()
}

export async function apiDownload(path:string, fallbackName:string){
  const token=localStorage.getItem('sgv_token')
  const headers=new Headers()
  if(token) headers.set('Authorization','Bearer '+token)
  const response=await fetch(API_URL+path,{headers})
  if(!response.ok){
    const body=await response.json().catch(()=>({}))
    throw new Error(body.detail||'No fue posible generar el documento')
  }
  const blob=await response.blob()
  const disposition=response.headers.get('Content-Disposition')||''
  const match=disposition.match(/filename="?([^"]+)"?/)
  const filename=match?.[1]||fallbackName
  const url=URL.createObjectURL(blob)
  const a=document.createElement('a')
  a.href=url
  a.download=filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
