import { useEffect, useState } from 'react'
import { Download, FileText, RefreshCw } from 'lucide-react'
import { apiDownload, apiFetch } from '../api'

export default function ElectronicInvoicesPage(){
  const [rows,setRows]=useState<any[]>([])
  const [error,setError]=useState('')
  const [loading,setLoading]=useState(true)
  const [action,setAction]=useState('')

  async function load(){
    setLoading(true);setError('')
    try{setRows(await apiFetch('/electronic-invoices'))}
    catch(e:any){setError(e.message||'No fue posible cargar las facturas electrónicas')}
    finally{setLoading(false)}
  }

  useEffect(()=>{load()},[])

  async function generateXml(id:string){
    setAction(id);setError('')
    try{
      await apiFetch('/electronic-invoices/'+id+'/generate-xml',{method:'POST'})
      await load()
    }catch(e:any){setError(e.message||'No fue posible generar el XML')}
    finally{setAction('')}
  }

  async function downloadXml(id:string){
    setAction(id);setError('')
    try{await apiDownload('/electronic-invoices/'+id+'/xml','factura.xml')}
    catch(e:any){setError(e.message||'No fue posible descargar el XML')}
    finally{setAction('')}
  }

  function badge(status:string){
    if(status==='AUTHORIZED')return 'border-emerald-200 bg-emerald-50 text-emerald-700'
    if(status==='REJECTED'||status==='ERROR')return 'border-red-200 bg-red-50 text-red-700'
    if(status==='PENDING_CONFIG')return 'border-slate-200 bg-slate-50 text-slate-600'
    return 'border-amber-200 bg-amber-50 text-amber-700'
  }

  return <div>
    <div>
      <p className="text-sm font-semibold text-[#52AD56]">SRI Ecuador</p>
      <h2 className="mt-1 text-2xl font-semibold">Facturación electrónica</h2>
      <p className="mt-1 text-sm text-slate-500">Las facturas se crean automáticamente cuando el predio queda totalmente pagado.</p>
    </div>

    {error&&<div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

    <div className="mt-6 overflow-hidden rounded-2xl border bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3">Fecha</th>
              <th className="px-4 py-3">Factura</th>
              <th className="px-4 py-3">Cliente</th>
              <th className="px-4 py-3">Predio</th>
              <th className="px-4 py-3">Total</th>
              <th className="px-4 py-3">Ambiente</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Acciones</th>
            </tr>
          </thead>
          <tbody>{rows.map(r=><tr key={r.id} className="border-t">
            <td className="px-4 py-3">{r.issue_date}</td>
            <td className="px-4 py-3 font-semibold">{r.document_number||'Pendiente'}</td>
            <td className="px-4 py-3"><p className="font-medium">{r.customer}</p><p className="text-xs text-slate-500">{r.identification}</p></td>
            <td className="px-4 py-3">{r.property}</td>
            <td className="px-4 py-3">$ {Number(r.total||0).toLocaleString('es-EC',{minimumFractionDigits:2})}</td>
            <td className="px-4 py-3">{r.environment==='PRODUCTION'?'Producción':'Pruebas'}</td>
            <td className="px-4 py-3"><span className={'inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold '+badge(r.status)}>{r.status_label}</span></td>
            <td className="px-4 py-3"><div className="flex flex-wrap gap-2">
              {['PENDING_CONFIG','PENDING_XML','XML_GENERATED','ERROR'].includes(r.status)&&<button type="button" disabled={action===r.id} onClick={()=>generateXml(r.id)} className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold text-slate-700 disabled:opacity-50"><RefreshCw className="h-3.5 w-3.5"/>{r.status==='XML_GENERATED'?'Regenerar XML':'Generar XML'}</button>}
              {r.status==='XML_GENERATED'&&<button type="button" disabled={action===r.id} onClick={()=>downloadXml(r.id)} className="inline-flex items-center gap-1.5 rounded-lg bg-[#3A6C32] px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"><Download className="h-3.5 w-3.5"/>Descargar XML</button>}
            </div></td>
          </tr>)}</tbody>
        </table>
        {!loading&&!rows.length&&<div className="py-14 text-center text-slate-400"><FileText className="mx-auto h-10 w-10"/><p className="mt-3">Todavía no existen facturas electrónicas.</p></div>}
        {loading&&<div className="py-12 text-center text-sm text-slate-500">Cargando facturas…</div>}
      </div>
    </div>
  </div>
}
