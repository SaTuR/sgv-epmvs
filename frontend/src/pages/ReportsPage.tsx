import { useEffect, useState } from 'react'
import { AlertCircle, Download, FileBarChart2, FileSpreadsheet, FileText, Loader2 } from 'lucide-react'
import { apiDownload, apiFetch } from '../api'
import { propertyStatusBadgeClass } from '../utils/statusStyles'

type Tab='properties'|'collections'|'receivables'|'commissions'
type CommissionView='summary'|'detail'
const today=()=>new Date().toISOString().slice(0,10)
const money=(v:any)=>Number(v||0).toLocaleString('es-EC',{minimumFractionDigits:2,maximumFractionDigits:2})

export default function ReportsPage(){
  const [tab,setTab]=useState<Tab>('properties')
  const [projects,setProjects]=useState<any[]>([])
  const [statuses,setStatuses]=useState<any[]>([])
  const [sellers,setSellers]=useState<any[]>([])
  const [rows,setRows]=useState<any[]>([])
  const [commissionTotals,setCommissionTotals]=useState<any>(null)
  const [stageId,setStageId]=useState('')
  const [statusCode,setStatusCode]=useState('')
  const [sellerId,setSellerId]=useState('')
  const [commissionStatus,setCommissionStatus]=useState('ALL')
  const [commissionView,setCommissionView]=useState<CommissionView>('summary')
  const [dateFrom,setDateFrom]=useState('')
  const [dateTo,setDateTo]=useState(today())
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState('')

  useEffect(()=>{
    Promise.all([apiFetch('/projects'),apiFetch('/property-statuses'),apiFetch('/sellers')])
      .then(([p,s,v])=>{setProjects(p);setStatuses(s);setSellers(v)})
      .catch((e:any)=>setError(e.message||'No fue posible cargar los filtros'))
  },[])

  useEffect(()=>{load()},[tab,stageId,statusCode,dateFrom,dateTo,sellerId,commissionStatus,commissionView])

  function params(includeView=true){
    const p=new URLSearchParams()
    if(stageId)p.set('stage_id',stageId)
    if(tab==='properties'&&statusCode)p.set('status_code',statusCode)
    if(tab==='collections'){
      if(dateFrom)p.set('date_from',dateFrom)
      if(dateTo)p.set('date_to',dateTo)
    }
    if(tab==='commissions'){
      if(sellerId)p.set('seller_id',sellerId)
      if(commissionStatus!=='ALL')p.set('status',commissionStatus)
      if(dateFrom)p.set('date_from',dateFrom)
      if(dateTo)p.set('date_to',dateTo)
      if(includeView)p.set('view',commissionView)
    }
    const q=p.toString()
    return q?'?'+q:''
  }

  async function load(){
    setLoading(true)
    setError('')
    setRows([])
    setCommissionTotals(null)
    try{
      const data=await apiFetch('/reports/'+tab+params())
      if(tab==='commissions'){
        setCommissionTotals(data.totals||null)
        setRows(commissionView==='summary'?(data.sellers||[]):(data.rows||[]))
      }else{
        setRows(Array.isArray(data)?data:[])
      }
    }catch(e:any){
      setError(e.message||'No fue posible cargar el reporte')
      setRows([])
    }finally{
      setLoading(false)
    }
  }

  function changeTab(next:Tab){
    if(next===tab)return
    setRows([])
    setCommissionTotals(null)
    setError('')
    setLoading(true)
    setTab(next)
  }

  async function exportFile(ext:'csv'|'xlsx'|'pdf'){
    try{
      setError('')
      await apiDownload('/reports/'+tab+'.'+ext+params(false),tab+'.'+ext)
    }catch(e:any){
      setError(e.message||'No fue posible exportar el reporte')
    }
  }

  const stages=projects.flatMap((p:any)=>p.stages||[])
  const totalCollections=tab==='collections'?rows.reduce((a:number,r:any)=>a+Number(r.amount||0),0):0
  const totalBalance=tab==='receivables'?rows.reduce((a:number,r:any)=>a+Number(r.balance||0),0):0
  const totalOverdue=tab==='receivables'?rows.reduce((a:number,r:any)=>a+Number(r.overdue||0),0):0

  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div><p className="text-sm font-semibold text-[#52AD56]">Análisis institucional</p><h2 className="mt-1 text-2xl font-semibold">Reportes</h2><p className="mt-1 text-sm text-slate-500">Inventario, recaudación, cartera y gestión comercial con información actual de la base de datos.</p></div>
      {tab==='commissions'?<div className="flex flex-wrap gap-2">
        <button onClick={()=>exportFile('csv')} disabled={loading} className="inline-flex items-center gap-2 rounded-xl border bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 disabled:opacity-50"><Download className="h-4 w-4"/>CSV</button>
        <button onClick={()=>exportFile('xlsx')} disabled={loading} className="inline-flex items-center gap-2 rounded-xl border bg-white px-4 py-2.5 text-sm font-semibold text-[#3A6C32] disabled:opacity-50"><FileSpreadsheet className="h-4 w-4"/>Excel</button>
        <button onClick={()=>exportFile('pdf')} disabled={loading} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"><FileText className="h-4 w-4"/>PDF</button>
      </div>:<button onClick={()=>exportFile('csv')} disabled={loading} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"><Download className="h-4 w-4"/>Exportar CSV</button>}
    </div>

    <div className="mt-6 flex flex-wrap gap-2">
      <button onClick={()=>changeTab('properties')} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(tab==='properties'?'bg-[#3A6C32] text-white':'border bg-white')}>Predios</button>
      <button onClick={()=>changeTab('collections')} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(tab==='collections'?'bg-[#3A6C32] text-white':'border bg-white')}>Recaudación</button>
      <button onClick={()=>changeTab('receivables')} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(tab==='receivables'?'bg-[#3A6C32] text-white':'border bg-white')}>Cartera</button>
      <button onClick={()=>changeTab('commissions')} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(tab==='commissions'?'bg-[#3A6C32] text-white':'border bg-white')}>Comisiones</button>
    </div>

    <div className="mt-4 flex flex-wrap items-end gap-3 rounded-2xl border bg-white p-4 shadow-sm">
      <label className="text-sm text-slate-500">Etapa<select value={stageId} onChange={e=>setStageId(e.target.value)} className="mt-1 block rounded-xl border px-3 py-2.5 text-sm">
        <option value="">Todas las etapas</option>
        {stages.map((s:any)=><option key={s.id} value={s.id}>{s.name}</option>)}
      </select></label>

      {tab==='properties'&&<label className="text-sm text-slate-500">Estado<select value={statusCode} onChange={e=>setStatusCode(e.target.value)} className="mt-1 block rounded-xl border px-3 py-2.5 text-sm">
        <option value="">Todos los estados</option>
        {statuses.map((s:any)=><option key={s.id} value={s.code}>{s.name}</option>)}
      </select></label>}

      {tab==='collections'&&<>
        <label className="text-sm text-slate-500">Desde<input type="date" value={dateFrom} onChange={e=>setDateFrom(e.target.value)} className="mt-1 block rounded-xl border px-3 py-2"/></label>
        <label className="text-sm text-slate-500">Hasta<input type="date" value={dateTo} onChange={e=>setDateTo(e.target.value)} className="mt-1 block rounded-xl border px-3 py-2"/></label>
      </>}

      {tab==='commissions'&&<>
        <label className="text-sm text-slate-500">Vendedor<select value={sellerId} onChange={e=>setSellerId(e.target.value)} className="mt-1 block min-w-56 rounded-xl border px-3 py-2.5 text-sm"><option value="">Todos los vendedores</option>{sellers.map((s:any)=><option key={s.id} value={s.id}>{s.full_name}</option>)}</select></label>
        <label className="text-sm text-slate-500">Estado<select value={commissionStatus} onChange={e=>setCommissionStatus(e.target.value)} className="mt-1 block rounded-xl border px-3 py-2.5 text-sm"><option value="ALL">Todos</option><option value="PENDING">Pendiente</option><option value="APPROVED">Aprobada</option><option value="PAID">Pagada</option><option value="CANCELLED">Anulada</option></select></label>
        <label className="text-sm text-slate-500">Desde<input type="date" value={dateFrom} onChange={e=>setDateFrom(e.target.value)} className="mt-1 block rounded-xl border px-3 py-2"/></label>
        <label className="text-sm text-slate-500">Hasta<input type="date" value={dateTo} onChange={e=>setDateTo(e.target.value)} className="mt-1 block rounded-xl border px-3 py-2"/></label>
        <div className="ml-auto flex gap-2"><button onClick={()=>setCommissionView('summary')} className={'rounded-xl px-4 py-2.5 text-sm font-semibold '+(commissionView==='summary'?'bg-[#3A6C32] text-white':'border bg-white')}>Resumen</button><button onClick={()=>setCommissionView('detail')} className={'rounded-xl px-4 py-2.5 text-sm font-semibold '+(commissionView==='detail'?'bg-[#3A6C32] text-white':'border bg-white')}>Detalle</button></div>
      </>}
    </div>

    {error&&<div className="mt-4 flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"><AlertCircle className="mt-0.5 h-5 w-5 shrink-0"/><div><p className="font-semibold">No fue posible cargar el reporte.</p><p className="mt-1">{error}</p></div></div>}

    {tab==='collections'&&!loading&&<div className="mt-4 rounded-2xl border bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Total recaudado según filtros</p><p className="mt-1 text-2xl font-semibold text-emerald-700">$ {money(totalCollections)}</p></div>}

    {tab==='receivables'&&!loading&&<div className="mt-4 grid gap-4 md:grid-cols-2">
      <div className="rounded-2xl border bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Saldo pendiente</p><p className="mt-1 text-2xl font-semibold">$ {money(totalBalance)}</p></div>
      <div className="rounded-2xl border bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Saldo vencido</p><p className="mt-1 text-2xl font-semibold text-amber-700">$ {money(totalOverdue)}</p></div>
    </div>}

    {tab==='commissions'&&!loading&&commissionTotals&&<div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
      <div className="rounded-2xl border bg-white p-4 shadow-sm"><p className="text-xs text-slate-500">Valor vendido</p><p className="mt-1 text-lg font-semibold">$ {money(commissionTotals.sold_amount)}</p><p className="text-xs text-slate-400">{commissionTotals.sales_count} venta(s)</p></div>
      <div className="rounded-2xl border bg-white p-4 shadow-sm"><p className="text-xs text-slate-500">Comisión generada</p><p className="mt-1 text-lg font-semibold text-emerald-700">$ {money(commissionTotals.generated)}</p></div>
      <div className="rounded-2xl border bg-white p-4 shadow-sm"><p className="text-xs text-slate-500">Pendiente</p><p className="mt-1 text-lg font-semibold text-amber-700">$ {money(commissionTotals.pending)}</p></div>
      <div className="rounded-2xl border bg-white p-4 shadow-sm"><p className="text-xs text-slate-500">Aprobada</p><p className="mt-1 text-lg font-semibold text-blue-700">$ {money(commissionTotals.approved)}</p></div>
      <div className="rounded-2xl border bg-white p-4 shadow-sm"><p className="text-xs text-slate-500">Pagada</p><p className="mt-1 text-lg font-semibold text-[#3A6C32]">$ {money(commissionTotals.paid)}</p></div>
      <div className="rounded-2xl border bg-white p-4 shadow-sm"><p className="text-xs text-slate-500">Anulada</p><p className="mt-1 text-lg font-semibold text-red-700">$ {money(commissionTotals.cancelled)}</p></div>
    </div>}

    <div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm">
      {loading?<div className="flex items-center justify-center gap-2 py-16 text-slate-500"><Loader2 className="h-5 w-5 animate-spin"/>Cargando reporte…</div>:
      <div className="overflow-x-auto">
        {tab==='properties'&&<table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Código</th><th className="px-4 py-3">Etapa</th><th className="px-4 py-3">Manzana</th><th className="px-4 py-3">Lote</th><th className="px-4 py-3">Área</th><th className="px-4 py-3">Precio</th><th className="px-4 py-3">Estado</th></tr></thead><tbody>{rows.map((r:any)=><tr key={r.code} className="border-t"><td className="px-4 py-3 font-medium">{r.code}</td><td className="px-4 py-3">{r.stage}</td><td className="px-4 py-3">{r.block}</td><td className="px-4 py-3">{r.lot}</td><td className="px-4 py-3">{Number(r.area_m2||0).toFixed(2)} m²</td><td className="px-4 py-3">$ {money(r.total_price)}</td><td className="px-4 py-3"><span className={'inline-flex rounded-full px-2.5 py-1 text-xs font-semibold '+propertyStatusBadgeClass(r.status)}>{r.status}</span></td></tr>)}</tbody></table>}

        {tab==='collections'&&<table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Fecha</th><th className="px-4 py-3">Cliente</th><th className="px-4 py-3">Etapa</th><th className="px-4 py-3">Predio</th><th className="px-4 py-3">Forma</th><th className="px-4 py-3">Referencia interna</th><th className="px-4 py-3">Comprobante bancario</th><th className="px-4 py-3 text-right">Valor</th></tr></thead><tbody>{rows.map((r:any,i:number)=><tr key={i} className="border-t"><td className="px-4 py-3">{r.date||'-'}</td><td className="px-4 py-3 font-medium">{r.customer||'-'}</td><td className="px-4 py-3">{r.stage||'-'}</td><td className="px-4 py-3">{r.property||'-'}</td><td className="px-4 py-3">{r.method||'-'}</td><td className="px-4 py-3">{r.reference||'-'}</td><td className="px-4 py-3">{r.bank_receipt||'-'}</td><td className="px-4 py-3 text-right font-semibold">$ {money(r.amount)}</td></tr>)}</tbody></table>}

        {tab==='receivables'&&<table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Cliente</th><th className="px-4 py-3">Etapa</th><th className="px-4 py-3">Manzana</th><th className="px-4 py-3">Predio</th><th className="px-4 py-3">Saldo</th><th className="px-4 py-3">Vencido</th><th className="px-4 py-3">Cuotas vencidas</th><th className="px-4 py-3">Próx. vencimiento</th></tr></thead><tbody>{rows.map((r:any,i:number)=><tr key={i} className="border-t"><td className="px-4 py-3 font-medium">{r.customer||'-'}</td><td className="px-4 py-3">{r.stage||'-'}</td><td className="px-4 py-3">{r.block||'-'}</td><td className="px-4 py-3">{r.property||'-'}</td><td className="px-4 py-3 font-semibold">$ {money(r.balance)}</td><td className="px-4 py-3 text-amber-700">$ {money(r.overdue)}</td><td className="px-4 py-3">{r.overdue_installments||0}</td><td className="px-4 py-3">{r.next_due||'-'}</td></tr>)}</tbody></table>}

        {tab==='commissions'&&commissionView==='summary'&&<table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Vendedor</th><th className="px-4 py-3 text-right">Ventas</th><th className="px-4 py-3 text-right">Valor vendido</th><th className="px-4 py-3 text-right">Generada</th><th className="px-4 py-3 text-right">Pendiente</th><th className="px-4 py-3 text-right">Aprobada</th><th className="px-4 py-3 text-right">Pagada</th><th className="px-4 py-3 text-right">Anulada</th></tr></thead><tbody>{rows.map((r:any)=><tr key={r.seller_id} className="border-t"><td className="px-4 py-3 font-medium">{r.seller}</td><td className="px-4 py-3 text-right">{r.sales_count}</td><td className="px-4 py-3 text-right">$ {money(r.sold_amount)}</td><td className="px-4 py-3 text-right font-semibold text-emerald-700">$ {money(r.generated)}</td><td className="px-4 py-3 text-right">$ {money(r.pending)}</td><td className="px-4 py-3 text-right">$ {money(r.approved)}</td><td className="px-4 py-3 text-right">$ {money(r.paid)}</td><td className="px-4 py-3 text-right text-red-700">$ {money(r.cancelled)}</td></tr>)}</tbody></table>}

        {tab==='commissions'&&commissionView==='detail'&&<table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Fecha</th><th className="px-4 py-3">Vendedor</th><th className="px-4 py-3">Cliente</th><th className="px-4 py-3">Etapa</th><th className="px-4 py-3">Predio</th><th className="px-4 py-3 text-right">Venta</th><th className="px-4 py-3 text-right">%</th><th className="px-4 py-3 text-right">Comisión</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3">Ref. pago</th></tr></thead><tbody>{rows.map((r:any)=><tr key={r.id} className="border-t"><td className="px-4 py-3">{r.date}</td><td className="px-4 py-3 font-medium">{r.seller}</td><td className="px-4 py-3">{r.customer}</td><td className="px-4 py-3">{r.stage}</td><td className="px-4 py-3">{r.property}</td><td className="px-4 py-3 text-right">$ {money(r.sale_price)}</td><td className="px-4 py-3 text-right">{Number(r.commission_rate).toFixed(2)}%</td><td className="px-4 py-3 text-right font-semibold text-emerald-700">$ {money(r.commission_amount)}</td><td className="px-4 py-3">{r.status_label}</td><td className="px-4 py-3">{r.payment_reference||'-'}</td></tr>)}</tbody></table>}

        {!rows.length&&!error&&<div className="py-14 text-center text-slate-400"><FileBarChart2 className="mx-auto h-10 w-10"/><p className="mt-3">No existen datos para los filtros seleccionados.</p></div>}
      </div>}
    </div>
  </div>
}
