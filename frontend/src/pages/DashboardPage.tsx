import { useEffect, useMemo, useState } from 'react'
import { Building2, CircleDollarSign, Landmark, MapPinned, TrendingUp, WalletCards } from 'lucide-react'
import { apiFetch } from '../api'
import { propertyStatusBarClass } from '../utils/statusStyles'

const money=(v:number)=>'$ '+v.toLocaleString('es-EC',{minimumFractionDigits:2,maximumFractionDigits:2})

export default function DashboardPage(){
  const [data,setData]=useState<any|null>(null)
  const [projects,setProjects]=useState<any[]>([])
  const [stageId,setStageId]=useState('')

  async function load(id=''){
    const [d,p]=await Promise.all([apiFetch('/reports/dashboard'+(id?'?stage_id='+id:'')),apiFetch('/projects')])
    setData(d);setProjects(p)
  }
  useEffect(()=>{load()},[])
  async function changeStage(id:string){setStageId(id);await load(id)}
  const stages=useMemo(()=>projects.flatMap((p:any)=>p.stages||[]),[projects])
  if(!data)return <p>Cargando indicadores…</p>

  const t=data.totals
  const maxStatus=Math.max(1,...data.properties_by_status.map((x:any)=>x.count))
  const maxMonth=Math.max(1,...data.collections_by_month.map((x:any)=>x.amount))

  const cards=[
    ['Predios registrados',String(t.properties),MapPinned],
    ['Compras confirmadas',String(t.confirmed),Building2],
    ['Total recaudado',money(t.collected),CircleDollarSign],
    ['Cartera pendiente',money(t.pending),Landmark],
    ['Cartera vencida',money(t.overdue),WalletCards],
    ['Recuperación',t.recovery_percentage.toFixed(2)+' %',TrendingUp],
  ] as const

  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div><p className="text-sm font-semibold text-[#52AD56]">Proyecto San Joaquín</p><h2 className="mt-1 text-2xl font-semibold text-slate-900">Resumen ejecutivo</h2><p className="mt-1 text-sm text-slate-500">Indicadores calculados directamente desde PostgreSQL.</p></div>
      <select value={stageId} onChange={e=>changeStage(e.target.value)} className="rounded-xl border bg-white px-4 py-2.5 text-sm"><option value="">Todas las etapas</option>{stages.map((s:any)=><option key={s.id} value={s.id}>{s.name}</option>)}</select>
    </div>

    <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {cards.map(([label,value,Icon])=><div key={label} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><span className="text-sm text-slate-500">{label}</span><span className="rounded-xl bg-emerald-50 p-2 text-[#3A6C32]"><Icon className="h-5 w-5"/></span></div><p className="mt-5 text-2xl font-semibold text-slate-900">{value}</p></div>)}
    </div>

    <div className="mt-6 grid gap-5 xl:grid-cols-2">
      <section className="rounded-2xl border bg-white p-6 shadow-sm"><div className="flex items-center justify-between"><div><h3 className="font-semibold text-slate-900">Predios por estado</h3><p className="mt-1 text-sm text-slate-500">Distribución actual del inventario.</p></div><span className="text-xs text-slate-400">Total {t.properties}</span></div>
        <div className="mt-6 space-y-4">{data.properties_by_status.map((x:any)=><div key={x.status}><div className="mb-1 flex justify-between text-sm"><span>{x.status}</span><span className="font-semibold">{x.count}</span></div><div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className={'h-full rounded-full '+propertyStatusBarClass(x.status)} style={{width:(x.count/maxStatus*100)+'%'}}/></div></div>)}{!data.properties_by_status.length&&<p className="py-10 text-center text-sm text-slate-400">Aún no hay predios registrados.</p>}</div>
      </section>

      <section className="rounded-2xl border bg-white p-6 shadow-sm"><div><h3 className="font-semibold text-slate-900">Recaudación mensual</h3><p className="mt-1 text-sm text-slate-500">Últimos meses con movimientos registrados.</p></div>
        <div className="mt-6 space-y-4">{data.collections_by_month.map((x:any)=><div key={x.month}><div className="mb-1 flex justify-between text-sm"><span>{x.month}</span><span className="font-semibold">{money(x.amount)}</span></div><div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-[#FAB71C]" style={{width:(x.amount/maxMonth*100)+'%'}}/></div></div>)}{!data.collections_by_month.length&&<p className="py-10 text-center text-sm text-slate-400">Aún no hay pagos registrados.</p>}</div>
      </section>
    </div>

    <div className="mt-5 rounded-2xl border bg-white p-6 shadow-sm">
      <h3 className="font-semibold text-slate-900">Resumen financiero</h3>
      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div><p className="text-xs uppercase tracking-wide text-slate-400">Valor total predios</p><p className="mt-1 text-lg font-semibold">{money(t.total_value)}</p></div>
        <div><p className="text-xs uppercase tracking-wide text-slate-400">Ventas comprometidas</p><p className="mt-1 text-lg font-semibold">{money(t.committed_sales)}</p></div>
        <div><p className="text-xs uppercase tracking-wide text-slate-400">Disponibles</p><p className="mt-1 text-lg font-semibold">{t.available}</p></div>
        <div><p className="text-xs uppercase tracking-wide text-slate-400">Pagados / adjudicados</p><p className="mt-1 text-lg font-semibold">{t.paid}</p></div>
      </div>
    </div>
  </div>
}
