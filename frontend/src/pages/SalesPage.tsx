import { FormEvent, useEffect, useState } from 'react'
import { BadgeCheck, CalendarClock, Eye, FileCheck2, FileText, Plus, ReceiptText, Search, ShoppingCart, Trash2 } from 'lucide-react'
import { apiDownload, apiFetch } from '../api'
import { installmentStatusBadgeClass } from '../utils/statusStyles'

const today=()=>new Date().toISOString().slice(0,10)
const addDays=(iso:string,days:number)=>{const d=new Date(iso+'T12:00:00');d.setDate(d.getDate()+days);return d.toISOString().slice(0,10)}

export default function SalesPage({permissions}:{permissions:string[]}){
  const [tab,setTab]=useState<'reservations'|'sales'>('reservations')
  const [customers,setCustomers]=useState<any[]>([])
  const [properties,setProperties]=useState<any[]>([])
  const [reservations,setReservations]=useState<any[]>([])
  const [sales,setSales]=useState<any[]>([])
  const [open,setOpen]=useState<'reservation'|'sale'|'installments'|null>(null)
  const [installments,setInstallments]=useState<any[]>([])
  const [selectedSale,setSelectedSale]=useState<any>(null)
  const [editingInstallments,setEditingInstallments]=useState(false)
  const [runtimeSettings,setRuntimeSettings]=useState<any>({reservation_default_days:3,currency_symbol:'$'})
  const [resForm,setResForm]=useState<any>({customer_id:'',property_id:'',reservation_date:today(),expires_on:'',notes:''})
  const [saleForm,setSaleForm]=useState<any>({customer_id:'',property_id:'',reservation_id:'',sale_price:'',down_payment:'0',installment_count:'12',frequency:'MONTHLY',first_due_date:today(),notes:''})
  const [customerSearch,setCustomerSearch]=useState('')
  const [propertySearch,setPropertySearch]=useState('')
  const [reservationFilter,setReservationFilter]=useState('')
  const [reservationFrom,setReservationFrom]=useState('')
  const [reservationTo,setReservationTo]=useState('')
  const [saleFilter,setSaleFilter]=useState('')
  const [saleStatusFilter,setSaleStatusFilter]=useState('ALL')

  async function load(){
    const [c,p,r,s]=await Promise.all([apiFetch('/customers'),apiFetch('/properties'),apiFetch('/reservations'),apiFetch('/sales')])
    setCustomers(c);setProperties(p);setReservations(r);setSales(s)
  }
  useEffect(()=>{load();apiFetch('/settings/runtime').then(setRuntimeSettings).catch(()=>{})},[])

  const available=properties.filter((p:any)=>['AVAILABLE','RESERVED'].includes(p.status.code))
  const customerTerm=customerSearch.trim().toLocaleLowerCase('es')
  const propertyTerm=propertySearch.trim().toLocaleLowerCase('es')
  const filteredCustomers=customerTerm
    ? customers.filter((c:any)=>[c.identification,c.full_name,c.email,c.mobile].some(v=>String(v??'').toLocaleLowerCase('es').includes(customerTerm)))
    : customers
  const filteredAvailableForReservation=properties
    .filter((p:any)=>p.status.code==='AVAILABLE')
    .filter((p:any)=>!propertyTerm || [p.code,p.block,p.lot_number,p.cadastral_key,p.location_reference].some(v=>String(v??'').toLocaleLowerCase('es').includes(propertyTerm)))
  const filteredAvailableForSale=available
    .filter((p:any)=>!propertyTerm || [p.code,p.block,p.lot_number,p.cadastral_key,p.location_reference].some(v=>String(v??'').toLocaleLowerCase('es').includes(propertyTerm)))

  const reservationTerm=reservationFilter.trim().toLocaleLowerCase('es')
  const filteredReservations=reservations.filter((r:any)=>{
    const matchesText=!reservationTerm || [r.customer,r.property].some(v=>String(v??'').toLocaleLowerCase('es').includes(reservationTerm))
    const matchesFrom=!reservationFrom || String(r.reservation_date||'')>=reservationFrom
    const matchesTo=!reservationTo || String(r.reservation_date||'')<=reservationTo
    return matchesText&&matchesFrom&&matchesTo
  })

  const saleTerm=saleFilter.trim().toLocaleLowerCase('es')
  const filteredSales=sales.filter((s:any)=>{
    const matchesText=!saleTerm || [s.customer,s.property].some(v=>String(v??'').toLocaleLowerCase('es').includes(saleTerm))
    const matchesStatus=saleStatusFilter==='ALL' || s.property_status===saleStatusFilter
    return matchesText&&matchesStatus
  })

  async function saveReservation(e:FormEvent){
    e.preventDefault()
    await apiFetch('/reservations',{method:'POST',body:JSON.stringify({...resForm,expires_on:resForm.expires_on||null})})
    setOpen(null);await load()
  }

  function fromReservation(r:any){
    setCustomerSearch('')
    setPropertySearch('')
    const prop=properties.find((p:any)=>p.id===r.property_id)
    setSaleForm({...saleForm,customer_id:r.customer_id,property_id:r.property_id,reservation_id:r.id,sale_price:String(prop?.total_price||''),first_due_date:today()})
    setOpen('sale')
  }

  async function saveSale(e:FormEvent){
    e.preventDefault()
    await apiFetch('/sales',{method:'POST',body:JSON.stringify({...saleForm,sale_price:Number(saleForm.sale_price),down_payment:Number(saleForm.down_payment||0),installment_count:Number(saleForm.installment_count)})})
    setOpen(null);await load()
  }

  async function showInstallments(s:any){
    setSelectedSale(s)
    setEditingInstallments(false)
    setInstallments(await apiFetch('/sales/'+s.id+'/installments'))
    setOpen('installments')
  }

  function updateInstallment(id:string,field:'due_date'|'amount',value:string){
    setInstallments((rows:any[])=>rows.map((i:any)=>i.id===id?{...i,[field]:field==='amount'?Number(value):value}:i))
  }

  async function saveInstallments(){
    if(!selectedSale) return
    const total=installments.reduce((sum:number,i:any)=>sum+Number(i.amount||0),0)
    const expected=Number(selectedSale.sale_price)-Number(selectedSale.down_payment||0)
    if(Math.abs(total-expected)>0.005){
      alert('La suma de las cuotas debe ser exactamente $ '+expected.toFixed(2)+'. Entrada + cuotas debe ser igual al precio de venta.')
      return
    }
    try{
      await apiFetch('/sales/'+selectedSale.id+'/installments',{
        method:'PUT',
        body:JSON.stringify({installments:installments.map((i:any)=>({id:i.id,due_date:i.due_date,amount:Number(i.amount)}))})
      })
      setInstallments(await apiFetch('/sales/'+selectedSale.id+'/installments'))
      setEditingInstallments(false)
      await load()
    }catch(err:any){
      alert(err?.message||'No fue posible actualizar las cuotas')
    }
  }

  const canRelease=permissions.includes('system.admin')||permissions.includes('reservations.release')
  const canCreateInvoice=permissions.includes('system.admin')||permissions.includes('invoices.create')
  const canDeleteSale=permissions.includes('system.admin')

  async function generateInvoice(s:any){
    if(!confirm('¿Generar la factura electrónica para el predio '+s.property+'? Esta acción quedará registrada en auditoría.')) return
    await apiFetch('/electronic-invoices/sales/'+s.id+'/create',{method:'POST'})
    await load()
  }

  async function releaseReservation(r:any){
    if(!confirm('¿Liberar el solar '+r.property+' reservado por '+r.customer+'? El solar volverá a estado Disponible.')) return
    await apiFetch('/reservations/'+r.id+'/cancel',{method:'POST'})
    await load()
  }

  async function deleteSale(s:any){
    if(!confirm('¿Eliminar la compra de '+s.customer+' sobre el predio '+s.property+'? El predio volverá a Disponible.')) return
    try{
      await apiFetch('/sales/'+s.id,{method:'DELETE'})
      await load()
    }catch(err:any){
      alert(err?.message||'No fue posible eliminar la compra')
    }
  }

  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div><p className="text-sm font-semibold text-[#52AD56]">Comercialización</p><h2 className="mt-1 text-2xl font-semibold">Reservas y ventas</h2><p className="mt-1 text-sm text-slate-500">Del lote disponible a la compra confirmada.</p></div>
      <button onClick={()=>{const d=today();setCustomerSearch('');setPropertySearch('');setResForm({...resForm,reservation_date:d,expires_on:addDays(d,Number(runtimeSettings.reservation_default_days||3))});setOpen('reservation')}} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white"><Plus className="h-4 w-4"/>Nueva reserva</button>
    </div>

    <div className="mt-6 flex gap-2">
      <button onClick={()=>setTab('reservations')} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(tab==='reservations'?'bg-[#3A6C32] text-white':'border bg-white')}>Reservas</button>
      <button onClick={()=>setTab('sales')} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(tab==='sales'?'bg-[#3A6C32] text-white':'border bg-white')}>Compras confirmadas</button>
    </div>

    {tab==='reservations'?<>
    <div className="mt-4 grid gap-3 rounded-2xl border bg-white p-4 shadow-sm md:grid-cols-[1fr_auto_auto_auto] md:items-end">
      <label className="text-sm font-medium text-slate-700">Buscar
        <div className="relative mt-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"/><input value={reservationFilter} onChange={e=>setReservationFilter(e.target.value)} placeholder="Cliente o predio" className="w-full rounded-xl border py-2.5 pl-9 pr-3 outline-none focus:border-[#52AD56] focus:ring-2 focus:ring-[#52AD56]/20"/></div>
      </label>
      <label className="text-sm font-medium text-slate-700">Desde<input type="date" value={reservationFrom} onChange={e=>setReservationFrom(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label className="text-sm font-medium text-slate-700">Hasta<input type="date" value={reservationTo} onChange={e=>setReservationTo(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <button type="button" onClick={()=>{setReservationFilter('');setReservationFrom('');setReservationTo('')}} className="rounded-xl border px-4 py-2.5 text-sm font-semibold text-slate-600">Limpiar</button>
      <p className="text-xs text-slate-400 md:col-span-4">{filteredReservations.length} de {reservations.length} reserva(s)</p>
    </div>
    <div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3">Cliente</th><th className="px-5 py-3">Predio</th><th className="px-5 py-3">Reserva</th><th className="px-5 py-3">Vence</th><th></th></tr></thead><tbody>{filteredReservations.map(r=><tr key={r.id} className="border-t"><td className="px-5 py-4 font-medium">{r.customer}</td><td className="px-5 py-4">{r.property}</td><td className="px-5 py-4">{r.reservation_date}</td><td className="px-5 py-4">{r.expires_on||'-'}</td><td className="px-5 py-4 text-right"><div className="flex justify-end gap-2"><button onClick={()=>fromReservation(r)} className="rounded-lg bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-700">Confirmar compra</button>{canRelease&&<button onClick={()=>releaseReservation(r)} className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700">Liberar solar</button>}</div></td></tr>)}</tbody></table>{!filteredReservations.length&&<div className="py-14 text-center text-slate-400"><CalendarClock className="mx-auto h-10 w-10"/><p className="mt-3">No hay reservas activas.</p></div>}</div></>
    :<>
    <div className="mt-4 grid gap-3 rounded-2xl border bg-white p-4 shadow-sm md:grid-cols-[1fr_260px_auto] md:items-end">
      <label className="text-sm font-medium text-slate-700">Buscar
        <div className="relative mt-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"/><input value={saleFilter} onChange={e=>setSaleFilter(e.target.value)} placeholder="Cliente o predio" className="w-full rounded-xl border py-2.5 pl-9 pr-3 outline-none focus:border-[#52AD56] focus:ring-2 focus:ring-[#52AD56]/20"/></div>
      </label>
      <label className="text-sm font-medium text-slate-700">Estado
        <select value={saleStatusFilter} onChange={e=>setSaleStatusFilter(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2.5">
          <option value="ALL">Todos</option>
          <option value="CONFIRMED">Compra confirmada</option>
          <option value="PAYING">En proceso de pago</option>
          <option value="PAID">Pagado</option>
          <option value="INVOICED">Facturado</option>
          <option value="AWARDED">Adjudicado</option>
        </select>
      </label>
      <button type="button" onClick={()=>{setSaleFilter('');setSaleStatusFilter('ALL')}} className="rounded-xl border px-4 py-2.5 text-sm font-semibold text-slate-600">Limpiar</button>
      <p className="text-xs text-slate-400 md:col-span-3">{filteredSales.length} de {sales.length} compra(s)</p>
    </div>
    <div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3">Cliente</th><th className="px-5 py-3">Predio</th><th className="px-5 py-3">Precio</th><th className="px-5 py-3">Pagado</th><th className="px-5 py-3">Saldo</th><th className="px-5 py-3">Estado</th><th className="px-5 py-3 text-right">Documentos</th></tr></thead><tbody>{filteredSales.map(s=><tr key={s.id} className="border-t"><td className="px-5 py-4 font-medium">{s.customer}</td><td className="px-5 py-4">{s.property}</td><td className="px-5 py-4">$ {s.sale_price.toFixed(2)}</td><td className="px-5 py-4 text-emerald-700">$ {s.paid.toFixed(2)}</td><td className="px-5 py-4 font-semibold">$ {s.balance.toFixed(2)}</td><td className="px-5 py-4"><span className="text-xs font-semibold">{s.property_status==='INVOICED'?'Facturado':s.property_status==='PAID'?'Pagado':s.property_status==='PAYING'?'En proceso de pago':s.property_status}</span></td><td className="px-5 py-4"><div className="flex flex-wrap justify-end gap-2">{canCreateInvoice&&s.can_generate_invoice&&<button onClick={()=>generateInvoice(s)} className="inline-flex items-center gap-1 rounded-lg bg-[#3A6C32] px-3 py-2 text-xs font-semibold text-white"><ReceiptText className="h-4 w-4"/>Generar factura</button>}{s.invoice_id&&<span className="inline-flex items-center rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">Factura creada</span>}<button onClick={()=>showInstallments(s)} className="inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-xs font-semibold"><Eye className="h-4 w-4"/>Cuotas</button><button onClick={()=>apiDownload('/sales/'+s.id+'/statement.pdf','estado-cuenta.pdf')} className="inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-xs font-semibold text-[#3A6C32]"><FileText className="h-4 w-4"/>Estado</button><button onClick={()=>apiDownload('/sales/'+s.id+'/payments-certificate.pdf','certificado-pagos.pdf')} className="inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-xs font-semibold text-[#3A6C32]"><FileCheck2 className="h-4 w-4"/>Certificado</button>{canDeleteSale&&s.can_delete&&<button onClick={()=>deleteSale(s)} className="inline-flex items-center gap-1 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700"><Trash2 className="h-4 w-4"/>Eliminar</button>}</div></td></tr>)}</tbody></table>{!filteredSales.length&&<div className="py-14 text-center text-slate-400"><ShoppingCart className="mx-auto h-10 w-10"/><p className="mt-3">No hay compras confirmadas.</p></div>}</div></>}

    {open==='reservation'&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={saveReservation} className="w-full max-w-xl rounded-2xl bg-white p-6"><h3 className="text-xl font-semibold">Nueva reserva</h3><div className="mt-5 grid gap-4">
      <label>Cliente<div className="relative mt-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"/><input value={customerSearch} onChange={e=>setCustomerSearch(e.target.value)} placeholder="Buscar por cédula, nombre, correo o celular" className="w-full rounded-xl border py-2.5 pl-9 pr-3 outline-none focus:border-[#52AD56] focus:ring-2 focus:ring-[#52AD56]/20"/></div><select required value={resForm.customer_id} onChange={e=>setResForm({...resForm,customer_id:e.target.value})} className="mt-2 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{filteredCustomers.map(c=><option key={c.id} value={c.id}>{c.identification} · {c.full_name}</option>)}</select>{customerSearch&&<span className="mt-1 block text-xs text-slate-400">{filteredCustomers.length} cliente(s) encontrados</span>}</label>
      <label>Predio disponible<div className="relative mt-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"/><input value={propertySearch} onChange={e=>setPropertySearch(e.target.value)} placeholder="Buscar por código, manzana, lote o clave catastral" className="w-full rounded-xl border py-2.5 pl-9 pr-3 outline-none focus:border-[#52AD56] focus:ring-2 focus:ring-[#52AD56]/20"/></div><select required value={resForm.property_id} onChange={e=>setResForm({...resForm,property_id:e.target.value})} className="mt-2 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{filteredAvailableForReservation.map((p:any)=><option key={p.id} value={p.id}>{p.code} · {p.block} / Lote {p.lot_number} · {runtimeSettings.currency_symbol} {p.total_price.toFixed(2)}</option>)}</select>{propertySearch&&<span className="mt-1 block text-xs text-slate-400">{filteredAvailableForReservation.length} predio(s) encontrados</span>}</label>
      <div className="grid gap-4 sm:grid-cols-2"><label>Fecha<input type="date" value={resForm.reservation_date} onChange={e=>setResForm({...resForm,reservation_date:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label><label>Válida hasta<input type="date" value={resForm.expires_on} onChange={e=>setResForm({...resForm,expires_on:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label></div>
    </div><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(null)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Reservar</button></div></form></div>}

    {open==='sale'&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={saveSale} className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6"><div className="flex items-center gap-2"><BadgeCheck className="text-[#3A6C32]"/><h3 className="text-xl font-semibold">Confirmar compra</h3></div><div className="mt-5 grid gap-4 sm:grid-cols-2">
      <label className="sm:col-span-2">Cliente<div className="relative mt-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"/><input value={customerSearch} onChange={e=>setCustomerSearch(e.target.value)} placeholder="Buscar cliente" className="w-full rounded-xl border py-2.5 pl-9 pr-3"/></div><select required value={saleForm.customer_id} onChange={e=>setSaleForm({...saleForm,customer_id:e.target.value})} className="mt-2 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{filteredCustomers.map(c=><option key={c.id} value={c.id}>{c.identification} · {c.full_name}</option>)}</select></label>
      <label className="sm:col-span-2">Predio<div className="relative mt-1"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"/><input value={propertySearch} onChange={e=>setPropertySearch(e.target.value)} placeholder="Buscar predio" className="w-full rounded-xl border py-2.5 pl-9 pr-3"/></div><select required value={saleForm.property_id} onChange={e=>{const p=available.find((x:any)=>x.id===e.target.value);setSaleForm({...saleForm,property_id:e.target.value,sale_price:String(p?.total_price||'')})}} className="mt-2 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{filteredAvailableForSale.map((p:any)=><option key={p.id} value={p.id}>{p.code} · {p.block} / {p.lot_number}</option>)}</select></label>
      <label>Precio de venta<input required type="number" step="0.01" value={saleForm.sale_price} onChange={e=>setSaleForm({...saleForm,sale_price:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label>Entrada<input type="number" step="0.01" value={saleForm.down_payment} onChange={e=>setSaleForm({...saleForm,down_payment:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label>Número de cuotas<input required type="number" min="1" value={saleForm.installment_count} onChange={e=>setSaleForm({...saleForm,installment_count:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
      <label>Primera cuota<input required type="date" value={saleForm.first_due_date} onChange={e=>setSaleForm({...saleForm,first_due_date:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
    </div><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(null)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Confirmar compra</button></div></form></div>}

    {open==='installments'&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-white p-6"><div className="flex items-center justify-between gap-4"><div><h3 className="text-xl font-semibold">Plan de pagos</h3><p className="mt-1 text-sm text-slate-500">{selectedSale?.customer} · {selectedSale?.property}</p></div><div className="flex items-center gap-2">{!editingInstallments?<button onClick={()=>setEditingInstallments(true)} className="rounded-xl border px-4 py-2 text-sm font-semibold">Editar cuotas</button>:<><button onClick={()=>{setEditingInstallments(false);showInstallments(selectedSale)}} className="rounded-xl border px-4 py-2 text-sm">Cancelar</button><button onClick={saveInstallments} className="rounded-xl bg-[#3A6C32] px-4 py-2 text-sm font-semibold text-white">Guardar cambios</button></>}<button onClick={()=>setOpen(null)}>✕</button></div></div><div className="mt-4 grid gap-3 sm:grid-cols-3"><div className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-slate-500">Precio venta</p><p className="font-semibold">$ {Number(selectedSale?.sale_price||0).toFixed(2)}</p></div><div className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-slate-500">Entrada</p><p className="font-semibold">$ {Number(selectedSale?.down_payment||0).toFixed(2)}</p></div><div className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-slate-500">Suma cuotas</p><p className={'font-semibold '+(Math.abs(installments.reduce((s:number,i:any)=>s+Number(i.amount||0),0)-(Number(selectedSale?.sale_price||0)-Number(selectedSale?.down_payment||0)))<0.005?'text-emerald-700':'text-red-700')}>$ {installments.reduce((s:number,i:any)=>s+Number(i.amount||0),0).toFixed(2)}</p></div></div><div className="mt-5 overflow-hidden rounded-xl border"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">#</th><th className="px-4 py-3">Vencimiento</th><th className="px-4 py-3">Cuota</th><th className="px-4 py-3">Pagado</th><th className="px-4 py-3">Saldo</th><th className="px-4 py-3">Estado</th></tr></thead><tbody>{installments.map((i:any)=><tr key={i.id} className="border-t"><td className="px-4 py-3">{i.number}</td><td className="px-4 py-3">{editingInstallments?<input type="date" value={i.due_date} onChange={e=>updateInstallment(i.id,'due_date',e.target.value)} className="rounded-lg border px-2 py-1.5"/>:i.due_date}</td><td className="px-4 py-3">{editingInstallments?<input type="number" min={Math.max(0.01,Number(i.paid_amount||0))} step="0.01" value={i.amount} onChange={e=>updateInstallment(i.id,'amount',e.target.value)} className="w-28 rounded-lg border px-2 py-1.5"/>:<span>$ {Number(i.amount).toFixed(2)}</span>}</td><td className="px-4 py-3">$ {Number(i.paid_amount).toFixed(2)}</td><td className="px-4 py-3 font-medium">$ {(Number(i.amount)-Number(i.paid_amount)).toFixed(2)}</td><td className="px-4 py-3"><span className={'inline-flex rounded-full px-2 py-1 text-xs font-semibold '+installmentStatusBadgeClass(i.status)}>{i.status}</span></td></tr>)}</tbody></table></div></div></div>}
  </div>
}
