import { FormEvent, useEffect, useState } from 'react'
import { Building2, Cloud, DatabaseBackup, FileText, Play, ReceiptText, RefreshCw, Save, Settings2, SlidersHorizontal, Upload } from 'lucide-react'
import { apiFetch } from '../api'

const required=(label:string)=><>{label}<span className="ml-1 text-red-600">*</span></>

const providerRemote=(provider:string)=>{
  if(provider==='ONEDRIVE') return 'onedrive'
  if(provider==='DROPBOX') return 'dropbox'
  return 'gdrive'
}

export default function SettingsPage(){
  const [form,setForm]=useState<any>(null)
  const [saving,setSaving]=useState(false)
  const [backupAction,setBackupAction]=useState('')
  const [sriCertPassword,setSriCertPassword]=useState('')
  const [sriCertAction,setSriCertAction]=useState(false)
  const [message,setMessage]=useState('')
  const [error,setError]=useState('')

  async function refresh(){
    setForm(await apiFetch('/settings'))
  }

  useEffect(()=>{
    refresh().catch((e:any)=>setError(e.message||'No fue posible cargar la configuración'))
  },[])

  useEffect(()=>{
    if(!form || !['QUEUED','RUNNING'].includes(form.backup_last_status)) return
    const timer=setInterval(()=>refresh().catch(()=>{}),3000)
    return ()=>clearInterval(timer)
  },[form?.backup_last_status])

  async function save(e:FormEvent){
    e.preventDefault();setSaving(true);setMessage('');setError('')
    try{
      const data=await apiFetch('/settings',{method:'PUT',body:JSON.stringify(form)})
      setForm(data);setMessage('Configuración guardada correctamente.')
    }catch(e:any){setError(e.message||'No fue posible guardar la configuración')}
    finally{setSaving(false)}
  }

  async function saveSri(){
    setMessage('');setError('')
    try{
      const data=await apiFetch('/settings/sri',{method:'PUT',body:JSON.stringify({
        sri_enabled:Boolean(form.sri_enabled),
        sri_environment:form.sri_environment||'TEST',
        sri_ruc:form.sri_ruc||'',
        sri_business_name:form.sri_business_name||'',
        sri_trade_name:form.sri_trade_name||null,
        sri_accounting_required:Boolean(form.sri_accounting_required),
        sri_special_taxpayer_code:form.sri_special_taxpayer_code||null,
        sri_withholding_agent_code:form.sri_withholding_agent_code||null,
        sri_establishment_code:form.sri_establishment_code||'',
        sri_emission_point:form.sri_emission_point||'',
        sri_invoice_sequence:Number(form.sri_invoice_sequence||1),
      })})
      setForm(data);setMessage('Configuración SRI guardada correctamente.')
    }catch(e:any){setError(e.message||'No fue posible guardar la configuración SRI')}
  }

  async function uploadSriCertificate(file:File){
    setSriCertAction(true);setMessage('');setError('')
    try{
      if(!sriCertPassword) throw new Error('Ingrese la contraseña del certificado.')
      const body=new FormData()
      body.append('password',sriCertPassword)
      body.append('file',file)
      const data=await apiFetch('/settings/sri/certificate',{method:'POST',body})
      setForm(data);setSriCertPassword('')
      setMessage('Certificado electrónico validado y cargado correctamente.')
    }catch(e:any){setError(e.message||'No fue posible cargar el certificado electrónico')}
    finally{setSriCertAction(false)}
  }

  async function saveBackup(){
    setBackupAction('save');setMessage('');setError('')
    try{
      const data=await apiFetch('/settings/backup',{method:'PUT',body:JSON.stringify({
        backup_enabled:Boolean(form.backup_enabled),
        backup_provider:form.backup_provider,
        backup_remote_name:form.backup_remote_name,
        backup_folder:form.backup_folder,
        backup_time:form.backup_time,
        backup_keep_last:2,
      })})
      setForm(data);setMessage('Configuración de respaldos guardada.')
    }catch(e:any){setError(e.message||'No fue posible guardar los respaldos')}
    finally{setBackupAction('')}
  }

  async function uploadConfig(file:File){
    setBackupAction('upload');setMessage('');setError('')
    try{
      const body=new FormData();body.append('file',file)
      await apiFetch('/settings/backup/rclone-config',{method:'POST',body})
      await refresh();setMessage('rclone.conf cargado de forma segura.')
    }catch(e:any){setError(e.message||'No fue posible cargar rclone.conf')}
    finally{setBackupAction('')}
  }

  async function testConnection(){
    setBackupAction('test');setMessage('');setError('')
    try{
      await saveBackup()
      const data=await apiFetch('/settings/backup/test',{method:'POST'})
      setMessage(data.message)
    }catch(e:any){setError(e.message||'No fue posible conectar con la nube')}
    finally{setBackupAction('')}
  }

  async function runBackup(){
    setBackupAction('run');setMessage('');setError('')
    try{
      await saveBackup()
      const data=await apiFetch('/settings/backup/run',{method:'POST'})
      await refresh();setMessage(data.message)
    }catch(e:any){setError(e.message||'No fue posible iniciar el respaldo')}
    finally{setBackupAction('')}
  }

  if(!form)return <div>{error?<p className="rounded-xl bg-red-50 p-4 text-red-700">{error}</p>:<p>Cargando configuración…</p>}</div>

  const input=(key:string,label:string,type='text',requiredField=true)=>(
    <label className="block">
      <span className="text-sm font-medium text-slate-700">{requiredField?required(label):label}</span>
      <input required={requiredField} type={type} value={form[key]??''} onChange={e=>setForm({...form,[key]:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/>
    </label>
  )

  const statusClass=form.backup_last_status==='SUCCESS'
    ?'border-emerald-200 bg-emerald-50 text-emerald-700'
    :form.backup_last_status==='ERROR'
      ?'border-red-200 bg-red-50 text-red-700'
      :['QUEUED','RUNNING'].includes(form.backup_last_status)
        ?'border-amber-200 bg-amber-50 text-amber-700'
        :'border-slate-200 bg-slate-50 text-slate-600'

  const statusLabel:any={
    NEVER:'Sin ejecutar',
    QUEUED:'En cola',
    RUNNING:'Ejecutando',
    SUCCESS:'Correcto',
    ERROR:'Error',
  }

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

      <section className="rounded-2xl border bg-white p-6 shadow-sm xl:col-span-2">
        <div className="flex items-center gap-2"><ReceiptText className="h-5 w-5 text-[#3A6C32]"/><h3 className="font-semibold">Configuración SRI</h3></div>
        <p className="mt-1 text-sm text-slate-500">Datos usados para la facturación electrónica. La factura se crea únicamente cuando el predio queda totalmente pagado.</p>
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <label className="flex items-center gap-3 rounded-xl border p-4 text-sm font-medium">
            <input type="checkbox" checked={Boolean(form.sri_enabled)} onChange={e=>setForm({...form,sri_enabled:e.target.checked})}/>
            Activar facturación electrónica
          </label>
          <label><span className="text-sm font-medium text-slate-700">{required('Ambiente')}</span><select value={form.sri_environment||'TEST'} onChange={e=>setForm({...form,sri_environment:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="TEST">Pruebas</option><option value="PRODUCTION">Producción</option></select></label>
          <label><span className="text-sm font-medium text-slate-700">{required('RUC')}</span><input maxLength={13} value={form.sri_ruc||''} onChange={e=>setForm({...form,sri_ruc:e.target.value.replace(/\D/g,'')})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
          <label className="md:col-span-2"><span className="text-sm font-medium text-slate-700">{required('Razón social')}</span><input value={form.sri_business_name||''} onChange={e=>setForm({...form,sri_business_name:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
          <label><span className="text-sm font-medium text-slate-700">Nombre comercial</span><input value={form.sri_trade_name||''} onChange={e=>setForm({...form,sri_trade_name:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
          <label><span className="text-sm font-medium text-slate-700">{required('Establecimiento')}</span><input maxLength={3} value={form.sri_establishment_code||''} onChange={e=>setForm({...form,sri_establishment_code:e.target.value.replace(/\D/g,'')})} placeholder="001" className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
          <label><span className="text-sm font-medium text-slate-700">{required('Punto de emisión')}</span><input maxLength={3} value={form.sri_emission_point||''} onChange={e=>setForm({...form,sri_emission_point:e.target.value.replace(/\D/g,'')})} placeholder="001" className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
          <label><span className="text-sm font-medium text-slate-700">{required('Próximo secuencial')}</span><input min="1" max="999999999" type="number" value={form.sri_invoice_sequence||1} onChange={e=>setForm({...form,sri_invoice_sequence:Number(e.target.value)})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
          <label className="flex items-center gap-3 rounded-xl border p-4 text-sm font-medium"><input type="checkbox" checked={Boolean(form.sri_accounting_required)} onChange={e=>setForm({...form,sri_accounting_required:e.target.checked})}/>Obligado a llevar contabilidad</label>
          <label><span className="text-sm font-medium text-slate-700">Contribuyente especial</span><input value={form.sri_special_taxpayer_code||''} onChange={e=>setForm({...form,sri_special_taxpayer_code:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
          <label><span className="text-sm font-medium text-slate-700">Agente de retención</span><input value={form.sri_withholding_agent_code||''} onChange={e=>setForm({...form,sri_withholding_agent_code:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
        </div>

        <div className="mt-5 rounded-xl border bg-slate-50 p-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="flex-1">
              <p className="font-medium text-slate-800">Certificado de firma electrónica</p>
              <p className="mt-1 text-sm text-slate-500">Archivo PKCS#12 (.p12/.pfx). La contraseña se almacena cifrada y nunca se muestra nuevamente.</p>
              {form.sri_certificate_configured?<div className="mt-3 grid gap-1 text-xs text-slate-600">
                <p><b>Estado:</b> Configurado</p>
                <p><b>Titular:</b> {form.sri_certificate_subject||'-'}</p>
                <p><b>Emisor:</b> {form.sri_certificate_issuer||'-'}</p>
                <p><b>Serie:</b> {form.sri_certificate_serial||'-'}</p>
                <p><b>Vigencia:</b> {form.sri_certificate_valid_from?new Date(form.sri_certificate_valid_from).toLocaleDateString('es-EC'):'-'} hasta {form.sri_certificate_valid_to?new Date(form.sri_certificate_valid_to).toLocaleDateString('es-EC'):'-'}</p>
              </div>:<p className="mt-3 text-sm font-medium text-amber-700">No hay certificado configurado.</p>}
            </div>
            <div className="w-full lg:max-w-md">
              <label><span className="text-sm font-medium text-slate-700">Contraseña del certificado</span><input type="password" autoComplete="new-password" value={sriCertPassword} onChange={e=>setSriCertPassword(e.target.value)} className="mt-1 w-full rounded-xl border bg-white px-3 py-2.5"/></label>
              <label className="mt-3 inline-flex cursor-pointer items-center gap-2 rounded-xl border bg-white px-4 py-2.5 text-sm font-semibold text-slate-700">
                <Upload className="h-4 w-4"/>{sriCertAction?'Validando…':'Cargar .p12 / .pfx'}
                <input disabled={sriCertAction} type="file" accept=".p12,.pfx,application/x-pkcs12" className="hidden" onChange={e=>e.target.files?.[0]&&uploadSriCertificate(e.target.files[0])}/>
              </label>
            </div>
          </div>
        </div>

        <div className="mt-5 flex justify-end"><button type="button" onClick={saveSri} className="rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white">Guardar configuración SRI</button></div>
      </section>

      <section className="rounded-2xl border bg-white p-6 shadow-sm xl:col-span-2">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div><div className="flex items-center gap-2"><DatabaseBackup className="h-5 w-5 text-[#3A6C32]"/><h3 className="font-semibold">Respaldos automáticos</h3></div><p className="mt-1 text-sm text-slate-500">PostgreSQL → nube. El sistema conserva únicamente los 2 respaldos más recientes.</p></div>
          <span className={'inline-flex rounded-full border px-3 py-1 text-xs font-semibold '+statusClass}>{statusLabel[form.backup_last_status]||form.backup_last_status}</span>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <label className="flex items-center gap-3 rounded-xl border p-4 text-sm font-medium">
            <input type="checkbox" checked={Boolean(form.backup_enabled)} onChange={e=>setForm({...form,backup_enabled:e.target.checked})}/>
            Activar respaldo diario
          </label>

          <label><span className="text-sm font-medium text-slate-700">{required('Proveedor')}</span><select value={form.backup_provider||'GDRIVE'} onChange={e=>setForm({...form,backup_provider:e.target.value,backup_remote_name:providerRemote(e.target.value)})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="GDRIVE">Google Drive</option><option value="ONEDRIVE">Microsoft OneDrive</option><option value="DROPBOX">Dropbox</option></select></label>

          <label><span className="text-sm font-medium text-slate-700">{required('Hora diaria')}</span><input required type="time" value={form.backup_time||'02:00'} onChange={e=>setForm({...form,backup_time:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>

          <label><span className="text-sm font-medium text-slate-700">{required('Nombre del remoto rclone')}</span><input required value={form.backup_remote_name||''} onChange={e=>setForm({...form,backup_remote_name:e.target.value})} placeholder="gdrive" className="mt-1 w-full rounded-xl border px-3 py-2.5"/><span className="mt-1 block text-xs text-slate-500">Debe coincidir con [nombre] dentro de rclone.conf.</span></label>

          <label className="md:col-span-1 xl:col-span-2"><span className="text-sm font-medium text-slate-700">{required('Carpeta en la nube')}</span><input required value={form.backup_folder||'SGV-EPMVS/backups'} onChange={e=>setForm({...form,backup_folder:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          <div className="rounded-xl border bg-slate-50 p-4">
            <div className="flex items-center gap-2"><Cloud className="h-5 w-5 text-[#3A6C32]"/><p className="font-medium">Conexión con la nube</p></div>
            <p className="mt-2 text-sm text-slate-600">{form.backup_configured?'rclone.conf está instalado en el servidor.':'Falta cargar rclone.conf con la autorización del proveedor.'}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border bg-white px-4 py-2.5 text-sm font-semibold text-slate-700"><Upload className="h-4 w-4"/>Subir rclone.conf<input type="file" accept=".conf,text/plain" className="hidden" onChange={e=>e.target.files?.[0]&&uploadConfig(e.target.files[0])}/></label>
              <button type="button" disabled={!!backupAction||!form.backup_configured} onClick={testConnection} className="inline-flex items-center gap-2 rounded-xl border bg-white px-4 py-2.5 text-sm font-semibold disabled:opacity-50"><RefreshCw className="h-4 w-4"/>Probar conexión</button>
            </div>
          </div>

          <div className="rounded-xl border p-4">
            <p className="font-medium">Último respaldo</p>
            <div className="mt-3 space-y-1 text-sm text-slate-600">
              <p><b>Fecha:</b> {form.backup_last_run?new Date(form.backup_last_run).toLocaleString('es-EC'):'Nunca'}</p>
              <p><b>Archivo:</b> {form.backup_last_filename||'-'}</p>
              <p><b>Retención:</b> 2 últimos respaldos</p>
              {form.backup_last_error&&<p className="mt-2 rounded-lg bg-red-50 p-2 text-red-700"><b>Error:</b> {form.backup_last_error}</p>}
            </div>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          <button type="button" disabled={!!backupAction} onClick={saveBackup} className="rounded-xl border px-4 py-2.5 text-sm font-semibold">Guardar respaldo</button>
          <button type="button" disabled={!!backupAction||!form.backup_configured||['QUEUED','RUNNING'].includes(form.backup_last_status)} onClick={runBackup} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"><Play className="h-4 w-4"/>Respaldar ahora</button>
        </div>
      </section>
    </div>
  </form>
}
