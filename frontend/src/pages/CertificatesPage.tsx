import { useEffect, useState } from 'react'
import { Download, FileCheck2, Search, ShieldCheck } from 'lucide-react'
import { apiDownload, apiFetch } from '../api'

const TYPES=[
  ['','Todos los documentos'],
  ['PAYMENT_RECEIPT','Comprobante de pago'],
  ['ACCOUNT_STATEMENT','Estado de cuenta'],
  ['PAYMENTS_CERTIFICATE','Certificado de pagos'],
]

export default function CertificatesPage(){
  const [rows,setRows]=useState<any[]>([])
  const [q,setQ]=useState('')
  const [type,setType]=useState('')
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState('')

  async function load(){
    setLoading(true);setError('')
    const p=new URLSearchParams()
    if(q)p.set('q',q)
    if(type)p.set('document_type',type)
    try{setRows(await apiFetch('/documents'+(p.toString()?'?'+p.toString():'')))}catch(e:any){setError(e.message);setRows([])}finally{setLoading(false)}
  }
  useEffect(()=>{load()},[])

  async function download(row:any){
    await apiDownload('/documents/'+row.id+'/download.pdf',row.document_number+'.pdf')
  }

  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div><p className="text-sm font-semibold text-[#52AD56]">Documentación institucional</p><h2 className="mt-1 text-2xl font-semibold">Certificados y documentos</h2><p className="mt-1 text-sm text-slate-500">Consulta y reimpresión de documentos oficiales emitidos por el sistema.</p></div>
    </div>

    <div className="mt-6 flex flex-col gap-3 rounded-2xl border bg-white p-4 shadow-sm md:flex-row">
      <div className="flex flex-1 items-center rounded-xl border px-3"><Search className="h-4 w-4 text-slate-400"/><input value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==='Enter'&&load()} className="w-full px-3 py-2 outline-none" placeholder="Número, cliente, cédula o predio"/></div>
      <select value={type} onChange={e=>setType(e.target.value)} className="rounded-xl border px-3 py-2.5 text-sm">{TYPES.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select>
      <button onClick={load} className="rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white">Buscar</button>
    </div>

    {error&&<div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

    <div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm">
      <div className="overflow-x-auto"><table className="min-w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Documento</th><th className="px-4 py-3">Tipo</th><th className="px-4 py-3">Cliente</th><th className="px-4 py-3">Predio</th><th className="px-4 py-3">Emisión</th><th className="px-4 py-3">Validación</th><th></th></tr></thead>
        <tbody>{rows.map(r=><tr key={r.id} className="border-t"><td className="px-4 py-3 font-semibold">{r.document_number}</td><td className="px-4 py-3">{r.document_label}</td><td className="px-4 py-3"><p className="font-medium">{r.customer||'-'}</p><p className="text-xs text-slate-500">{r.identification||''}</p></td><td className="px-4 py-3">{r.property||'-'}</td><td className="px-4 py-3">{new Date(r.created_at).toLocaleString('es-EC')}</td><td className="px-4 py-3"><span className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700"><ShieldCheck className="h-3.5 w-3.5"/>Válido</span><p className="mt-1 max-w-44 truncate text-xs text-slate-400" title={r.verification_code}>{r.verification_code}</p></td><td className="px-4 py-3 text-right"><button onClick={()=>download(r)} className="inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-xs font-semibold text-[#3A6C32]"><Download className="h-4 w-4"/>PDF</button></td></tr>)}</tbody>
      </table>
      {!loading&&!rows.length&&<div className="py-14 text-center text-slate-400"><FileCheck2 className="mx-auto h-10 w-10"/><p className="mt-3">No existen documentos emitidos para los filtros seleccionados.</p></div>}
      {loading&&<div className="py-12 text-center text-sm text-slate-500">Cargando documentos…</div>}
      </div>
    </div>
  </div>
}
