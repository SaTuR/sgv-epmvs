import { FormEvent, useEffect, useState } from 'react'
import { KeyRound, Pencil, Plus, ShieldCheck, UserCog } from 'lucide-react'
import { apiFetch } from '../api'

export default function SecurityPage(){
  const [users,setUsers]=useState<any[]>([])
  const [roles,setRoles]=useState<any[]>([])
  const [permissions,setPermissions]=useState<any[]>([])
  const [tab,setTab]=useState<'users'|'roles'>('users')
  const [open,setOpen]=useState<'user'|'role'|'password'|null>(null)
  const [editing,setEditing]=useState<any>(null)
  const [error,setError]=useState('')
  const [userForm,setUserForm]=useState<any>({identification:'',first_name:'',last_name:'',email:'',password:'',role_ids:[],active:true})
  const [roleForm,setRoleForm]=useState<any>({description:'',permission_ids:[],active:true})
  const [password,setPassword]=useState('')

  async function load(){
    const [u,r,p]=await Promise.all([apiFetch('/security/users'),apiFetch('/security/roles'),apiFetch('/security/permissions')])
    setUsers(u);setRoles(r);setPermissions(p)
  }
  useEffect(()=>{load()},[])

  function newUser(){setEditing(null);setUserForm({identification:'',first_name:'',last_name:'',email:'',password:'',role_ids:[],active:true});setOpen('user')}
  function editUser(u:any){setEditing(u);setUserForm({identification:u.identification||'',first_name:u.first_name,last_name:u.last_name,email:u.email,role_ids:u.roles.map((r:any)=>r.id),active:u.active});setOpen('user')}
  async function saveUser(e:FormEvent){e.preventDefault();setError('');try{await apiFetch(editing?'/security/users/'+editing.id:'/security/users',{method:editing?'PUT':'POST',body:JSON.stringify(userForm)});setOpen(null);await load()}catch(e:any){setError(e.message)}}
  function editRole(r:any){setEditing(r);setRoleForm({description:r.description||'',permission_ids:r.permissions.map((p:any)=>p.id),active:r.active});setOpen('role')}
  async function saveRole(e:FormEvent){e.preventDefault();setError('');try{await apiFetch('/security/roles/'+editing.id,{method:'PUT',body:JSON.stringify(roleForm)});setOpen(null);await load()}catch(e:any){setError(e.message)}}
  function resetPassword(u:any){setEditing(u);setPassword('');setOpen('password')}
  async function savePassword(e:FormEvent){e.preventDefault();setError('');try{await apiFetch('/security/users/'+editing.id+'/password',{method:'POST',body:JSON.stringify({password})});setOpen(null)}catch(e:any){setError(e.message)}}

  function toggleRole(id:string){setUserForm({...userForm,role_ids:userForm.role_ids.includes(id)?userForm.role_ids.filter((x:string)=>x!==id):[...userForm.role_ids,id]})}
  function togglePermission(id:string){setRoleForm({...roleForm,permission_ids:roleForm.permission_ids.includes(id)?roleForm.permission_ids.filter((x:string)=>x!==id):[...roleForm.permission_ids,id]})}

  return <div>
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between"><div><p className="text-sm font-semibold text-[#52AD56]">Seguridad</p><h2 className="mt-1 text-2xl font-semibold">Usuarios y permisos</h2><p className="mt-1 text-sm text-slate-500">Control de acceso por roles y permisos.</p></div>{tab==='users'&&<button onClick={newUser} className="inline-flex items-center gap-2 rounded-xl bg-[#3A6C32] px-4 py-2.5 text-sm font-semibold text-white"><Plus className="h-4 w-4"/>Nuevo usuario</button>}</div>
    <div className="mt-6 flex gap-2"><button onClick={()=>setTab('users')} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(tab==='users'?'bg-[#3A6C32] text-white':'border bg-white')}>Usuarios</button><button onClick={()=>setTab('roles')} className={'rounded-xl px-4 py-2 text-sm font-semibold '+(tab==='roles'?'bg-[#3A6C32] text-white':'border bg-white')}>Roles y permisos</button></div>

    {tab==='users'?<div className="mt-4 overflow-hidden rounded-2xl border bg-white shadow-sm"><div className="overflow-x-auto"><table className="min-w-full text-sm"><thead className="bg-slate-50 text-left text-slate-500"><tr><th className="px-4 py-3">Usuario</th><th className="px-4 py-3">Correo</th><th className="px-4 py-3">Roles</th><th className="px-4 py-3">Estado</th><th></th></tr></thead><tbody>{users.map(u=><tr key={u.id} className="border-t"><td className="px-4 py-3"><p className="font-medium">{u.full_name}</p><p className="text-xs text-slate-500">{u.identification||'-'}</p></td><td className="px-4 py-3">{u.email}</td><td className="px-4 py-3">{u.roles.map((r:any)=>r.name).join(', ')||'-'}</td><td className="px-4 py-3"><span className={'rounded-full px-2 py-1 text-xs '+(u.active?'bg-emerald-100 text-emerald-700':'bg-slate-100 text-slate-500')}>{u.active?'Activo':'Inactivo'}</span></td><td className="px-4 py-3"><div className="flex justify-end gap-2"><button onClick={()=>editUser(u)} className="rounded-lg border p-2"><Pencil className="h-4 w-4"/></button><button onClick={()=>resetPassword(u)} className="rounded-lg border p-2"><KeyRound className="h-4 w-4"/></button></div></td></tr>)}</tbody></table></div></div>
    :<div className="mt-4 grid gap-4 xl:grid-cols-2">{roles.map(r=><div key={r.id} className="rounded-2xl border bg-white p-5 shadow-sm"><div className="flex items-start justify-between"><div><h3 className="font-semibold">{r.name}</h3><p className="mt-1 text-sm text-slate-500">{r.description||'Sin descripción'}</p></div><button onClick={()=>editRole(r)} className="rounded-lg border p-2"><Pencil className="h-4 w-4"/></button></div><div className="mt-4 flex flex-wrap gap-2">{r.permissions.map((p:any)=><span key={p.id} className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs text-[#3A6C32]">{p.name}</span>)}</div></div>)}</div>}

    {open==='user'&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={saveUser} className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6"><div className="flex items-center gap-2"><UserCog className="text-[#3A6C32]"/><h3 className="text-xl font-semibold">{editing?'Editar usuario':'Nuevo usuario'}</h3></div>{error&&<p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}<div className="mt-5 grid gap-4 sm:grid-cols-2">
      {([['identification','Identificación'],['first_name','Nombres'],['last_name','Apellidos'],['email','Correo']] as const).map(([k,l])=><label key={k}>{l}<input required={k!=='identification'} type={k==='email'?'email':'text'} value={userForm[k]||''} onChange={e=>setUserForm({...userForm,[k]:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>)}
      {!editing&&<label className="sm:col-span-2">Contraseña<input required type="password" minLength={8} value={userForm.password} onChange={e=>setUserForm({...userForm,password:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label>}
      <div className="sm:col-span-2"><p className="text-sm font-medium">Roles</p><div className="mt-2 grid gap-2 sm:grid-cols-2">{roles.filter(r=>r.active).map(r=><label key={r.id} className="flex items-center gap-2 rounded-xl border p-3 text-sm"><input type="checkbox" checked={userForm.role_ids.includes(r.id)} onChange={()=>toggleRole(r.id)}/>{r.name}</label>)}</div></div>
      <label className="sm:col-span-2 flex items-center gap-2 text-sm"><input type="checkbox" checked={userForm.active} onChange={e=>setUserForm({...userForm,active:e.target.checked})}/>Usuario activo</label>
    </div><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(null)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Guardar</button></div></form></div>}

    {open==='role'&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={saveRole} className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6"><div className="flex items-center gap-2"><ShieldCheck className="text-[#3A6C32]"/><h3 className="text-xl font-semibold">{editing?.name}</h3></div>{error&&<p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}<label className="mt-5 block">Descripción<input value={roleForm.description} onChange={e=>setRoleForm({...roleForm,description:e.target.value})} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label><div className="mt-5"><p className="text-sm font-medium">Permisos</p><div className="mt-2 grid gap-2 sm:grid-cols-2">{permissions.map(p=><label key={p.id} className="flex items-start gap-2 rounded-xl border p-3 text-sm"><input disabled={editing?.name==='Administrador'} type="checkbox" checked={roleForm.permission_ids.includes(p.id)} onChange={()=>togglePermission(p.id)}/><span><b>{p.name}</b><br/><span className="text-xs text-slate-500">{p.code}</span></span></label>)}</div></div><label className="mt-4 flex items-center gap-2 text-sm"><input disabled={editing?.name==='Administrador'} type="checkbox" checked={roleForm.active} onChange={e=>setRoleForm({...roleForm,active:e.target.checked})}/>Rol activo</label><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(null)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Guardar permisos</button></div></form></div>}

    {open==='password'&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"><form onSubmit={savePassword} className="w-full max-w-md rounded-2xl bg-white p-6"><h3 className="text-xl font-semibold">Cambiar contraseña</h3><p className="mt-1 text-sm text-slate-500">{editing?.full_name}</p>{error&&<p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}<label className="mt-5 block">Nueva contraseña<input required type="password" minLength={8} value={password} onChange={e=>setPassword(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2.5"/></label><div className="mt-6 flex justify-end gap-2"><button type="button" onClick={()=>setOpen(null)} className="rounded-xl border px-4 py-2.5">Cancelar</button><button className="rounded-xl bg-[#3A6C32] px-5 py-2.5 font-semibold text-white">Actualizar</button></div></form></div>}
  </div>
}
