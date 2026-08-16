import { Bell, Menu, Search } from 'lucide-react'
import { useAuth } from '../../auth/useAuth'

export function Header({ onOpenMenu }: { onOpenMenu: () => void }) {
  const { user } = useAuth()
  const firstName = user?.display_name.split(' ')[0] ?? 'User'
  const initials = user?.display_name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase() ?? 'PA'
  return (
    <header className="sticky top-0 z-20 flex h-20 items-center gap-4 border-b border-slate-200/80 bg-canvas/90 px-4 backdrop-blur-md sm:px-8">
      <button className="rounded-xl p-2 text-ink-700 hover:bg-white lg:hidden" onClick={onOpenMenu} aria-label="Open navigation">
        <Menu size={22} />
      </button>
      <div className="relative hidden max-w-md flex-1 md:block">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-500" size={18} aria-hidden="true" />
        <label htmlFor="global-search" className="sr-only">Search projects and tasks</label>
        <input
          id="global-search"
          type="search"
          placeholder="Search projects and tasks..."
          className="h-11 w-full rounded-xl border border-slate-200 bg-white pl-11 pr-4 text-sm placeholder:text-slate-400"
        />
      </div>
      <div className="ml-auto flex items-center gap-2">
        <button className="relative rounded-xl border border-slate-200 bg-white p-2.5 text-ink-700 hover:bg-slate-50" aria-label="Notifications">
          <Bell size={19} />
          <span className="absolute right-2 top-2 size-2 rounded-full bg-brand-500 ring-2 ring-white" />
        </button>
        <div className="hidden text-right sm:block">
          <p className="text-sm font-semibold">{firstName}</p>
          <p className="text-xs text-ink-500">Workspace owner</p>
        </div>
        <div className="grid size-10 place-items-center rounded-full bg-ink-950 text-xs font-bold text-white">{initials}</div>
      </div>
    </header>
  )
}
