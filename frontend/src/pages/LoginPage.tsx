import { FormEvent, useState } from 'react'
import { LockKeyhole, Mail } from 'lucide-react'
import { apiFetch } from '../api'

type Props = { onLogin: () => Promise<void> }

export default function LoginPage({ onLogin }: Props) {
  const [email,setEmail]=useState('')
  const [password,setPassword]=useState('')
  const [error,setError]=useState('')
  const [loading,setLoading]=useState(false)
  async function submit(e:FormEvent){
    e.preventDefault(); setError(''); setLoading(true)
    try {
      const data=await apiFetch('/auth/login',{method:'POST',body:JSON.stringify({email,password})})
      localStorage.setItem('sgv_token',data.access_token)
      await onLogin()
    } catch(err:any){ setError(err.message || 'No fue posible iniciar sesión') } finally { setLoading(false) }
  }
  return <main className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-amber-50 p-6">
    <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-6xl items-center justify-center">
      <div className="grid w-full overflow-hidden rounded-3xl bg-white shadow-2xl shadow-emerald-950/10 lg:grid-cols-2">
        <section className="hidden bg-[#3A6C32] p-12 text-white lg:flex lg:flex-col lg:justify-between">
          <div><img src="/epmvs-logo.webp" alt="EPM Vivienda Samborondón" className="w-72 rounded-2xl bg-white p-4" /></div>
          <div><p className="text-sm uppercase tracking-[0.24em] text-emerald-200">Empresa Pública Municipal</p><h1 className="mt-3 text-4xl font-semibold leading-tight">Sistema de Gestión y Venta EPMVS</h1><p className="mt-4 max-w-md text-emerald-100">Gestión de clientes, predios, ventas, pagos y cartera del Proyecto San Joaquín.</p></div>
          <div className="h-1 w-28 rounded-full bg-[#FAB71C]"/>
        </section>
        <section className="p-8 sm:p-12 lg:p-14">
          <img src="/epmvs-logo.webp" alt="EPMVS" className="mb-8 w-52 lg:hidden"/>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#52AD56]">Acceso institucional</p>
          <h2 className="mt-2 text-3xl font-semibold text-slate-900">Iniciar sesión</h2>
          <p className="mt-2 text-sm text-slate-500">Ingrese sus credenciales autorizadas.</p>
          <form onSubmit={submit} className="mt-8 space-y-5">
            <label className="block"><span className="text-sm font-medium text-slate-700">Correo electrónico</span><div className="mt-2 flex items-center rounded-xl border border-slate-200 px-3 focus-within:border-[#52AD56] focus-within:ring-2 focus-within:ring-emerald-100"><Mail className="h-5 w-5 text-slate-400"/><input value={email} onChange={e=>setEmail(e.target.value)} type="email" required className="w-full border-0 bg-transparent px-3 py-3 outline-none" placeholder="usuario@epmvs.gob.ec"/></div></label>
            <label className="block"><span className="text-sm font-medium text-slate-700">Contraseña</span><div className="mt-2 flex items-center rounded-xl border border-slate-200 px-3 focus-within:border-[#52AD56] focus-within:ring-2 focus-within:ring-emerald-100"><LockKeyhole className="h-5 w-5 text-slate-400"/><input value={password} onChange={e=>setPassword(e.target.value)} type="password" required className="w-full border-0 bg-transparent px-3 py-3 outline-none" placeholder="••••••••"/></div></label>
            {error && <p className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
            <button disabled={loading} className="w-full rounded-xl bg-[#3A6C32] px-4 py-3 font-semibold text-white transition hover:bg-[#315c2b] disabled:opacity-60">{loading?'Ingresando…':'Ingresar'}</button>
          </form>
        </section>
      </div>
    </div>
  </main>
}
