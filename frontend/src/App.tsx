import { useEffect, useState } from 'react'
import { LogOut, UserCircle2 } from 'lucide-react'
import { apiFetch } from './api'
import Sidebar, { MobileMenuButton } from './components/Sidebar'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import type { SessionUser } from './types'

export default function App(){
  const [user,setUser]=useState<SessionUser|null>(null)
  const [loading,setLoading]=useState(true)
  const [menuOpen,setMenuOpen]=useState(false)
  const [active,setActive]=useState('Dashboard')
  async function loadUser(){
    try{const data=await apiFetch('/auth/me'); setUser(data)}catch{localStorage.removeItem('sgv_token'); setUser(null)}finally{setLoading(false)}
  }
  useEffect(()=>{loadUser()},[])
  function logout(){localStorage.removeItem('sgv_token'); setUser(null)}
  if(loading) return <div className="flex min-h-screen items-center justify-center text-[#3A6C32]">Cargando SGV EPMVS…</div>
  if(!user) return <LoginPage onLogin={loadUser}/>
  return <div className="min-h-screen bg-slate-50">
    <Sidebar open={menuOpen} setOpen={setMenuOpen} active={active} setActive={setActive}/>
    <div className="lg:pl-72">
      <header className="sticky top-0 z-20 flex h-20 items-center gap-3 border-b bg-white/95 px-5 backdrop-blur lg:px-8">
        <MobileMenuButton onClick={()=>setMenuOpen(true)}/><div className="min-w-0 flex-1"><p className="truncate text-sm text-slate-500">Sistema de Gestión y Venta EPMVS</p><p className="truncate font-semibold text-slate-900">{active}</p></div>
        <div className="hidden items-center gap-3 sm:flex"><UserCircle2 className="h-8 w-8 text-[#3A6C32]"/><div className="text-right"><p className="text-sm font-medium text-slate-800">{user.first_name} {user.last_name}</p><p className="text-xs text-slate-500">{user.roles.join(', ')}</p></div></div>
        <button onClick={logout} className="rounded-xl border p-2.5 text-slate-500 hover:bg-slate-50" title="Cerrar sesión"><LogOut className="h-5 w-5"/></button>
      </header>
      <main className="p-5 lg:p-8">{active==='Dashboard'?<DashboardPage/>:<section className="rounded-2xl border bg-white p-8 shadow-sm"><p className="text-sm font-semibold text-[#52AD56]">Módulo</p><h2 className="mt-1 text-2xl font-semibold text-slate-900">{active}</h2><p className="mt-3 text-slate-500">Estructura preparada. Este módulo será implementado en los siguientes bloques funcionales.</p></section>}</main>
    </div>
  </div>
}
