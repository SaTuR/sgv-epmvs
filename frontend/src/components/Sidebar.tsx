import { BarChart3, Building2, FileCheck2, FileText, Home, Bell, Landmark, LayoutDashboard, Map, Menu, ReceiptText, Settings, ShieldCheck, Users, WalletCards, X } from 'lucide-react'

const items = [
  ['Dashboard', LayoutDashboard, 'dashboard.view'],
  ['Clientes', Users, 'customers.manage'],
  ['Proyecto San Joaquín', Building2, 'projects.manage'],
  ['Predios', Map, 'properties.manage'],
  ['Reservas y ventas', Home, 'sales.manage'],
  ['Pagos', WalletCards, 'payments.manage'],
  ['Cartera', Landmark, 'receivables.view'],
  ['Certificados', FileCheck2, 'documents.view'],
  ['Facturación electrónica', FileText, 'invoices.view'],
  ['Reportes', BarChart3, 'reports.view'],
  ['Notificaciones', Bell, 'system.admin'],
  ['Usuarios y permisos', ShieldCheck, 'users.manage'],
  ['Configuración', Settings, 'system.admin'],
  ['Auditoría', ReceiptText, 'audit.view'],
] as const

type Props = {
  open:boolean
  setOpen:(v:boolean)=>void
  active:string
  setActive:(v:string)=>void
  permissions:string[]
  collapsed:boolean
  setCollapsed:(v:boolean)=>void
}

export default function Sidebar({ open, setOpen, active, setActive, permissions, collapsed, setCollapsed }: Props) {
  const can=(permission:string)=>permissions.includes('system.admin')||permissions.includes(permission)
  return <>
    {open && <button aria-label="Cerrar menú" className="fixed inset-0 z-30 bg-black/30 lg:hidden" onClick={()=>setOpen(false)} />}
    <aside className={'fixed inset-y-0 left-0 z-40 flex flex-col border-r border-emerald-900/10 bg-white shadow-sm transition-all duration-300 lg:translate-x-0 '+(collapsed?'w-20':'w-72')+' '+(open?'translate-x-0':'-translate-x-full')}>
      <div className={'flex h-24 items-center border-b transition-all duration-300 '+(collapsed?'justify-center px-2':'gap-3 px-5')}>
        <img src="/epmvs-logo.webp" alt="EPM Vivienda Samborondón" className={'object-contain transition-all duration-300 '+(collapsed?'max-h-12 max-w-[58px]':'max-h-16 max-w-[190px]')} />
        <button className="ml-auto lg:hidden" onClick={()=>setOpen(false)}><X /></button>
      </div>
      {!collapsed&&<div className="px-5 py-4 transition-opacity duration-200">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#52AD56]">SGV EPMVS</p>
        <p className="mt-1 text-sm font-medium text-slate-700">Sistema de Gestión y Venta</p>
      </div>}
      <div className={'hidden lg:flex '+(collapsed?'justify-center px-2 py-3':'justify-end px-3 py-3')}>
        <button onClick={()=>setCollapsed(!collapsed)} className="group relative rounded-xl border bg-white p-2 text-slate-500 shadow-sm transition hover:-translate-y-0.5 hover:border-emerald-200 hover:bg-emerald-50 hover:text-[#3A6C32]" aria-label={collapsed?'Expandir menú':'Contraer menú'}>
          <Menu className={'h-5 w-5 transition-transform duration-300 '+(collapsed?'rotate-180':'')}/>
          <span className="pointer-events-none absolute left-full top-1/2 z-50 ml-2 -translate-y-1/2 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-xs text-white opacity-0 shadow-lg transition group-hover:opacity-100">{collapsed?'Expandir':'Contraer'}</span>
        </button>
      </div>
      <nav className={'flex-1 space-y-1 overflow-y-auto pb-4 '+(collapsed?'px-2':'px-3')}>
        {items.filter(([, ,permission])=>can(permission)).map(([label,Icon])=>{
          const selected=active===label
          return <button key={label} title={collapsed?label:undefined} onClick={()=>{setActive(label);setOpen(false)}} className={'group relative flex w-full items-center rounded-xl text-sm font-medium transition-all duration-200 hover:-translate-y-0.5 '+(collapsed?'justify-center px-2 py-3':'gap-3 px-3 py-2.5 text-left')+' '+(selected?'bg-[#3A6C32] text-white shadow-md':'text-slate-600 hover:bg-emerald-50 hover:text-[#3A6C32]')}>
            <Icon className="h-5 w-5 shrink-0"/>
            {!collapsed&&<span className="truncate">{label}</span>}
            {collapsed&&<span className="pointer-events-none absolute left-full top-1/2 z-50 ml-2 -translate-y-1/2 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-xs text-white opacity-0 shadow-lg transition group-hover:opacity-100">{label}</span>}
          </button>
        })}
      </nav>
      {!collapsed&&<div className="border-t px-5 py-4 text-xs text-slate-400">Proyecto San Joaquín · Etapas 1 y 2</div>}
    </aside>
  </>
}

export function MobileMenuButton({onClick}:{onClick:()=>void}) {
  return <button onClick={onClick} className="rounded-lg border bg-white p-2 text-slate-600 lg:hidden" aria-label="Abrir menú"><Menu className="h-5 w-5"/></button>
}
