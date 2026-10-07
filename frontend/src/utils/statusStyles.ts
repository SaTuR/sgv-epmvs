export function propertyStatusBadgeClass(status:string){
  const key=(status||'').toUpperCase()
  switch(key){
    case 'AVAILABLE':
    case 'DISPONIBLE':
      return 'border border-teal-200 bg-teal-50 text-teal-700'
    case 'RESERVED':
    case 'RESERVADO':
      return 'border border-sky-200 bg-sky-50 text-sky-700'
    case 'CONFIRMED':
    case 'COMPRA CONFIRMADA':
      return 'border border-indigo-200 bg-indigo-50 text-indigo-700'
    case 'PAYING':
    case 'EN PROCESO DE PAGO':
      return 'border border-amber-200 bg-amber-50 text-amber-700'
    case 'PAID':
    case 'PAGADO':
      return 'border border-emerald-200 bg-emerald-50 text-emerald-700'
    case 'INVOICED':
    case 'FACTURADO':
      return 'border border-green-300 bg-green-100 text-green-800'
    case 'AWARDED':
    case 'ADJUDICADO':
      return 'border border-violet-200 bg-violet-50 text-violet-700'
    case 'BLOCKED':
    case 'BLOQUEADO':
      return 'border border-slate-300 bg-slate-100 text-slate-700'
    case 'CANCELLED':
    case 'ANULADO':
      return 'border border-red-200 bg-red-50 text-red-700'
    default:
      return 'border border-slate-200 bg-slate-50 text-slate-600'
  }
}

export function propertyStatusBarClass(status:string){
  const key=(status||'').toUpperCase()
  switch(key){
    case 'AVAILABLE':
    case 'DISPONIBLE': return 'bg-teal-500'
    case 'RESERVED':
    case 'RESERVADO': return 'bg-sky-500'
    case 'CONFIRMED':
    case 'COMPRA CONFIRMADA': return 'bg-indigo-500'
    case 'PAYING':
    case 'EN PROCESO DE PAGO': return 'bg-amber-500'
    case 'PAID':
    case 'PAGADO': return 'bg-emerald-500'
    case 'INVOICED':
    case 'FACTURADO': return 'bg-green-700'
    case 'AWARDED':
    case 'ADJUDICADO': return 'bg-violet-500'
    case 'BLOCKED':
    case 'BLOQUEADO': return 'bg-slate-500'
    case 'CANCELLED':
    case 'ANULADO': return 'bg-red-500'
    default: return 'bg-slate-400'
  }
}

export function installmentStatusBadgeClass(status:string){
  switch((status||'').toUpperCase()){
    case 'PAID': return 'border border-emerald-200 bg-emerald-50 text-emerald-700'
    case 'PARTIAL': return 'border border-amber-200 bg-amber-50 text-amber-700'
    case 'OVERDUE': return 'border border-red-200 bg-red-50 text-red-700'
    case 'PENDING':
    default: return 'border border-slate-200 bg-slate-50 text-slate-600'
  }
}

export function binaryStatusBadgeClass(active:boolean){
  return active
    ? 'border border-emerald-200 bg-emerald-50 text-emerald-700'
    : 'border border-slate-200 bg-slate-100 text-slate-500'
}
