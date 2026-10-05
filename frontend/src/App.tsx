import { Building2, Map, Users, WalletCards, FileBarChart, Landmark } from 'lucide-react'

const cards = [
  ['Predios', 'Etapas 1 y 2', Map],
  ['Clientes', 'Gestión de compradores', Users],
  ['Ventas', 'Reservas y confirmaciones', Building2],
  ['Pagos', 'Recaudación y certificados', WalletCards],
  ['Cartera', 'Cuentas por cobrar', Landmark],
  ['Reportes', 'Predios, pagos y estados', FileBarChart],
]

export default function App() {
  return (
    <main className="min-h-screen bg-slate-100">
      <header className="bg-slate-900 text-white">
        <div className="mx-auto max-w-7xl px-6 py-8">
          <p className="text-sm uppercase tracking-[0.2em] text-slate-300">EPMVS</p>
          <h1 className="mt-2 text-3xl font-semibold">Sistema de Gestión y Venta EPMVS</h1>
          <p className="mt-2 text-slate-300">Proyecto San Joaquín · Etapas 1 y 2</p>
        </div>
      </header>
      <section className="mx-auto max-w-7xl px-6 py-10">
        <div className="mb-8 rounded-2xl bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Panel inicial</h2>
          <p className="mt-2 text-slate-600">Base técnica preparada para clientes, predios, planos, ventas, pagos, cartera y reportes.</p>
        </div>
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {cards.map(([title, description, Icon]: any) => (
            <article key={title} className="rounded-2xl bg-white p-6 shadow-sm">
              <Icon className="h-7 w-7 text-slate-700" />
              <h3 className="mt-4 text-lg font-semibold text-slate-900">{title}</h3>
              <p className="mt-1 text-sm text-slate-500">{description}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}
