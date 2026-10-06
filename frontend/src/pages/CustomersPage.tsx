import { FormEvent, useEffect, useState } from 'react'
import { Pencil, Plus, Search, Users } from 'lucide-react'
import { apiFetch } from '../api'

type Customer={id:string;identification:string;first_name:string;last_name:string;full_name:string;phone?:string;mobile?:string;email?:string;address?:string;canton?:string;province?:string;notes?:string;active:boolean}
const empty:any={identification_type:'CEDULA',identification:'',first_name:'',last_name:'',phone:'',mobile:'',email:'',address:'',canton:'Samborondón',province:'Guayas',notes:''}

export default function CustomersPage(){
  const [rows,setRows]=useState<Customer[]>([])
  const [q,setQ]=useState('')
  const [form,setForm]=useState<any>(empty)
  const [editing,setEditing]=useState<string|null>(null)
  const [open,setOpen]=useState(false)
  const [error,setError]=useState('')
  async function load(){setRows(await apiFetch('/customers'+(q?'?q='+encodeURIComponent(q):'')))}
  useEffect(()=>{load()},[])
  async function save(e:FormEvent){
    e.preventDefault(); setError('')
    try{
      await apiFetch(editing?'/customers/'+editing:'/customers',{method:editing?'PUT':'POST',body:JSON.stringify({...form,active:true})})
      setOpen(false); setEditing(null); setForm(empty); await load()
    }catch(err:any){setError(err.message)}
  }
  function edit(c:Customer){setEditing(c.id);setForm({...empty,...c});setOpen(true)}
  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div><p className="text-sm font-semibold text-[#52AD56]">Gestión comercial</p><h2 className="mt-1 text-2xl font-semibold">Clientes</h2><p className="mt-1 text-sm text-slate-500">Registro de compradores y postulantes.</p></div>
      <button onClick={()=>{setEditing(null);setForm(empty);setOpen(true)}} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white"><Plus className="h-4 w-4"/>Nuevo cliente</button>
    </div>
    <div className="mt-6 rounded-2xl border bg-white shadow-sm">
      <div className="flex gap-2 border-b p-4"><div className="flex flex-1 items-center rounded-xl border px-3"><Search className="h-4 w-4 text-slate-400"/><input value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==='Enter'&&load()} className="w-full px-3 py-2 outline-none" placeholder="Buscar por cédula o nombre"/></div><button onClick={load} className="rounded-xl border px-4 text-sm">Buscar</button></div>
      <div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3">Identificación</th><th className="px-5 py-3">Cliente</th><th className="px-5 py-3">Contacto</th><th className="px-5 py-3">Ubicación</th><th></th></tr></thead><tbody>{rows.map(c=><tr key={c.id} className="border-t"><td className="px-5 py-4">{c.identification}</td><td className="px-5 py-4 font-medium">{c.full_name}</td><td className="px-5 py-4 text-slate-600">{c.mobile||c.phone||'-'}<br/><span className="text-xs">{c.email||''}</span></td><td className="px-5 py-4 text-slate-600">{[c.canton,c.province].filter(Boolean).join(', ')||'-'}</td><td className="px-5 py-4"><button onClick={()=>edit(c)} className="rounded-lg border p-2"><Pencil className="h-4 w-4"/></button></td></tr>)}</tbody></table>
      {!rows.length&&<div className="flex flex-col items-center py-14 text-slate-400"><Users className="h-10 w-10"/><p className="mt-3">No hay clientes registrados.</p></div>}</div>
    </div>
    {open&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={save} className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl"><div className="flex items-center justify-between"><h3 className="text-xl font-semibold">{editing?'Editar cliente':'Nuevo cliente'}</h3><button type="button" onClick={()=>setOpen(false)}>✕</button></div>{error&&<p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
    <div className="mt-6 grid gap-4 md:grid-cols-2">{[['identification','Identificación'],['first_name','Nombres'],['last_name','Apellidos'],['mobile','Celular'],['phone','Teléfono'],['email','Correo'],['canton','Cantón'],['province','Provincia']].map(([k,l])=><label key={k}><span className="text-sm font-medium text-slate-700">{l}{['identification','first_name','last_name','mobile'].includes(k)&&<span className="ml-1 text-red-600">*</span>}</span><input required={['identification','first_name','last_name','mobile'].includes(k)} type={k==='email'?'email':'text'} value={form[k]||''} onChange={e=>setForm({...form,[k]:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>)}<label className="md:col-span-2"><span className="text-sm font-medium">Dirección<span className="ml-1 text-red-600">*</span></span><input required value={form.address||''} onChange={e=>setForm({...form,address:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label><label className="md:col-span-2"><span className="text-sm font-medium">Observaciones</span><textarea value={form.notes||''} onChange={e=>setForm({...form,notes:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label></div>
    <div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(false)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Guardar</button></div></form></div>}
  </div>
}
