import { FormEvent, useEffect, useState } from 'react'
import { CircleDollarSign, Plus } from 'lucide-react'
import { apiFetch } from '../api'

const today=()=>new Date().toISOString().slice(0,10)

export default function PaymentsPage(){
  const [sales,setSales]=useState<any[]>([])
  const [payments,setPayments]=useState<any[]>([])
  const [open,setOpen]=useState(false)
  const [form,setForm]=useState<any>({sale_id:'',payment_date:today(),amount:'',payment_method:'TRANSFERENCIA',reference:'',notes:''})
  async function load(){const [s,p]=await Promise.all([apiFetch('/sales'),apiFetch('/payments')]);setSales(s);setPayments(p)}
  useEffect(()=>{load()},[])
  async function save(e:FormEvent){e.preventDefault();await apiFetch('/payments',{method:'POST',body:JSON.stringify({...form,amount:Number(form.amount)})});setOpen(false);setForm({...form,sale_id:'',amount:'',reference:'',notes:''});await load()}
  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between"><div><p className="text-sm font-semibold text-[#52AD56]">Recaudación</p><h2 className="mt-1 text-2xl font-semibold">Pagos</h2><p className="mt-1 text-sm text-slate-500">Los pagos se aplican automáticamente a las cuotas más antiguas pendientes.</p></div><button onClick={()=>setOpen(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white"><Plus className="h-4 w-4"/>Registrar pago</button></div>
    <div className="mt-6 overflow-hidden rounded-2xl border bg-white shadow-sm"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3">Fecha</th><th className="px-5 py-3">Cliente</th><th className="px-5 py-3">Predio</th><th className="px-5 py-3">Forma</th><th className="px-5 py-3">Referencia</th><th className="px-5 py-3 text-right">Valor</th></tr></thead><tbody>{payments.map(p=><tr key={p.id} className="border-t"><td className="px-5 py-4">{p.payment_date}</td><td className="px-5 py-4 font-medium">{p.customer}</td><td className="px-5 py-4">{p.property}</td><td className="px-5 py-4">{p.payment_method}</td><td className="px-5 py-4">{p.reference||'-'}</td><td className="px-5 py-4 text-right font-semibold text-emerald-700">$ {p.amount.toFixed(2)}</td></tr>)}</tbody></table>{!payments.length&&<div className="py-14 text-center text-slate-400"><CircleDollarSign className="mx-auto h-10 w-10"/><p className="mt-3">No hay pagos registrados.</p></div>}</div>
    {open&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={save} className="w-full max-w-xl rounded-2xl bg-white p-6"><h3 className="text-xl font-semibold">Registrar pago</h3><div className="mt-5 grid gap-4">
      <label>Compra<select required value={form.sale_id} onChange={e=>setForm({...form,sale_id:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{sales.filter(s=>s.balance>0).map(s=><option key={s.id} value={s.id}>{s.customer} · {s.property} · Saldo $ {s.balance.toFixed(2)}</option>)}</select></label>
      <div className="grid gap-4 sm:grid-cols-2"><label>Fecha<input type="date" value={form.payment_date} onChange={e=>setForm({...form,payment_date:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label><label>Valor<input required type="number" step="0.01" min="0.01" value={form.amount} onChange={e=>setForm({...form,amount:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label></div>
      <label>Forma de pago<select value={form.payment_method} onChange={e=>setForm({...form,payment_method:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option>EFECTIVO</option><option>TRANSFERENCIA</option><option>DEPOSITO</option><option>CHEQUE</option><option>OTRA</option></select></label>
      <label>Referencia<input value={form.reference} onChange={e=>setForm({...form,reference:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
    </div><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(false)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Registrar</button></div></form></div>}
  </div>
}
