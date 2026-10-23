import { FormEvent, useEffect, useState } from 'react'
import { Mail, MessageCircle, MessageSquareText, RefreshCw, Send } from 'lucide-react'
import { apiFetch } from '../api'

export default function NotificationsPage(){
  const [cfg,setCfg]=useState<any>(null)
  const [customers,setCustomers]=useState<any[]>([])
  const [logs,setLogs]=useState<any[]>([])
  const [waToken,setWaToken]=useState('')
  const [smsToken,setSmsToken]=useState('')
  const [message,setMessage]=useState('')
  const [error,setError]=useState('')
  const [sendForm,setSendForm]=useState<any>({customer_id:'',channel:'WHATSAPP',event_type:'MANUAL',subject:'',body:''})

  async function refresh(){
    const [c,cs,l]=await Promise.all([apiFetch('/notifications/settings'),apiFetch('/customers'),apiFetch('/notifications/logs')])
    setCfg(c);setCustomers(cs);setLogs(l)
  }
  useEffect(()=>{refresh().catch((e:any)=>setError(e.message||'No fue posible cargar notificaciones'))},[])

  async function saveCfg(e:FormEvent){
    e.preventDefault();setMessage('');setError('')
    try{
      setCfg(await apiFetch('/notifications/settings',{method:'PUT',body:JSON.stringify({
        whatsapp_enabled:Boolean(cfg.whatsapp_enabled),
        whatsapp_phone_number_id:cfg.whatsapp_phone_number_id||null,
        whatsapp_api_version:cfg.whatsapp_api_version||'v24.0',
        sms_enabled:Boolean(cfg.sms_enabled),
        sms_provider:'TWILIO',
        sms_account_sid:cfg.sms_account_sid||null,
        sms_from_number:cfg.sms_from_number||null,
        email_enabled:Boolean(cfg.email_enabled),
      })}))
      setMessage('Configuración de notificaciones guardada.')
    }catch(e:any){setError(e.message||'No fue posible guardar')}
  }

  async function saveSecret(kind:'whatsapp'|'sms'){
    setMessage('');setError('')
    try{
      const value=kind==='whatsapp'?waToken:smsToken
      if(!value) throw new Error('Ingrese la credencial.')
      const body=new FormData();body.append('token',value)
      await apiFetch('/notifications/settings/'+(kind==='whatsapp'?'whatsapp-token':'sms-token'),{method:'POST',body})
      kind==='whatsapp'?setWaToken(''):setSmsToken('')
      await refresh();setMessage('Credencial almacenada cifrada.')
    }catch(e:any){setError(e.message||'No fue posible guardar la credencial')}
  }

  async function send(e:FormEvent){
    e.preventDefault();setMessage('');setError('')
    try{
      await apiFetch('/notifications/send',{method:'POST',body:JSON.stringify({...sendForm,subject:sendForm.subject||null})})
      setMessage('Notificación enviada correctamente.');await refresh()
    }catch(e:any){setError(e.message||'No fue posible enviar')}
  }

  if(!cfg)return <div className="text-slate-500">Cargando centro de notificaciones…</div>

  return <div className="space-y-6">
    <div><p className="text-sm font-semibold text-[#52AD56]">Comunicaciones</p><h2 className="mt-1 text-2xl font-semibold">Centro de Notificaciones</h2><p className="mt-1 text-sm text-slate-500">WhatsApp, SMS y correo electrónico desde un solo módulo.</p></div>
    {message&&<div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div>}
    {error&&<div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

    <form onSubmit={saveCfg} className="grid gap-5 xl:grid-cols-3">
      <section className="rounded-2xl border bg-white p-5 shadow-sm"><div className="flex items-center gap-2"><MessageCircle className="h-5 w-5 text-[#3A6C32]"/><h3 className="font-semibold">WhatsApp</h3></div>
        <label className="mt-4 flex items-center gap-3 rounded-xl border p-3 text-sm"><input type="checkbox" checked={Boolean(cfg.whatsapp_enabled)} onChange={e=>setCfg({...cfg,whatsapp_enabled:e.target.checked})}/>Activar WhatsApp</label>
        <label className="mt-3 block text-sm">Phone Number ID<input value={cfg.whatsapp_phone_number_id||''} onChange={e=>setCfg({...cfg,whatsapp_phone_number_id:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
        <label className="mt-3 block text-sm">API version<input value={cfg.whatsapp_api_version||'v24.0'} onChange={e=>setCfg({...cfg,whatsapp_api_version:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
        <label className="mt-3 block text-sm">Access Token<div className="mt-1 flex gap-2"><input type="password" value={waToken} onChange={e=>setWaToken(e.target.value)} placeholder={cfg.whatsapp_access_token_configured?'Configurado':'Sin configurar'} className="min-w-0 flex-1 rounded-xl border px-3 py-2.5"/><button type="button" onClick={()=>saveSecret('whatsapp')} className="rounded-xl border px-3 font-semibold">Guardar</button></div></label>
      </section>

      <section className="rounded-2xl border bg-white p-5 shadow-sm"><div className="flex items-center gap-2"><MessageSquareText className="h-5 w-5 text-[#3A6C32]"/><h3 className="font-semibold">SMS</h3></div>
        <label className="mt-4 flex items-center gap-3 rounded-xl border p-3 text-sm"><input type="checkbox" checked={Boolean(cfg.sms_enabled)} onChange={e=>setCfg({...cfg,sms_enabled:e.target.checked})}/>Activar SMS</label>
        <label className="mt-3 block text-sm">Proveedor<select value={cfg.sms_provider||'TWILIO'} disabled className="mt-1 w-full rounded-xl border bg-slate-50 px-3 py-2.5"><option>TWILIO</option></select></label>
        <label className="mt-3 block text-sm">Account SID<input value={cfg.sms_account_sid||''} onChange={e=>setCfg({...cfg,sms_account_sid:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
        <label className="mt-3 block text-sm">Número remitente<input value={cfg.sms_from_number||''} onChange={e=>setCfg({...cfg,sms_from_number:e.target.value})} placeholder="+1..." className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
        <label className="mt-3 block text-sm">Auth Token<div className="mt-1 flex gap-2"><input type="password" value={smsToken} onChange={e=>setSmsToken(e.target.value)} placeholder={cfg.sms_auth_token_configured?'Configurado':'Sin configurar'} className="min-w-0 flex-1 rounded-xl border px-3 py-2.5"/><button type="button" onClick={()=>saveSecret('sms')} className="rounded-xl border px-3 font-semibold">Guardar</button></div></label>
      </section>

      <section className="rounded-2xl border bg-white p-5 shadow-sm"><div className="flex items-center gap-2"><Mail className="h-5 w-5 text-[#3A6C32]"/><h3 className="font-semibold">Email</h3></div>
        <label className="mt-4 flex items-center gap-3 rounded-xl border p-3 text-sm"><input type="checkbox" checked={Boolean(cfg.email_enabled)} onChange={e=>setCfg({...cfg,email_enabled:e.target.checked})}/>Activar Email</label>
        <p className="mt-3 text-sm text-slate-500">Usa el servidor SMTP ya configurado en Configuración → Correo de facturación electrónica.</p>
        <p className="mt-3 rounded-xl bg-slate-50 p-3 text-xs text-slate-500">Esto evita guardar dos usuarios/contraseñas SMTP diferentes.</p>
      </section>
      <div className="xl:col-span-3 flex justify-end"><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 text-sm font-semibold text-white">Guardar canales</button></div>
    </form>

    <section className="rounded-2xl border bg-white p-5 shadow-sm">
      <div className="flex items-center gap-2"><Send className="h-5 w-5 text-[#3A6C32]"/><h3 className="font-semibold">Enviar notificación</h3></div>
      <form onSubmit={send} className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="text-sm">Cliente<select required value={sendForm.customer_id} onChange={e=>setSendForm({...sendForm,customer_id:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="">Seleccione</option>{customers.map((c:any)=><option key={c.id} value={c.id}>{c.identification} · {c.full_name}</option>)}</select></label>
        <label className="text-sm">Canal<select value={sendForm.channel} onChange={e=>setSendForm({...sendForm,channel:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"><option value="WHATSAPP">WhatsApp</option><option value="SMS">SMS</option><option value="EMAIL">Email</option></select></label>
        {sendForm.channel==='EMAIL'&&<label className="text-sm md:col-span-2">Asunto<input value={sendForm.subject} onChange={e=>setSendForm({...sendForm,subject:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>}
        <label className="text-sm md:col-span-2">Mensaje<textarea required rows={5} value={sendForm.body} onChange={e=>setSendForm({...sendForm,body:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>
        <div className="md:col-span-2 flex justify-end"><button className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-5 py-2.5 text-sm font-semibold text-white"><Send className="h-4 w-4"/>Enviar</button></div>
      </form>
    </section>

    <section className="overflow-hidden rounded-2xl border bg-white shadow-sm">
      <div className="flex items-center justify-between px-5 py-4"><div><h3 className="font-semibold">Historial</h3><p className="text-sm text-slate-500">Últimos 300 intentos de notificación.</p></div><button onClick={()=>refresh()} className="rounded-xl border p-2"><RefreshCw className="h-4 w-4"/></button></div>
      <div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Fecha</th><th className="px-4 py-3">Canal</th><th className="px-4 py-3">Destino</th><th className="px-4 py-3">Evento</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3">Error</th></tr></thead><tbody>{logs.map((x:any)=><tr key={x.id} className="border-t"><td className="px-4 py-3">{new Date(x.created_at).toLocaleString('es-EC')}</td><td className="px-4 py-3 font-medium">{x.channel}</td><td className="px-4 py-3">{x.recipient||'-'}</td><td className="px-4 py-3">{x.event_type}</td><td className="px-4 py-3"><span className={'rounded-full px-2 py-1 text-xs font-semibold '+(x.status==='SENT'?'bg-emerald-50 text-emerald-700':x.status==='ERROR'?'bg-red-50 text-red-700':'bg-amber-50 text-amber-700')}>{x.status}</span></td><td className="max-w-xs truncate px-4 py-3 text-red-600" title={x.error||''}>{x.error||'-'}</td></tr>)}</tbody></table></div>
      {!logs.length&&<div className="p-8 text-center text-slate-400">Aún no hay notificaciones registradas.</div>}
    </section>
  </div>
}
