import { FormEvent, useEffect, useState } from 'react'
import { Pencil, Plus, Search, UserRoundCheck } from 'lucide-react'
import { apiFetch } from '../api'

const empty={identification:'',first_name:'',last_name:'',phone:'',email:'',seller_type:'INTERNAL',default_commission_rate:'0',active:true}

export default function SellersPage({permissions}:{permissions:string[]}){
  const [rows,setRows]=useState<any[]>([])
  const [q,setQ]=useState('')
  const [open,setOpen]=useState(false)
  const [editing,setEditing]=useState<any>(null)
  const [form,setForm]=useState<any>(empty)
  const canManage=permissions.includes('system.admin')||permissions.includes('sellers.manage')

  async function load(){setRows(await apiFetch('/sellers'))}
  useEffect(()=>{load()},[])

  function startNew(){setEditing(null);setForm({...empty});setOpen(true)}
  function startEdit(r:any){setEditing(r);setForm({...r,default_commission_rate:String(r.default_commission_rate)});setOpen(true)}
  async function save(e:FormEvent){
    e.preventDefault()
    const body={...form,default_commission_rate:Number(form.default_commission_rate)}
    if(editing) await apiFetch('/sellers/'+editing.id,{method:'PUT',body:JSON.stringify(body)})
    else await apiFetch('/sellers',{method:'POST',body:JSON.stringify(body)})
    setOpen(false);await load()
  }

  const term=q.trim().toLocaleLowerCase('es')
  const filtered=rows.filter((r:any)=>!term||[r.identification,r.full_name,r.phone,r.email].some(v=>String(v??'').toLocaleLowerCase('es').includes(term)))

  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div><p className="text-sm font-semibold text-[#52AD56]">Gestión comercial</p><h2 className="mt-1 text-2xl font-semibold">Vendedores</h2><p className="mt-1 text-sm text-slate-500">Catálogo de vendedores y porcentaje de comisión por defecto.</p></div>
      {canManage&&<button onClick={startNew} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white"><Plus className="h-4 w-4"/>Nuevo vendedor</button>}
    </div>

    <div className="mt-6 rounded-2xl border bg-white p-4 shadow-sm">
      <div className="relative max-w-xl"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"/><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Buscar por identificación, nombre, celular o correo" className="w-full rounded-xl border py-2.5 pl-9 pr-3"/></div>
    </div>

    <div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm"><div className="overflow-x-auto"><table className="min-w-full text-sm">
      <thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3">Identificación</th><th className="px-5 py-3">Vendedor</th><th className="px-5 py-3">Tipo</th><th className="px-5 py-3">Contacto</th><th className="px-5 py-3 text-right">Comisión</th><th className="px-5 py-3">Estado</th><th></th></tr></thead>
      <tbody>{filtered.map((r:any)=><tr key={r.id} className="border-t"><td className="px-5 py-4">{r.identification}</td><td className="px-5 py-4 font-medium">{r.full_name}</td><td className="px-5 py-4">{r.seller_type==='EXTERNAL'?'Externo':'Interno'}</td><td className="px-5 py-4"><div>{r.phone||'-'}</div><div className="text-xs text-slate-400">{r.email||''}</div></td><td className="px-5 py-4 text-right font-semibold">{Number(r.default_commission_rate).toFixed(2)}%</td><td className="px-5 py-4"><span className={'rounded-full px-2.5 py-1 text-xs font-semibold '+(r.active?'bg-emerald-50 text-emerald-700':'bg-slate-100 text-slate-500')}>{r.active?'Activo':'Inactivo'}</span></td><td className="px-5 py-4 text-right">{canManage&&<button onClick={()=>startEdit(r)} className="inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-xs font-semibold"><Pencil className="h-4 w-4"/>Editar</button>}</td></tr>)}</tbody>
    </table>{!filtered.length&&<div className="py-14 text-center text-slate-400"><UserRoundCheck className="mx-auto h-10 w-10"/><p className="mt-3">No hay vendedores registrados.</p></div>}</div></div>

    {open&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={save} className="w-full max-w-2xl rounded-2xl bg-white p-6"><h3 className="text-xl font-semibold">{editing?'Editar vendedor':'Nuevo vendedor'}</h3><div className="mt-5 grid gap-4 sm:grid-cols-2">
      <label>Identificación<input required value={form.identification} onChange={e=>setForm({...form,identification:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label>Tipo<select value={form.seller_type} onChange={e=>setForm({...form,seller_type:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="INTERNAL">Interno</option><option value="EXTERNAL">Externo</option></select></label>
      <label>Nombres<input required value={form.first_name} onChange={e=>setForm({...form,first_name:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label>Apellidos<input required value={form.last_name} onChange={e=>setForm({...form,last_name:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label>Celular<input value={form.phone||''} onChange={e=>setForm({...form,phone:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label>Correo<input type="email" value={form.email||''} onChange={e=>setForm({...form,email:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label>Comisión por defecto (%)<input required type="number" min="0" max="100" step="0.01" value={form.default_commission_rate} onChange={e=>setForm({...form,default_commission_rate:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      {editing&&<label>Estado<select value={form.active?'1':'0'} onChange={e=>setForm({...form,active:e.target.value==='1'})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="1">Activo</option><option value="0">Inactivo</option></select></label>}
    </div><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(false)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Guardar</button></div></form></div>}
  </div>
}
