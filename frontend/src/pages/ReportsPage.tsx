import { useEffect, useState } from 'react'
import { Download, FileBarChart2 } from 'lucide-react'
import { apiDownload, apiFetch } from '../api'

type Tab='properties'|'collections'|'receivables'
const today=()=>new Date().toISOString().slice(0,10)

export default function ReportsPage(){
  const [tab,setTab]=useState<Tab>('properties')
  const [projects,setProjects]=useState<any[]>([])
  const [statuses,setStatuses]=useState<any[]>([])
  const [rows,setRows]=useState<any[]>([])
  const [stageId,setStageId]=useState('')
  const [statusCode,setStatusCode]=useState('')
  const [dateFrom,setDateFrom]=useState('')
  const [dateTo,setDateTo]=useState(today())

  useEffect(()=>{Promise.all([apiFetch('/projects'),apiFetch('/property-statuses')]).then(([p,s])=>{setProjects(p);setStatuses(s)})},[])
  useEffect(()=>{load()},[tab,stageId,statusCode,dateFrom,dateTo])

  function params(){
    const p=new URLSearchParams()
    if(stageId)p.set('stage_id',stageId)
    if(tab==='properties'&&statusCode)p.set('status_code',statusCode)
    if(tab==='collections'){if(dateFrom)p.set('date_from',dateFrom);if(dateTo)p.set('date_to',dateTo)}
    const q=p.toString()
    return q?'?'+q:''
  }
  async function load(){setRows(await apiFetch('/reports/'+tab+params()))}
  async function exportCsv(){await apiDownload('/reports/'+tab+'.csv'+params(),tab+'.csv')}
  const stages=projects.flatMap((p:any)=>p.stages||[])
  const totalCollections=tab==='collections'?rows.reduce((a:number,r:any)=>a+r.amount,0):0
  const totalBalance=tab==='receivables'?rows.reduce((a:number,r:any)=>a+r.balance,0):0
  const totalOverdue=tab==='receivables'?rows.reduce((a:number,r:any)=>a+r.overdue,0):0

  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between"><div><p className="text-sm font-semibold text-[#52AD56]">Análisis institucional</p><h2 className="mt-1 text-2xl font-semibold">Reportes</h2><p className="mt-1 text-sm text-slate-500">Inventario, recaudación y cartera con información actual de la base de datos.</p></div><button onClick={exportCsv} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white"><Download className="h-4 w-4"/>Exportar CSV</button></div>

    <div className="mt-6 flex flex-wrap gap-2">{[['properties','Predios'],['collections','Recaudación'],['receivables','Cartera']].map(([key,label])=><button key={key} onClick={()=>setTab(key as Tab)} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(tab===key?'bg-[#3A6C32] text-white':'border bg-white')}>{label}</button>)}</div>

    <div className="mt-4 flex flex-wrap gap-3 rounded-2xl border bg-white p-4 shadow-sm">
      <select value={stageId} onChange={e=>setStageId(e.target.value)} className="rounded-xl border px-3 py-2.5 text-sm"><option value="">Todas las etapas</option>{stages.map((s:any)=><option key={s.id} value={s.id}>{s.name}</option>)}</select>
      {tab==='properties'&&<select value={statusCode} onChange={e=>setStatusCode(e.target.value)} className="rounded-xl border px-3 py-2.5 text-sm"><option value="">Todos los estados</option>{statuses.map((s:any)=><option key={s.id} value={s.code}>{s.name}</option>)}</select>}
      {tab==='collections'&&<><label className="text-sm text-slate-500">Desde <input type="date" value={dateFrom} onChange={e=>setDateFrom(e.target.value)} className="ml-2 rounded-xl border px-3 py-2"/></label><label className="text-sm text-slate-500">Hasta <input type="date" value={dateTo} onChange={e=>setDateTo(e.target.value)} className="ml-2 rounded-xl border px-3 py-2"/></label></>}
    </div>

    {tab==='collections'&&<div className="mt-4 rounded-2xl border bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Total recaudado según filtros</p><p className="mt-1 text-2xl font-semibold text-emerald-700">$ {totalCollections.toLocaleString('es-EC',{minimumFractionDigits:2})}</p></div>}
    {tab==='receivables'&&<div className="mt-4 grid gap-4 md:grid-cols-2"><div className="rounded-2xl border bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Saldo pendiente</p><p className="mt-1 text-2xl font-semibold">$ {totalBalance.toLocaleString('es-EC',{minimumFractionDigits:2})}</p></div><div className="rounded-2xl border bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Saldo vencido</p><p className="mt-1 text-2xl font-semibold text-amber-700">$ {totalOverdue.toLocaleString('es-EC',{minimumFractionDigits:2})}</p></div></div>}

    <div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm"><div className="overflow-x-auto">
      {tab==='properties'&&<table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Código</th><th className="px-4 py-3">Etapa</th><th className="px-4 py-3">Manzana</th><th className="px-4 py-3">Lote</th><th className="px-4 py-3">Área</th><th className="px-4 py-3">Precio</th><th className="px-4 py-3">Estado</th></tr></thead><tbody>{rows.map((r:any)=><tr key={r.code} className="border-t"><td className="px-4 py-3 font-medium">{r.code}</td><td className="px-4 py-3">{r.stage}</td><td className="px-4 py-3">{r.block}</td><td className="px-4 py-3">{r.lot}</td><td className="px-4 py-3">{r.area_m2.toFixed(2)} m²</td><td className="px-4 py-3">$ {r.total_price.toFixed(2)}</td><td className="px-4 py-3">{r.status}</td></tr>)}</tbody></table>}
      {tab==='collections'&&<table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Fecha</th><th className="px-4 py-3">Cliente</th><th className="px-4 py-3">Etapa</th><th className="px-4 py-3">Predio</th><th className="px-4 py-3">Forma</th><th className="px-4 py-3">Referencia</th><th className="px-4 py-3 text-right">Valor</th></tr></thead><tbody>{rows.map((r:any,i:number)=><tr key={i} className="border-t"><td className="px-4 py-3">{r.date}</td><td className="px-4 py-3 font-medium">{r.customer}</td><td className="px-4 py-3">{r.stage}</td><td className="px-4 py-3">{r.property}</td><td className="px-4 py-3">{r.method}</td><td className="px-4 py-3">{r.reference||'-'}</td><td className="px-4 py-3 text-right font-semibold">$ {r.amount.toFixed(2)}</td></tr>)}</tbody></table>}
      {tab==='receivables'&&<table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Cliente</th><th className="px-4 py-3">Etapa</th><th className="px-4 py-3">Manzana</th><th className="px-4 py-3">Predio</th><th className="px-4 py-3">Saldo</th><th className="px-4 py-3">Vencido</th><th className="px-4 py-3">Cuotas vencidas</th><th className="px-4 py-3">Próx. vencimiento</th></tr></thead><tbody>{rows.map((r:any,i:number)=><tr key={i} className="border-t"><td className="px-4 py-3 font-medium">{r.customer}</td><td className="px-4 py-3">{r.stage}</td><td className="px-4 py-3">{r.block}</td><td className="px-4 py-3">{r.property}</td><td className="px-4 py-3 font-semibold">$ {r.balance.toFixed(2)}</td><td className="px-4 py-3 text-amber-700">$ {r.overdue.toFixed(2)}</td><td className="px-4 py-3">{r.overdue_installments}</td><td className="px-4 py-3">{r.next_due||'-'}</td></tr>)}</tbody></table>}
      {!rows.length&&<div className="py-14 text-center text-slate-400"><FileBarChart2 className="mx-auto h-10 w-10"/><p className="mt-3">No existen datos para los filtros seleccionados.</p></div>}
    </div></div>
  </div>
}
