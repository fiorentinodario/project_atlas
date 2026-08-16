import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

export function EmptyState({ action, description, icon: Icon, title }: { action?: ReactNode; description: string; icon: LucideIcon; title: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">
      <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-brand-50 text-brand-700"><Icon size={24} /></span>
      <h2 className="mt-5 text-lg font-bold">{title}</h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-ink-500">{description}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
