import { FormEvent, useEffect, useState } from 'react'
import { BadgeCheck, CalendarClock, Plus, ShoppingCart } from 'lucide-react'
import { apiFetch } from '../api'

const today=()=>new Date().toISOString().slice(0,10)

export default function SalesPage(){
  const [tab,setTab]=useState<'reservations'|'sales'>('reservations')
  const [customers,setCustomers]=useState<any[]>([])
  const [properties,setProperties]=useState<any[]>([])
  const [reservations,setReservations]=useState<any[]>([])
  const [sales,setSales]=useState<any[]>([])
  const [open,setOpen]=useState<'reservation'|'sale'|null>(null)
  const [resForm,setResForm]=useState<any>({customer_id:'',property_id:'',reservation_date:today(),expires_on:'',notes:''})
  const [saleForm,setSaleForm]=useState<any>({customer_id:'',property_id:'',reservation_id:'',sale_price:'',down_payment:'0',installment_count:'12',frequency:'MONTHLY',first_due_date:today(),notes:''})

  async function load(){
    const [c,p,r,s]=await Promise.all([
      apiFetch('/customers'),
      apiFetch('/properties'),
      apiFetch('/reservations'),
      apiFetch('/sales')
    ])
    setCustomers(c);setProperties(p);setReservations(r);setSales(s)
  }
  useEffect(()=>{load()},[])

  const available=properties.filter((p:any)=>['AVAILABLE','RESERVED'].includes(p.status.code))

  async function saveReservation(e:FormEvent){
    e.preventDefault()
    await apiFetch('/reservations',{method:'POST',body:JSON.stringify({...resForm,expires_on:resForm.expires_on||null})})
    setOpen(null);await load()
  }

  function fromReservation(r:any){
    const prop=properties.find((p:any)=>p.id===r.property_id)
    setSaleForm({...saleForm,customer_id:r.customer_id,property_id:r.property_id,reservation_id:r.id,sale_price:String(prop?.total_price||''),first_due_date:today()})
    setOpen('sale')
  }

  async function saveSale(e:FormEvent){
    e.preventDefault()
    await apiFetch('/sales',{method:'POST',body:JSON.stringify({
      ...saleForm,
      sale_price:Number(saleForm.sale_price),
      down_payment:Number(saleForm.down_payment||0),
      installment_count:Number(saleForm.installment_count)
    })})
    setOpen(null);await load()
  }

  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div><p className="text-sm font-semibold text-[#52AD56]">Comercialización</p><h2 className="mt-1 text-2xl font-semibold">Reservas y ventas</h2><p className="mt-1 text-sm text-slate-500">Del lote disponible a la compra confirmada.</p></div>
      <button onClick={()=>setOpen('reservation')} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white"><Plus className="h-4 w-4"/>Nueva reserva</button>
    </div>

    <div className="mt-6 flex gap-2">
      <button onClick={()=>setTab('reservations')} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(tab==='reservations'?'bg-[#3A6C32] text-white':'border bg-white')}>Reservas</button>
      <button onClick={()=>setTab('sales')} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(tab==='sales'?'bg-[#3A6C32] text-white':'border bg-white')}>Compras confirmadas</button>
    </div>

    {tab==='reservations'?<div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3">Cliente</th><th className="px-5 py-3">Predio</th><th className="px-5 py-3">Reserva</th><th className="px-5 py-3">Vence</th><th></th></tr></thead><tbody>{reservations.map(r=><tr key={r.id} className="border-t"><td className="px-5 py-4 font-medium">{r.customer}</td><td className="px-5 py-4">{r.property}</td><td className="px-5 py-4">{r.reservation_date}</td><td className="px-5 py-4">{r.expires_on||'-'}</td><td className="px-5 py-4 text-right"><button onClick={()=>fromReservation(r)} className="rounded-lg bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-700">Confirmar compra</button></td></tr>)}</tbody></table>{!reservations.length&&<div className="py-14 text-center text-slate-400"><CalendarClock className="mx-auto h-10 w-10"/><p className="mt-3">No hay reservas activas.</p></div>}</div>
    :<div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3">Cliente</th><th className="px-5 py-3">Predio</th><th className="px-5 py-3">Precio</th><th className="px-5 py-3">Pagado</th><th className="px-5 py-3">Saldo</th></tr></thead><tbody>{sales.map(s=><tr key={s.id} className="border-t"><td className="px-5 py-4 font-medium">{s.customer}</td><td className="px-5 py-4">{s.property}</td><td className="px-5 py-4">$ {s.sale_price.toFixed(2)}</td><td className="px-5 py-4 text-emerald-700">$ {s.paid.toFixed(2)}</td><td className="px-5 py-4 font-semibold">$ {s.balance.toFixed(2)}</td></tr>)}</tbody></table>{!sales.length&&<div className="py-14 text-center text-slate-400"><ShoppingCart className="mx-auto h-10 w-10"/><p className="mt-3">No hay compras confirmadas.</p></div>}</div>}

    {open==='reservation'&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={saveReservation} className="w-full max-w-xl rounded-2xl bg-white p-6"><h3 className="text-xl font-semibold">Nueva reserva</h3><div className="mt-5 grid gap-4">
      <label>Cliente<select required value={resForm.customer_id} onChange={e=>setResForm({...resForm,customer_id:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{customers.map(c=><option key={c.id} value={c.id}>{c.identification} · {c.full_name}</option>)}</select></label>
      <label>Predio disponible<select required value={resForm.property_id} onChange={e=>setResForm({...resForm,property_id:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{properties.filter((p:any)=>p.status.code==='AVAILABLE').map((p:any)=><option key={p.id} value={p.id}>{p.code} · {p.block} / Lote {p.lot_number} · $ {p.total_price.toFixed(2)}</option>)}</select></label>
      <div className="grid gap-4 sm:grid-cols-2"><label>Fecha<input type="date" value={resForm.reservation_date} onChange={e=>setResForm({...resForm,reservation_date:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label><label>Válida hasta<input type="date" value={resForm.expires_on} onChange={e=>setResForm({...resForm,expires_on:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label></div>
    </div><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(null)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Reservar</button></div></form></div>}

    {open==='sale'&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={saveSale} className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6"><div className="flex items-center gap-2"><BadgeCheck className="text-[#3A6C32]"/><h3 className="text-xl font-semibold">Confirmar compra</h3></div><div className="mt-5 grid gap-4 sm:grid-cols-2">
      <label className="sm:col-span-2">Cliente<select required value={saleForm.customer_id} onChange={e=>setSaleForm({...saleForm,customer_id:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{customers.map(c=><option key={c.id} value={c.id}>{c.full_name}</option>)}</select></label>
      <label className="sm:col-span-2">Predio<select required value={saleForm.property_id} onChange={e=>{const p=available.find((x:any)=>x.id===e.target.value);setSaleForm({...saleForm,property_id:e.target.value,sale_price:String(p?.total_price||'')})}} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{available.map((p:any)=><option key={p.id} value={p.id}>{p.code} · {p.block} / {p.lot_number}</option>)}</select></label>
      <label>Precio de venta<input required type="number" step="0.01" value={saleForm.sale_price} onChange={e=>setSaleForm({...saleForm,sale_price:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label>Entrada<input type="number" step="0.01" value={saleForm.down_payment} onChange={e=>setSaleForm({...saleForm,down_payment:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label>Número de cuotas<input required type="number" min="1" value={saleForm.installment_count} onChange={e=>setSaleForm({...saleForm,installment_count:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label>Primera cuota<input required type="date" value={saleForm.first_due_date} onChange={e=>setSaleForm({...saleForm,first_due_date:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
    </div><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(null)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Confirmar compra</button></div></form></div>}
  </div>
}
