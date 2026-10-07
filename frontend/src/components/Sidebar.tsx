import { BarChart3, Building2, FileCheck2, FileText, Home, Landmark, LayoutDashboard, Map, Menu, ReceiptText, Settings, ShieldCheck, Users, WalletCards, X } from 'lucide-react'

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
}

export default function Sidebar({ open, setOpen, active, setActive, permissions }: Props) {
  const can=(permission:string)=>permissions.includes('system.admin')||permissions.includes(permission)
  return <>
    {open && <button aria-label="Cerrar menú" className="fixed inset-0 z-30 bg-black/30 lg:hidden" onClick={()=>setOpen(false)} />}
    <aside className={'fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-emerald-900/10 bg-white transition-transform lg:translate-x-0 '+(open?'translate-x-0':'-translate-x-full')}>
      <div className="flex h-24 items-center gap-3 border-b px-5">
        <img src="/epmvs-logo.webp" alt="EPM Vivienda Samborondón" className="max-h-16 w-auto max-w-[190px] object-contain" />
        <button className="ml-auto lg:hidden" onClick={()=>setOpen(false)}><X /></button>
      </div>
      <div className="px-5 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#52AD56]">SGV EPMVS</p>
        <p className="mt-1 text-sm font-medium text-slate-700">Sistema de Gestión y Venta</p>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-4">
        {items.filter(([, ,permission])=>can(permission)).map(([label,Icon])=>{
          const selected=active===label
          return <button key={label} onClick={()=>{setActive(label);setOpen(false)}} className={'flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition '+(selected?'bg-[#3A6C32] text-white shadow-sm':'text-slate-600 hover:bg-emerald-50 hover:text-[#3A6C32]')}>
            <Icon className="h-5 w-5"/><span>{label}</span>
          </button>
        })}
      </nav>
      <div className="border-t px-5 py-4 text-xs text-slate-400">Proyecto San Joaquín · Etapas 1 y 2</div>
    </aside>
  </>
}

export function MobileMenuButton({onClick}:{onClick:()=>void}) {
  return <button onClick={onClick} className="rounded-lg border bg-white p-2 text-slate-600 lg:hidden" aria-label="Abrir menú"><Menu className="h-5 w-5"/></button>
}
