import { FormEvent, useEffect, useState } from 'react'
import { MapPinned, Pencil, Plus, Trash2 } from 'lucide-react'
import { apiFetch } from '../api'
import { propertyStatusBadgeClass } from '../utils/statusStyles'

export default function PropertiesPage(){
  const [projects,setProjects]=useState<any[]>([])
  const [stageId,setStageId]=useState('')
  const [blocks,setBlocks]=useState<any[]>([])
  const [statuses,setStatuses]=useState<any[]>([])
  const [rows,setRows]=useState<any[]>([])
  const [open,setOpen]=useState(false)
  const [editingId,setEditingId]=useState<string|null>(null)
  const [form,setForm]=useState<any>({block_id:'',status_code:'AVAILABLE',code:'',lot_number:'',cadastral_key:'',area_m2:'',price_per_m2:'',total_price:'',location_reference:'',notes:''})
  async function init(){
    const ps=await apiFetch('/projects');setProjects(ps)
    const sid=ps?.[0]?.stages?.[0]?.id||'';setStageId(sid)
    setStatuses(await apiFetch('/property-statuses'))
    if(sid){setBlocks(await apiFetch('/stages/'+sid+'/blocks'));setRows(await apiFetch('/properties?stage_id='+sid))}
  }
  useEffect(()=>{init()},[])
  async function changeStage(id:string){setStageId(id);setBlocks(await apiFetch('/stages/'+id+'/blocks'));setRows(await apiFetch('/properties?stage_id='+id))}
  function updatePriceField(field:'area_m2'|'price_per_m2',value:string){
    const next={...form,[field]:value}
    const area=Number(field==='area_m2'?value:next.area_m2)
    const price=Number(field==='price_per_m2'?value:next.price_per_m2)
    next.total_price=area>0&&price>=0?(area*price).toFixed(2):''
    setForm(next)
  }
  function resetForm(){
    setEditingId(null)
    setForm({block_id:'',status_code:'AVAILABLE',code:'',lot_number:'',cadastral_key:'',area_m2:'',price_per_m2:'',total_price:'',location_reference:'',notes:''})
  }
  function openCreate(){resetForm();setOpen(true)}
  function openEdit(r:any){
    setEditingId(r.id)
    setForm({
      block_id:r.block_id,
      status_code:r.status.code,
      code:r.code,
      lot_number:r.lot_number,
      cadastral_key:r.cadastral_key||'',
      area_m2:String(r.area_m2 ?? ''),
      price_per_m2:String(r.price_per_m2 ?? ''),
      total_price:String(r.total_price ?? ''),
      location_reference:r.location_reference||'',
      notes:r.notes||'',
    })
    setOpen(true)
  }
  async function save(e:FormEvent){
    e.preventDefault()
    const payload={...form,area_m2:Number(form.area_m2),price_per_m2:Number(form.price_per_m2),total_price:Number(form.total_price)}
    await apiFetch(editingId?'/properties/'+editingId:'/properties',{method:editingId?'PUT':'POST',body:JSON.stringify(payload)})
    setOpen(false)
    resetForm()
    setRows(await apiFetch('/properties?stage_id='+stageId))
  }
  async function removeProperty(r:any){
    if(!confirm('¿Eliminar el predio '+r.code+'? Esta acción solo se permitirá si no tiene reservas ni ventas asociadas.')) return
    try{
      await apiFetch('/properties/'+r.id,{method:'DELETE'})
      setRows(await apiFetch('/properties?stage_id='+stageId))
    }catch(err:any){
      alert(err?.message||'No fue posible eliminar el predio')
    }
  }
  const stages=projects.flatMap((x:any)=>x.stages||[])
  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between"><div><p className="text-sm font-semibold text-[#52AD56]">Catastro comercial</p><h2 className="mt-1 text-2xl font-semibold">Predios</h2><p className="mt-1 text-sm text-slate-500">Lotes del Proyecto San Joaquín.</p></div><button onClick={openCreate} disabled={!blocks.length} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-40"><Plus className="h-4 w-4"/>Nuevo predio</button></div>
    <div className="mt-6 rounded-2xl border bg-white p-4 shadow-sm"><select value={stageId} onChange={e=>changeStage(e.target.value)} className="rounded-xl border px-4 py-2.5">{stages.map((s:any)=><option key={s.id} value={s.id}>{s.name}</option>)}</select></div>
    <div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm"><div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-5 py-3">Código</th><th className="px-5 py-3">Manzana / Lote</th><th className="px-5 py-3">Área</th><th className="px-5 py-3">Precio</th><th className="px-5 py-3">Estado</th><th className="px-5 py-3 text-right">Acciones</th></tr></thead><tbody>{rows.map(r=><tr key={r.id} className="border-t"><td className="px-5 py-4 font-medium">{r.code}</td><td className="px-5 py-4">{r.block} / {r.lot_number}</td><td className="px-5 py-4">{r.area_m2.toFixed(2)} m²</td><td className="px-5 py-4">$ {r.total_price.toLocaleString('es-EC',{minimumFractionDigits:2})}</td><td className="px-5 py-4"><span className={'inline-flex rounded-full px-2.5 py-1 text-xs font-semibold '+propertyStatusBadgeClass(r.status.code)}>{r.status.name}</span></td><td className="px-5 py-4"><div className="flex justify-end gap-2"><button type="button" onClick={()=>openEdit(r)} className="inline-flex items-center gap-1 rounded-lg border px-3 py-2 text-xs font-semibold hover:bg-slate-50"><Pencil className="h-3.5 w-3.5"/>Editar</button><button type="button" onClick={()=>removeProperty(r)} className="inline-flex items-center gap-1 rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-50"><Trash2 className="h-3.5 w-3.5"/>Eliminar</button></div></td></tr>)}</tbody></table>{!rows.length&&<div className="flex flex-col items-center py-14 text-slate-400"><MapPinned className="h-10 w-10"/><p className="mt-3">No hay predios registrados en esta etapa.</p></div>}</div></div>
    {open&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={save} className="w-full max-w-2xl rounded-2xl bg-white p-6"><h3 className="text-xl font-semibold">{editingId?'Editar predio':'Nuevo predio'}</h3><div className="mt-5 grid gap-4 md:grid-cols-2"><label>Manzana<span className="ml-1 text-red-600">*</span><select required value={form.block_id} onChange={e=>setForm({...form,block_id:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{blocks.map(b=><option key={b.id} value={b.id}>{b.name}</option>)}</select></label><label>Estado<span className="ml-1 text-red-600">*</span><select required value={form.status_code} onChange={e=>setForm({...form,status_code:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5">{statuses.map(s=><option key={s.id} value={s.code}>{s.name}</option>)}</select></label>
    {[['code','Código'],['lot_number','Número de lote'],['cadastral_key','Clave catastral']].map(([k,l])=><label key={k}>{l}<span className="ml-1 text-red-600">*</span><input required type="text" value={form[k]} onChange={e=>setForm({...form,[k]:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>)}
    <label>Área m²<span className="ml-1 text-red-600">*</span><input required type="number" min="0.01" step="0.01" value={form.area_m2} onChange={e=>updatePriceField('area_m2',e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
    <label>Precio por m²<span className="ml-1 text-red-600">*</span><input required type="number" min="0" step="0.0001" value={form.price_per_m2} onChange={e=>updatePriceField('price_per_m2',e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
    <label>Precio total<span className="ml-1 text-red-600">*</span><input required readOnly tabIndex={-1} type="number" step="0.01" value={form.total_price} className="mt-1 w-full cursor-not-allowed rounded-xl border bg-slate-50 px-3 py-2.5 font-semibold text-[#3A6C32]"/></label><label className="md:col-span-2">Referencia de ubicación<span className="ml-1 text-red-600">*</span><input required value={form.location_reference} onChange={e=>setForm({...form,location_reference:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label><label className="md:col-span-2">Observaciones<span className="ml-1 text-red-600">*</span><textarea required value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label></div><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>{setOpen(false);resetForm()}} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">{editingId?'Guardar cambios':'Guardar'}</button></div></form></div>}
  </div>
}
