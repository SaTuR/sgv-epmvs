import { useEffect, useState } from 'react'
import { AlertTriangle, Landmark } from 'lucide-react'
import { apiFetch } from '../api'

export default function ReceivablesPage(){
  const [rows,setRows]=useState<any[]>([])
  useEffect(()=>{apiFetch('/accounts-receivable').then(setRows)},[])
  const total=rows.reduce((a,r)=>a+r.balance,0)
  const overdue=rows.reduce((a,r)=>a+r.overdue,0)
  return <div>
    <div><p className="text-sm font-semibold text-[#52AD56]">Financiero / Cartera</p><h2 className="mt-1 text-2xl font-semibold">Cuentas por cobrar</h2><p className="mt-1 text-sm text-slate-500">Solo compras confirmadas con saldo pendiente.</p></div>
    <div className="mt-6 grid gap-4 md:grid-cols-2"><div className="rounded-2xl border bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><span className="text-sm text-slate-500">Cartera pendiente</span><Landmark className="h-5 w-5 text-[#3A6C32]"/></div><p className="mt-4 text-2xl font-semibold">$ {total.toLocaleString('es-EC',{minimumFractionDigits:2})}</p></div><div className="rounded-2xl border bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><span className="text-sm text-slate-500">Cartera vencida</span><AlertTriangle className="h-5 w-5 text-amber-600"/></div><p className="mt-4 text-2xl font-semibold text-amber-700">$ {overdue.toLocaleString('es-EC',{minimumFractionDigits:2})}</p></div></div>
    <div className="mt-5 overflow-hidden rounded-2xl border bg-white shadow-sm"><div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3">Cliente</th><th className="px-5 py-3">Identificación</th><th className="px-5 py-3">Predio</th><th className="px-5 py-3">Saldo</th><th className="px-5 py-3">Vencido</th><th className="px-5 py-3">Cuotas vencidas</th><th className="px-5 py-3">Días mora</th><th className="px-5 py-3">Próx. vencimiento</th></tr></thead><tbody>{rows.map(r=><tr key={r.sale_id} className="border-t"><td className="px-5 py-4 font-medium">{r.customer}</td><td className="px-5 py-4">{r.identification}</td><td className="px-5 py-4">{r.property}</td><td className="px-5 py-4 font-semibold">$ {r.balance.toFixed(2)}</td><td className={'px-5 py-4 '+(r.overdue>0?'font-semibold text-amber-700':'text-slate-500')}>$ {r.overdue.toFixed(2)}</td><td className="px-5 py-4">{r.overdue_installments}</td><td className="px-5 py-4">{r.days_overdue}</td><td className="px-5 py-4">{r.next_due||'-'}</td></tr>)}</tbody></table>{!rows.length&&<div className="py-14 text-center text-slate-400"><Landmark className="mx-auto h-10 w-10"/><p className="mt-3">No existen cuentas por cobrar.</p></div>}</div></div>
  </div>
}
