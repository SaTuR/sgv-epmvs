import { FormEvent, useEffect, useState } from 'react'
import { MapPinned, Plus } from 'lucide-react'
import { apiFetch } from '../api'

export default function PropertiesPage(){
  const [projects,setProjects]=useState<any[]>([])
  const [stageId,setStageId]=useState('')
  const [blocks,setBlocks]=useState<any[]>([])
  const [statuses,setStatuses]=useState<any[]>([])
  const [rows,setRows]=useState<any[]>([])
  const [open,setOpen]=useState(false)
  const [form,setForm]=useState<any>({block_id:'',status_code:'AVAILABLE',code:'',lot_number:'',cadastral_key:'',area_m2:'',price_per_m2:'',total_price:''})
  async function init(){
    const ps=await apiFetch('/projects');setProjects(ps)
    const sid=ps?.[0]?.stages?.[0]?.id||'';setStageId(sid)
    setStatuses(await apiFetch('/property-statuses'))
    if(sid){setBlocks(await apiFetch('/stages/'+sid+'/blocks'));setRows(await apiFetch('/properties?stage_id='+sid))}
  }
  useEffect(()=>{init()},[])
  async function changeStage(id:string){setStageId(id);setBlocks(await apiFetch('/stages/'+id+'/blocks'));setRows(await apiFetch('/properties?stage_id='+id))}
  async function save(e:FormEvent){e.preventDefault();await apiFetch('/properties',{method:'POST',body:JSON.stringify({...form,area_m2:Number(form.area_m2),price_per_m2:form.price_per_m2?Number(form.price_per_m2):null,total_price:Number(form.total_price)})});setOpen(false);setRows(await apiFetch('/properties?stage_id='+stageId))}
  const stages=projects.flatMap((x:any)=>x.stages||[])
  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between"><div><p className="text-sm font-semibold text-[#52AD56]">Catastro comercial</p><h2 className="mt-1 text-2xl font-semibold">Predios</h2><p className="mt-1 text-sm text-slate-500">Lotes del Proyecto San Joaquín.</p></div><button onClick={()=>setOpen(true)} disabled={!blocks.length} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-40"><Plus className="h-4 w-4"/>Nuevo predio</button></div>
    <div className="mt-6 rounded-2xl border bg-white p-4 shadow-sm"><select value={stageId} onChange={e=>changeStage(e.target.value)} className="rounded-xl border px-4 py-2.5">{stages.map((s:any)=><option key={s.id} value={s.id}>{s.name}</option>)}</select></div>
    <div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm"><div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3">Código</th><th className="px-5 py-3">Manzana / Lote</th><th className="px-5 py-3">Área</th><th className="px-5 py-3">Precio</th><th className="px-5 py-3">Estado</th></tr></thead><tbody>{rows.map(r=><tr key={r.id} className="border-t"><td className="px-5 py-4 font-medium">{r.code}</td><td className="px-5 py-4">{r.block} / {r.lot_number}</td><td className="px-5 py-4">{r.area_m2.toFixed(2)} m²</td><td className="px-5 py-4">$ {r.total_price.toLocaleString('es-EC',{minimumFractionDigits:2})}</td><td className="px-5 py-4"><span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-[#3A6C32]">{r.status.name}</span></td></tr>)}</tbody></table>{!rows.length&&<div className="flex flex-col items-center py-14 text-slate-400"><MapPinned className="h-10 w-10"/><p className="mt-3">No hay predios registrados en esta etapa.</p></div>}</div></div>
    {open&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={save} className="w-full max-w-2xl rounded-2xl bg-white p-6"><h3 className="text-xl font-semibold">Nuevo predio</h3><div className="mt-5 grid gap-4 md:grid-cols-2"><label>Manzana<select required value={form.block_id} onChange={e=>setForm({...form,block_id:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{blocks.map(b=><option key={b.id} value={b.id}>{b.name}</option>)}</select></label><label>Estado<select value={form.status_code} onChange={e=>setForm({...form,status_code:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5">{statuses.map(s=><option key={s.id} value={s.code}>{s.name}</option>)}</select></label>
    {[['code','Código'],['lot_number','Número de lote'],['cadastral_key','Clave catastral'],['area_m2','Área m²'],['price_per_m2','Precio por m²'],['total_price','Precio total']].map(([k,l])=><label key={k}>{l}<input required={!['cadastral_key','price_per_m2'].includes(k)} type={['area_m2','price_per_m2','total_price'].includes(k)?'number':'text'} step="0.01" value={form[k]} onChange={e=>setForm({...form,[k]:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>)}</div><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(false)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Guardar</button></div></form></div>}
  </div>
}
