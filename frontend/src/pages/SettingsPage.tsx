import { FormEvent, useEffect, useState } from 'react'
import { Building2, FileText, Save, Settings2, SlidersHorizontal } from 'lucide-react'
import { apiFetch } from '../api'

const required=(label:string)=><>{label}<span className="ml-1 text-red-600">*</span></>

export default function SettingsPage(){
  const [form,setForm]=useState<any>(null)
  const [saving,setSaving]=useState(false)
  const [message,setMessage]=useState('')
  const [error,setError]=useState('')

  useEffect(()=>{
    apiFetch('/settings').then(setForm).catch((e:any)=>setError(e.message||'No fue posible cargar la configuración'))
  },[])

  async function save(e:FormEvent){
    e.preventDefault();setSaving(true);setMessage('');setError('')
    try{
      const data=await apiFetch('/settings',{method:'PUT',body:JSON.stringify(form)})
      setForm(data);setMessage('Configuración guardada correctamente.')
    }catch(e:any){setError(e.message||'No fue posible guardar la configuración')}
    finally{setSaving(false)}
  }

  if(!form)return <div>{error?<p className="rounded-xl bg-red-50 p-4 text-red-700">{error}</p>:<p>Cargando configuración…</p>}</div>

  const input=(key:string,label:string,type='text',requiredField=true)=>(
    <label className="block">
      <span className="text-sm font-medium text-slate-700">{requiredField?required(label):label}</span>
      <input required={requiredField} type={type} value={form[key]??''} onChange={e=>setForm({...form,[key]:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/>
    </label>
  )

  return <form onSubmit={save}>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div><p className="text-sm font-semibold text-[#52AD56]">Administración</p><h2 className="mt-1 text-2xl font-semibold">Configuración</h2><p className="mt-1 text-sm text-slate-500">Parámetros institucionales y operativos del SGV EPMVS.</p></div>
      <button disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50"><Save className="h-4 w-4"/>{saving?'Guardando…':'Guardar cambios'}</button>
    </div>

    {message&&<p className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>}
    {error&&<p className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}

    <div className="mt-6 grid gap-5 xl:grid-cols-2">
      <section className="rounded-2xl border bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2"><Building2 className="h-5 w-5 text-[#3A6C32]"/><h3 className="font-semibold">Datos institucionales</h3></div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">{input('institution_name','Nombre de la institución')}</div>
          {input('tax_id','RUC','text',false)}
          {input('phone','Teléfono','text',false)}
          {input('email','Correo institucional','email',false)}
          {input('city','Cantón')}
          {input('province','Provincia')}
          <label className="sm:col-span-2"><span className="text-sm font-medium text-slate-700">Dirección</span><textarea value={form.address??''} onChange={e=>setForm({...form,address:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
        </div>
      </section>

      <section className="rounded-2xl border bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2"><SlidersHorizontal className="h-5 w-5 text-[#3A6C32]"/><h3 className="font-semibold">Parámetros comerciales</h3></div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <label><span className="text-sm font-medium text-slate-700">{required('Vigencia predeterminada de reserva')}</span><div className="mt-1 flex items-center rounded-xl border"><input required min="1" max="365" type="number" value={form.reservation_default_days} onChange={e=>setForm({...form,reservation_default_days:Number(e.target.value)})} className="w-full rounded-xl px-3 py-2.5 outline-none"/><span className="pr-3 text-sm text-slate-500">días</span></div></label>
          {input('currency_symbol','Símbolo de moneda')}
          {input('timezone','Zona horaria')}
        </div>
        <div className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600"><Settings2 className="mb-2 h-5 w-5 text-[#3A6C32]"/>La vigencia configurada se utilizará automáticamente al crear nuevas reservas.</div>
      </section>

      <section className="rounded-2xl border bg-white p-6 shadow-sm xl:col-span-2">
        <div className="flex items-center gap-2"><FileText className="h-5 w-5 text-[#3A6C32]"/><h3 className="font-semibold">Documentos y validación</h3></div>
        <div className="mt-5 grid gap-4">
          {input('public_base_url','URL pública de validación')}
          <label><span className="text-sm font-medium text-slate-700">{required('Texto del pie de documentos')}</span><input required value={form.document_footer??''} onChange={e=>setForm({...form,document_footer:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
          <p className="text-xs text-slate-500">La URL pública se usa para construir el QR de los comprobantes, estados de cuenta y certificados.</p>
        </div>
      </section>
    </div>
  </form>
}
