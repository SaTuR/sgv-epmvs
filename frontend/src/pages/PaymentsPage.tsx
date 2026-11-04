import { FormEvent, useEffect, useState } from 'react'
import { CircleDollarSign, FileDown, Pencil, Plus, Trash2 } from 'lucide-react'
import { apiDownload, apiFetch } from '../api'

const today=()=>new Date().toISOString().slice(0,10)

export default function PaymentsPage({permissions}:{permissions:string[]}){
  const [sales,setSales]=useState<any[]>([])
  const [payments,setPayments]=useState<any[]>([])
  const [open,setOpen]=useState(false)
  const [editing,setEditing]=useState<any>(null)
  const [form,setForm]=useState<any>({sale_id:'',payment_date:today(),amount:'',payment_method:'TRANSFERENCIA',reference:'',bank_receipt:'',notes:''})
  const canDelete=permissions.includes('system.admin')||permissions.includes('payments.delete')
  const canEdit=permissions.includes('system.admin')||permissions.includes('payments.edit')
  async function load(){const [s,p]=await Promise.all([apiFetch('/sales'),apiFetch('/payments')]);setSales(s);setPayments(p)}
  useEffect(()=>{load()},[])
  async function save(e:FormEvent){
    e.preventDefault()
    await apiFetch('/payments',{method:'POST',body:JSON.stringify({...form,amount:Number(form.amount)})})
    setOpen(false);setForm({...form,sale_id:'',amount:'',reference:'',bank_receipt:'',notes:''});await load()
  }
  async function receipt(p:any){
    await apiDownload('/payments/'+p.id+'/receipt.pdf','comprobante-pago.pdf')
  }

  function editPayment(p:any){
    setEditing({...p,notes:p.notes||''})
  }

  async function saveEdit(e:FormEvent){
    e.preventDefault()
    if(!editing)return
    try{
      await apiFetch('/payments/'+editing.id,{
        method:'PUT',
        body:JSON.stringify({
          payment_date:editing.payment_date,
          payment_method:editing.payment_method,
          reference:editing.reference,
          bank_receipt:editing.bank_receipt,
          notes:editing.notes||null
        })
      })
      setEditing(null)
      await load()
    }catch(err:any){
      alert(err?.message||'No fue posible actualizar el pago')
    }
  }

  async function deletePayment(p:any){
    if(!confirm('¿Eliminar el pago de $ '+Number(p.amount).toFixed(2)+' de '+p.customer+' para el predio '+p.property+'?\n\nSe revertirá el valor aplicado a las cuotas y la acción quedará registrada en auditoría.')) return
    try{
      await apiFetch('/payments/'+p.id,{method:'DELETE'})
      await load()
    }catch(err:any){
      alert(err?.message||'No fue posible eliminar el pago')
    }
  }
  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div><p className="text-sm font-semibold text-[#52AD56]">Recaudación</p><h2 className="mt-1 text-2xl font-semibold">Pagos</h2><p className="mt-1 text-sm text-slate-500">Pagos aplicados automáticamente a las cuotas más antiguas pendientes.</p></div>
      <button onClick={()=>setOpen(true)} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white"><Plus className="h-4 w-4"/>Registrar pago</button>
    </div>

    <div className="mt-6 overflow-hidden rounded-2xl border bg-white shadow-sm">
      <div className="overflow-x-auto"><table className="min-w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3">Fecha</th><th className="px-5 py-3">Cliente</th><th className="px-5 py-3">Predio</th><th className="px-5 py-3">Forma</th><th className="px-5 py-3">Referencia interna</th><th className="px-5 py-3">Comprobante bancario</th><th className="px-5 py-3 text-right">Valor</th><th></th></tr></thead>
        <tbody>{payments.map(p=><tr key={p.id} className="border-t"><td className="px-5 py-4">{p.payment_date}</td><td className="px-5 py-4 font-medium">{p.customer}</td><td className="px-5 py-4">{p.property}</td><td className="px-5 py-4">{p.payment_method}</td><td className="px-5 py-4">{p.reference||'-'}</td><td className="px-5 py-4">{p.bank_receipt||'-'}</td><td className="px-5 py-4 text-right font-semibold text-emerald-700">$ {p.amount.toFixed(2)}</td><td className="px-5 py-4 text-right"><div className="flex justify-end gap-2"><button onClick={()=>receipt(p)} className="inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-xs font-semibold text-[#3A6C32]"><FileDown className="h-4 w-4"/>PDF</button>{canEdit&&<button onClick={()=>editPayment(p)} className="inline-flex items-center gap-1 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-800"><Pencil className="h-4 w-4"/>Editar</button>}{canDelete&&<button onClick={()=>deletePayment(p)} className="inline-flex items-center gap-1 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700"><Trash2 className="h-4 w-4"/>Eliminar</button>}</div></td></tr>)}</tbody>
      </table>{!payments.length&&<div className="py-14 text-center text-slate-400"><CircleDollarSign className="mx-auto h-10 w-10"/><p className="mt-3">No hay pagos registrados.</p></div>}</div>
    </div>

    {editing&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={saveEdit} className="w-full max-w-xl rounded-2xl bg-white p-6"><h3 className="text-xl font-semibold">Editar datos del pago</h3><p className="mt-1 text-sm text-slate-500">{editing.customer} · {editing.property}</p><div className="mt-5 grid gap-4">
      <div className="grid gap-4 sm:grid-cols-2"><label>Fecha<input required type="date" value={editing.payment_date} onChange={e=>setEditing({...editing,payment_date:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label><label>Valor<input disabled value={'$ '+Number(editing.amount).toFixed(2)} className="mt-1 w-full rounded-xl border bg-slate-100 px-3 py-2.5 text-slate-500"/></label></div>
      <label>Forma de pago<select required value={editing.payment_method} onChange={e=>setEditing({...editing,payment_method:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option>EFECTIVO</option><option>TRANSFERENCIA</option><option>DEPOSITO</option><option>CHEQUE</option><option>OTRA</option></select></label>
      <label>Referencia interna<input required value={editing.reference||''} onChange={e=>setEditing({...editing,reference:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5" placeholder="Comprobante interno entregado por Ventas"/></label>
      <label>Comprobante bancario<input required value={editing.bank_receipt||''} onChange={e=>setEditing({...editing,bank_receipt:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5" placeholder="Número de comprobante bancario"/></label>
      <label>Observaciones<textarea value={editing.notes||''} onChange={e=>setEditing({...editing,notes:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
    </div><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setEditing(null)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Guardar cambios</button></div></form></div>}

    {open&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={save} className="w-full max-w-xl rounded-2xl bg-white p-6"><h3 className="text-xl font-semibold">Registrar pago</h3><div className="mt-5 grid gap-4">
      <label>Compra<select required value={form.sale_id} onChange={e=>setForm({...form,sale_id:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{sales.filter(s=>s.balance>0).map(s=><option key={s.id} value={s.id}>{s.customer} · {s.property} · Saldo $ {s.balance.toFixed(2)}</option>)}</select></label>
      <div className="grid gap-4 sm:grid-cols-2"><label>Fecha<input type="date" value={form.payment_date} onChange={e=>setForm({...form,payment_date:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label><label>Valor<input required type="number" step="0.01" min="0.01" value={form.amount} onChange={e=>setForm({...form,amount:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label></div>
      <label>Forma de pago<select value={form.payment_method} onChange={e=>setForm({...form,payment_method:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option>EFECTIVO</option><option>TRANSFERENCIA</option><option>DEPOSITO</option><option>CHEQUE</option><option>OTRA</option></select></label>
      <label>Referencia interna<input required value={form.reference} onChange={e=>setForm({...form,reference:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5" placeholder="Comprobante interno entregado por Ventas"/></label>
      <label>Comprobante bancario<input required value={form.bank_receipt} onChange={e=>setForm({...form,bank_receipt:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5" placeholder="Número de comprobante de depósito/transferencia"/></label>
      <label>Observaciones<textarea value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
    </div><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(false)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Registrar</button></div></form></div>}
  </div>
}
