import { FormEvent, useEffect, useState } from 'react'
import { FileImage, Layers3, Plus, Upload } from 'lucide-react'
import { apiFetch } from '../api'
import { binaryStatusBadgeClass } from '../utils/statusStyles'

type Stage={id:string;name:string;description?:string}
type Project={id:string;name:string;description?:string;stages:Stage[]}

export default function ProjectPage(){
  const [project,setProject]=useState<Project|null>(null)
  const [stage,setStage]=useState<Stage|null>(null)
  const [maps,setMaps]=useState<any[]>([])
  const [blocks,setBlocks]=useState<any[]>([])
  const [blockName,setBlockName]=useState('')
  async function load(){
    const ps=await apiFetch('/projects')
    const pr=ps[0]||null
    setProject(pr)
    const st=pr?.stages?.[0]||null
    setStage(st)
    if(st){setMaps(await apiFetch('/stages/'+st.id+'/maps'));setBlocks(await apiFetch('/stages/'+st.id+'/blocks'))}
  }
  useEffect(()=>{load()},[])
  async function choose(s:Stage){setStage(s);setMaps(await apiFetch('/stages/'+s.id+'/maps'));setBlocks(await apiFetch('/stages/'+s.id+'/blocks'))}
  async function upload(file:File){if(!stage)return;const f=new FormData();f.append('file',file);await apiFetch('/stages/'+stage.id+'/maps',{method:'POST',body:f});setMaps(await apiFetch('/stages/'+stage.id+'/maps'))}
  async function addBlock(e:FormEvent){e.preventDefault();if(!stage||!blockName.trim())return;await apiFetch('/stages/'+stage.id+'/blocks',{method:'POST',body:JSON.stringify({name:blockName})});setBlockName('');setBlocks(await apiFetch('/stages/'+stage.id+'/blocks'))}
  if(!project)return <p>Cargando proyecto…</p>
  return <div>
    <div><p className="text-sm font-semibold text-[#52AD56]">Proyecto habitacional</p><h2 className="mt-1 text-2xl font-semibold">{project.name}</h2><p className="mt-1 text-sm text-slate-500">{project.description}</p></div>
    <div className="mt-6 flex gap-2">{project.stages.map(s=><button key={s.id} onClick={()=>choose(s)} className={'rounded-xl px-4 py-2.5 text-sm font-semibold '+(stage?.id===s.id?'bg-[#3A6C32] text-white':'border bg-white text-slate-600')}>{s.name}</button>)}</div>
    {stage&&<div className="mt-6 grid gap-5 xl:grid-cols-2">
      <section className="rounded-2xl border bg-white p-6 shadow-sm"><div className="flex items-center justify-between"><div><h3 className="font-semibold">Plano de {stage.name}</h3><p className="mt-1 text-sm text-slate-500">JPG, PNG, WEBP o PDF. Se conserva el historial de versiones.</p></div><FileImage className="text-[#3A6C32]"/></div>
      <label className="mt-5 flex cursor-pointer items-center justify-center gap-2 rounded-xl border-2 border-dashed border-emerald-200 bg-emerald-50/50 p-8 text-sm font-medium text-[#3A6C32]"><Upload className="h-5 w-5"/>Subir plano<input type="file" accept=".jpg,.jpeg,.png,.webp,.pdf" className="hidden" onChange={e=>e.target.files?.[0]&&upload(e.target.files[0])}/></label>
      <div className="mt-4 space-y-2">{maps.map(m=><div key={m.id} className="flex items-center justify-between rounded-xl border p-3"><div><p className="text-sm font-medium">{m.name}</p><p className="text-xs text-slate-500">Versión {m.version}</p></div><span className={'inline-flex rounded-full px-2 py-1 text-xs font-semibold '+binaryStatusBadgeClass(m.is_active)}>{m.is_active?'Activo':'Anterior'}</span></div>)}</div></section>
      <section className="rounded-2xl border bg-white p-6 shadow-sm"><div className="flex items-center gap-2"><Layers3 className="text-[#3A6C32]"/><h3 className="font-semibold">Manzanas</h3></div>
      <form onSubmit={addBlock} className="mt-5 flex gap-2"><input value={blockName} onChange={e=>setBlockName(e.target.value)} className="flex-1 rounded-xl border px-3 py-2.5" placeholder="Ej. Manzana A"/><button className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 text-sm font-semibold text-white"><Plus className="h-4 w-4"/>Agregar</button></form>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">{blocks.map(b=><div key={b.id} className="rounded-xl border p-4"><p className="font-semibold">{b.name}</p><p className="mt-1 text-xs text-slate-500">{stage.name}</p></div>)}</div>{!blocks.length&&<p className="mt-8 text-center text-sm text-slate-400">Aún no hay manzanas registradas.</p>}</section>
    </div>}
  </div>
}
