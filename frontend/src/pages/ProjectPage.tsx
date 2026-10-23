import { FormEvent, MouseEvent, useEffect, useMemo, useState } from 'react'
import { FileImage, Layers3, MapPinned, Plus, Save, Trash2, Upload, X } from 'lucide-react'
import { apiBlobUrl, apiFetch } from '../api'
import { binaryStatusBadgeClass } from '../utils/statusStyles'

type Stage={id:string;name:string;description?:string}
type Project={id:string;name:string;description?:string;stages:Stage[]}

const COLORS:Record<string,string>={
  AVAILABLE:'#22c55e',RESERVED:'#eab308',CONFIRMED:'#3b82f6',PAYING:'#f97316',
  PAID:'#15803d',INVOICED:'#9333ea',AWARDED:'#1d4ed8',BLOCKED:'#64748b',CANCELLED:'#dc2626'
}

export default function ProjectPage(){
  const [project,setProject]=useState<Project|null>(null)
  const [stage,setStage]=useState<Stage|null>(null)
  const [maps,setMaps]=useState<any[]>([])
  const [blocks,setBlocks]=useState<any[]>([])
  const [properties,setProperties]=useState<any[]>([])
  const [zones,setZones]=useState<any[]>([])
  const [blockName,setBlockName]=useState('')
  const [mapOpen,setMapOpen]=useState(false)
  const [editMode,setEditMode]=useState(false)
  const [selectedProperty,setSelectedProperty]=useState('')
  const [points,setPoints]=useState<number[][]>([])
  const [error,setError]=useState('')
  const [saving,setSaving]=useState(false)
  const [mapImageUrl,setMapImageUrl]=useState('')
  const [mapImageLoading,setMapImageLoading]=useState(false)

  const activeMap=useMemo(()=>maps.find(m=>m.is_active)||maps[0]||null,[maps])

  async function loadStageData(st:Stage){
    const [m,b,p]=await Promise.all([
      apiFetch('/stages/'+st.id+'/maps'),
      apiFetch('/stages/'+st.id+'/blocks'),
      apiFetch('/properties?stage_id='+st.id)
    ])
    setMaps(m);setBlocks(b);setProperties(p)
    const am=m.find((x:any)=>x.is_active)||m[0]
    setZones(am?await apiFetch('/stage-maps/'+am.id+'/zones'):[])
  }

  async function load(){
    const ps=await apiFetch('/projects')
    const pr=ps[0]||null
    setProject(pr)
    const st=pr?.stages?.[0]||null
    setStage(st)
    if(st)await loadStageData(st)
  }

  useEffect(()=>{load().catch((e:any)=>setError(e.message||'No fue posible cargar el proyecto'))},[])

  async function choose(s:Stage){setStage(s);setMapOpen(false);setEditMode(false);setPoints([]);setSelectedProperty('');await loadStageData(s)}
  async function upload(file:File){if(!stage)return;const f=new FormData();f.append('file',file);await apiFetch('/stages/'+stage.id+'/maps',{method:'POST',body:f});await loadStageData(stage)}
  async function addBlock(e:FormEvent){e.preventDefault();if(!stage||!blockName.trim())return;await apiFetch('/stages/'+stage.id+'/blocks',{method:'POST',body:JSON.stringify({name:blockName})});setBlockName('');setBlocks(await apiFetch('/stages/'+stage.id+'/blocks'))}

  function addPoint(e:MouseEvent<SVGSVGElement>){
    if(!editMode||!selectedProperty)return
    const rect=e.currentTarget.getBoundingClientRect()
    const x=((e.clientX-rect.left)/rect.width)*100
    const y=((e.clientY-rect.top)/rect.height)*100
    setPoints(v=>[...v,[Number(x.toFixed(4)),Number(y.toFixed(4))]])
  }

  async function saveZone(){
    if(!activeMap||!selectedProperty||points.length<3)return
    setSaving(true);setError('')
    try{
      const avg=[points.reduce((s,p)=>s+p[0],0)/points.length,points.reduce((s,p)=>s+p[1],0)/points.length]
      await apiFetch('/stage-maps/'+activeMap.id+'/zones',{method:'PUT',body:JSON.stringify({property_id:selectedProperty,polygon_coordinates:points,label_position:avg})})
      setZones(await apiFetch('/stage-maps/'+activeMap.id+'/zones'))
      setPoints([]);setSelectedProperty('')
    }catch(e:any){setError(e.message||'No fue posible guardar el lote')}
    finally{setSaving(false)}
  }

  async function openCommercialMap(){
    if(!activeMap)return
    setMapOpen(true);setMapImageLoading(true);setError('')
    try{
      if(mapImageUrl) URL.revokeObjectURL(mapImageUrl)
      setMapImageUrl(await apiBlobUrl('/stage-maps/'+activeMap.id+'/file'))
    }catch(e:any){setError(e.message||'No fue posible cargar el plano')}
    finally{setMapImageLoading(false)}
  }

  function closeCommercialMap(){
    setMapOpen(false);setEditMode(false);setPoints([]);setSelectedProperty('')
    if(mapImageUrl){URL.revokeObjectURL(mapImageUrl);setMapImageUrl('')}
  }

  async function deleteZone(propertyId:string){
    if(!activeMap||!confirm('¿Quitar la zona de este lote del plano?'))return
    await apiFetch('/stage-maps/'+activeMap.id+'/zones/'+propertyId,{method:'DELETE'})
    setZones(await apiFetch('/stage-maps/'+activeMap.id+'/zones'))
  }

  const assigned=new Set(zones.map(z=>z.property_id))
  const unassigned=properties.filter(p=>!assigned.has(p.id)||p.id===selectedProperty)

  if(!project)return <p>Cargando proyecto…</p>

  return <div>
    <div><p className="text-sm font-semibold text-[#52AD56]">Proyecto habitacional</p><h2 className="mt-1 text-2xl font-semibold">{project.name}</h2><p className="mt-1 text-sm text-slate-500">{project.description}</p></div>
    {error&&<div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
    <div className="mt-6 flex gap-2">{project.stages.map(s=><button key={s.id} onClick={()=>choose(s)} className={'rounded-xl px-4 py-2.5 text-sm font-semibold '+(stage?.id===s.id?'bg-[#3A6C32] text-white':'border bg-white text-slate-600')}>{s.name}</button>)}</div>

    {stage&&<div className="mt-6 grid gap-5 xl:grid-cols-2">
      <section className="rounded-2xl border bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between"><div><h3 className="font-semibold">Plano de {stage.name}</h3><p className="mt-1 text-sm text-slate-500">JPG, PNG, WEBP o PDF. Se conserva el historial de versiones.</p></div><FileImage className="text-[#3A6C32]"/></div>
        <label className="mt-5 flex cursor-pointer items-center justify-center gap-2 rounded-xl border-2 border-dashed border-emerald-200 bg-emerald-50/50 p-8 text-sm font-medium text-[#3A6C32]"><Upload className="h-5 w-5"/>Subir plano<input type="file" accept=".jpg,.jpeg,.png,.webp,.pdf" className="hidden" onChange={e=>e.target.files?.[0]&&upload(e.target.files[0])}/></label>
        {activeMap&&<button onClick={openCommercialMap} className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white"><MapPinned className="h-4 w-4"/>Abrir mapa comercial</button>}
        <div className="mt-4 space-y-2">{maps.map(m=><div key={m.id} className="flex items-center justify-between rounded-xl border p-3"><div><p className="text-sm font-medium">{m.name}</p><p className="text-xs text-slate-500">Versión {m.version}</p></div><span className={'inline-flex rounded-full px-2 py-1 text-xs font-semibold '+binaryStatusBadgeClass(m.is_active)}>{m.is_active?'Activo':'Anterior'}</span></div>)}</div>
      </section>

      <section className="rounded-2xl border bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2"><Layers3 className="text-[#3A6C32]"/><h3 className="font-semibold">Manzanas</h3></div>
        <form onSubmit={addBlock} className="mt-5 flex gap-2"><input value={blockName} onChange={e=>setBlockName(e.target.value)} className="flex-1 rounded-xl border px-3 py-2.5" placeholder="Ej. Manzana A"/><button className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 text-sm font-semibold text-white"><Plus className="h-4 w-4"/>Agregar</button></form>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">{blocks.map(b=><div key={b.id} className="rounded-xl border p-4"><p className="font-semibold">{b.name}</p><p className="mt-1 text-xs text-slate-500">{stage.name}</p></div>)}</div>
        {!blocks.length&&<p className="mt-8 text-center text-sm text-slate-400">Aún no hay manzanas registradas.</p>}
      </section>
    </div>}

    {mapOpen&&activeMap&&<div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 p-3">
      <div className="flex max-h-[96vh] w-full max-w-[1500px] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b px-5 py-4">
          <div><h3 className="text-lg font-semibold">Mapa comercial · {stage?.name}</h3><p className="text-sm text-slate-500">{zones.length} lotes configurados de {properties.length}</p></div>
          <div className="flex items-center gap-2">
            <button onClick={()=>{setEditMode(!editMode);setPoints([]);setSelectedProperty('')}} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(editMode?'bg-amber-100 text-amber-800':'border')}>{editMode?'Salir de configuración':'Configurar lotes'}</button>
            <button onClick={closeCommercialMap} className="rounded-xl border p-2"><X className="h-5 w-5"/></button>
          </div>
        </div>

        {editMode&&<div className="flex flex-wrap items-end gap-3 border-b bg-slate-50 px-5 py-3">
          <label className="min-w-[280px] flex-1 text-sm">Predio
            <select value={selectedProperty} onChange={e=>{setSelectedProperty(e.target.value);setPoints([])}} className="mt-1 w-full rounded-xl border bg-white px-3 py-2.5">
              <option value="">Seleccione un lote</option>
              {unassigned.map(p=><option key={p.id} value={p.id}>{p.code} · {p.block} · Lote {p.lot_number}</option>)}
            </select>
          </label>
          <div className="text-xs text-slate-500">Haz clic en cada esquina del lote. Mínimo 3 puntos.</div>
          <button disabled={points.length<3||saving} onClick={saveZone} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-40"><Save className="h-4 w-4"/>Guardar lote</button>
          <button disabled={!points.length} onClick={()=>setPoints([])} className="rounded-xl border px-4 py-2.5 text-sm">Limpiar puntos</button>
        </div>}

        <div className="flex-1 overflow-auto bg-slate-900 p-3">
          <div className="relative mx-auto w-fit max-w-full">
            {mapImageLoading&&<div className="flex h-[50vh] min-w-[60vw] items-center justify-center text-sm text-slate-300">Cargando plano…</div>}
            {!mapImageLoading&&mapImageUrl&&<img src={mapImageUrl} alt={activeMap.name} className="block max-h-[75vh] max-w-full select-none object-contain" draggable={false}/>}
            {!mapImageLoading&&!mapImageUrl&&<div className="flex h-[50vh] min-w-[60vw] items-center justify-center text-sm text-red-300">No fue posible mostrar el plano.</div>}
            {mapImageUrl&&<svg onClick={addPoint} className={'absolute inset-0 h-full w-full '+(editMode&&selectedProperty?'cursor-crosshair':'')} viewBox="0 0 100 100" preserveAspectRatio="none">
              {zones.map(z=><g key={z.id}>
                <polygon points={z.polygon_coordinates.map((p:number[])=>p.join(',')).join(' ')} fill={COLORS[z.property.status.code]||'#64748b'} fillOpacity="0.48" stroke={COLORS[z.property.status.code]||'#64748b'} strokeWidth="0.35">
                  <title>{z.property.code} · {z.property.status.name} · $ {Number(z.property.total_price).toFixed(2)}</title>
                </polygon>
                {z.label_position&&<text x={z.label_position[0]} y={z.label_position[1]} fontSize="1.2" textAnchor="middle" dominantBaseline="middle" fill="white" stroke="black" strokeWidth="0.12" paintOrder="stroke">{z.property.lot_number}</text>}
              </g>)}
              {points.length>0&&<><polyline points={points.map(p=>p.join(',')).join(' ')} fill={points.length>=3?'rgba(250,183,28,.25)':'none'} stroke="#FAB71C" strokeWidth="0.45"/>{points.map((p,i)=><circle key={i} cx={p[0]} cy={p[1]} r="0.55" fill="#FAB71C"/>)}</>}
            </svg>}
          </div>
        </div>

        <div className="border-t px-5 py-3">
          <div className="flex flex-wrap gap-3 text-xs">{Object.entries(COLORS).map(([code,color])=><div key={code} className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-sm" style={{backgroundColor:color}}></span><span>{code}</span></div>)}</div>
          {editMode&&zones.length>0&&<div className="mt-3 flex max-h-24 flex-wrap gap-2 overflow-y-auto">{zones.map(z=><button key={z.id} onClick={()=>deleteZone(z.property_id)} className="inline-flex items-center gap-1 rounded-lg border border-red-100 px-2 py-1 text-xs text-red-700"><Trash2 className="h-3 w-3"/>{z.property.code}</button>)}</div>}
        </div>
      </div>
    </div>}
  </div>
}
