import { useEffect, useState } from 'react'
import { BadgeDollarSign, CheckCircle2, Search } from 'lucide-react'
import { apiFetch } from '../api'

export default function CommissionsPage({permissions}:{permissions:string[]}){
  const [rows,setRows]=useState<any[]>([])
  const [q,setQ]=useState('')
  const [status,setStatus]=useState('ALL')
  const canManage=permissions.includes('system.admin')||permissions.includes('commissions.manage')
  const canApprove=permissions.includes('system.admin')||permissions.includes('commissions.approve')
  const canPay=permissions.includes('system.admin')||permissions.includes('commissions.pay')
  async function load(){setRows(await apiFetch('/commissions'))}
  useEffect(()=>{load()},[])

  async function changeStatus(r:any,next:string){
    let payment_reference:string|undefined
    if(next==='PAID'){
      payment_reference=prompt('Referencia del pago de la comisión')||''
      if(!payment_reference.trim())return
    }
    if(!confirm('¿Cambiar la comisión de '+r.seller+' a '+next+'?'))return
    await apiFetch('/commissions/'+r.id+'/status',{method:'PUT',body:JSON.stringify({status:next,payment_reference:payment_reference||null,notes:r.notes||null})})
    await load()
  }

  const term=q.trim().toLocaleLowerCase('es')
  const filtered=rows.filter((r:any)=>(status==='ALL'||r.status===status)&&(!term||[r.seller,r.customer,r.property].some(v=>String(v??'').toLocaleLowerCase('es').includes(term))))
  const total=filtered.reduce((a:number,r:any)=>a+Number(r.commission_amount||0),0)

  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between"><div><p className="text-sm font-semibold text-[#52AD56]">Gestión comercial</p><h2 className="mt-1 text-2xl font-semibold">Comisiones</h2><p className="mt-1 text-sm text-slate-500">Comisiones generadas automáticamente desde las ventas confirmadas.</p></div><div className="rounded-2xl border bg-white px-5 py-3 shadow-sm"><p className="text-xs text-slate-500">Total según filtro</p><p className="text-xl font-semibold text-emerald-700">$ {total.toFixed(2)}</p></div></div>

    <div className="mt-6 grid gap-3 rounded-2xl border bg-white p-4 shadow-sm md:grid-cols-[1fr_220px]"><label className="text-sm font-medium text-slate-700">Buscar<div className="relative mt-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"/><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Vendedor, cliente o predio" className="w-full rounded-xl border py-2.5 pl-9 pr-3"/></div></label><label className="text-sm font-medium text-slate-700">Estado<select value={status} onChange={e=>setStatus(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="ALL">Todos</option><option value="PENDING">Pendiente</option><option value="APPROVED">Aprobada</option><option value="PAID">Pagada</option><option value="CANCELLED">Anulada</option></select></label></div>

    <div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm"><div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Vendedor</th><th className="px-4 py-3">Cliente</th><th className="px-4 py-3">Predio</th><th className="px-4 py-3 text-right">Venta</th><th className="px-4 py-3 text-right">%</th><th className="px-4 py-3 text-right">Comisión</th><th className="px-4 py-3">Estado</th><th></th></tr></thead><tbody>
      {filtered.map((r:any)=><tr key={r.id} className="border-t"><td className="px-4 py-3 font-medium">{r.seller}</td><td className="px-4 py-3">{r.customer}</td><td className="px-4 py-3">{r.property}</td><td className="px-4 py-3 text-right">$ {Number(r.sale_price).toFixed(2)}</td><td className="px-4 py-3 text-right">{Number(r.commission_rate).toFixed(2)}%</td><td className="px-4 py-3 text-right font-semibold text-emerald-700">$ {Number(r.commission_amount).toFixed(2)}</td><td className="px-4 py-3"><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold">{r.status}</span></td><td className="px-4 py-3 text-right"><div className="flex justify-end gap-2">{canManage&&canApprove&&r.status==='PENDING'&&<button onClick={()=>changeStatus(r,'APPROVED')} className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">Aprobar</button>}{canManage&&canPay&&r.status==='APPROVED'&&<button onClick={()=>changeStatus(r,'PAID')} className="rounded-lg bg-[#3A6C32] px-3 py-2 text-xs font-semibold text-white">Registrar pago</button>}{canManage&&r.status!=='PAID'&&r.status!=='CANCELLED'&&<button onClick={()=>changeStatus(r,'CANCELLED')} className="rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-700">Anular</button>}</div></td></tr>)}
    </tbody></table>{!filtered.length&&<div className="py-14 text-center text-slate-400"><BadgeDollarSign className="mx-auto h-10 w-10"/><p className="mt-3">No hay comisiones para los filtros seleccionados.</p></div>}</div></div>
  </div>
}
