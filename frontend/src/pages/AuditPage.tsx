import { useEffect, useState } from 'react'
import { History, Search } from 'lucide-react'
import { apiFetch } from '../api'

const ACTIONS:any={
  USER_CREATE:'Usuario creado',
  USER_UPDATE:'Usuario actualizado',
  USER_PASSWORD_RESET:'Contraseña cambiada',
  ROLE_UPDATE:'Rol actualizado',
  CUSTOMER_CREATE:'Cliente creado',
  CUSTOMER_UPDATE:'Cliente actualizado',
  PROPERTY_CREATE:'Predio creado',
  RESERVATION_CREATE:'Reserva creada',
  RESERVATION_CANCEL:'Reserva cancelada',
  SALE_CONFIRM:'Compra confirmada',
  PAYMENT_CREATE:'Pago registrado',
}

export default function AuditPage(){
  const [rows,setRows]=useState<any[]>([])
  const [email,setEmail]=useState('')
  const [action,setAction]=useState('')
  const [loading,setLoading]=useState(false)
  async function load(){
    setLoading(true)
    const p=new URLSearchParams()
    if(email)p.set('user_email',email)
    if(action)p.set('action',action)
    try{setRows(await apiFetch('/security/audit?'+p.toString()))}finally{setLoading(false)}
  }
  useEffect(()=>{load()},[])
  return <div>
    <div><p className="text-sm font-semibold text-[#52AD56]">Trazabilidad</p><h2 className="mt-1 text-2xl font-semibold">Auditoría</h2><p className="mt-1 text-sm text-slate-500">Historial de acciones administrativas y de seguridad.</p></div>
    <div className="mt-6 flex flex-wrap gap-3 rounded-2xl border bg-white p-4 shadow-sm"><div className="flex min-w-64 flex-1 items-center rounded-xl border px-3"><Search className="h-4 w-4 text-slate-400"/><input value={email} onChange={e=>setEmail(e.target.value)} onKeyDown={e=>e.key==='Enter'&&load()} placeholder="Correo del usuario" className="w-full px-3 py-2 outline-none"/></div><select value={action} onChange={e=>setAction(e.target.value)} className="rounded-xl border px-3 py-2"><option value="">Todas las acciones</option>{Object.entries(ACTIONS).map(([k,v])=><option key={k} value={k}>{String(v)}</option>)}</select><button onClick={load} className="rounded-xl bg-[#3A6C32] px-4 py-2 text-sm font-semibold text-white">Filtrar</button></div>
    <div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm"><div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Fecha</th><th className="px-4 py-3">Usuario</th><th className="px-4 py-3">Acción</th><th className="px-4 py-3">Objeto</th><th className="px-4 py-3">IP</th><th className="px-4 py-3">Detalle</th></tr></thead><tbody>{rows.map(r=><tr key={r.id} className="border-t align-top"><td className="whitespace-nowrap px-4 py-3">{new Date(r.created_at).toLocaleString('es-EC')}</td><td className="px-4 py-3">{r.user_email||'Sistema'}</td><td className="px-4 py-3 font-medium">{ACTIONS[r.action]||r.action}</td><td className="px-4 py-3">{r.target_type}<br/><span className="text-xs text-slate-400">{r.target_id||''}</span></td><td className="px-4 py-3">{r.ip_address||'-'}</td><td className="max-w-md px-4 py-3"><pre className="whitespace-pre-wrap break-words text-xs text-slate-500">{r.details?JSON.stringify(r.details,null,2):'-'}</pre></td></tr>)}</tbody></table>{!rows.length&&!loading&&<div className="py-14 text-center text-slate-400"><History className="mx-auto h-10 w-10"/><p className="mt-3">No existen registros de auditoría.</p></div>}{loading&&<div className="py-10 text-center text-sm text-slate-500">Cargando auditoría…</div>}</div></div>
  </div>
}
