import {
  BookOpen,
  CheckSquare2,
  FolderKanban,
  LayoutDashboard,
  Settings,
  LogOut,
  Sparkles,
  X,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../auth/useAuth'

const navigation = [
  { label: 'Overview', to: '/', icon: LayoutDashboard },
  { label: 'Projects', to: '/projects', icon: FolderKanban },
  { label: 'My tasks', to: '/tasks', icon: CheckSquare2 },
  { label: 'Knowledge', to: '/knowledge', icon: BookOpen },
]

type SidebarProps = {
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user, logout } = useAuth()
  const initials = user?.display_name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase() ?? 'PA'
  return (
    <>
      {isOpen && (
        <button
          aria-label="Close navigation"
          className="fixed inset-0 z-30 bg-ink-950/30 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-slate-200 bg-white px-4 py-5 transition-transform duration-200 lg:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex items-center justify-between px-2">
          <NavLink to="/" className="flex items-center gap-3" onClick={onClose}>
            <span className="grid size-10 place-items-center rounded-xl bg-ink-950 text-white">
              <Sparkles size={19} aria-hidden="true" />
            </span>
            <span className="text-lg font-bold tracking-tight">ProjectAtlas</span>
          </NavLink>
          <button className="rounded-lg p-2 text-ink-500 hover:bg-slate-100 lg:hidden" onClick={onClose} aria-label="Close navigation">
            <X size={20} />
          </button>
        </div>

        <nav className="mt-9 flex flex-1 flex-col gap-1" aria-label="Primary navigation">
          <p className="mb-2 px-3 text-[11px] font-bold uppercase tracking-[0.16em] text-ink-500">Workspace</p>
          {navigation.map(({ icon: Icon, label, to }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  isActive ? 'bg-brand-50 text-brand-700' : 'text-ink-500 hover:bg-slate-50 hover:text-ink-950'
                }`
              }
            >
              <Icon size={19} aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>

        <NavLink
          to="/settings"
          onClick={onClose}
          className="mb-3 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-ink-500 hover:bg-slate-50 hover:text-ink-950"
        >
          <Settings size={19} aria-hidden="true" />
          Settings
        </NavLink>
        <div className="flex items-center gap-3 border-t border-slate-100 px-2 pt-4">
          <div className="grid size-10 shrink-0 place-items-center rounded-full bg-amber-100 text-sm font-bold text-amber-800">{initials}</div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold">{user?.display_name}</p>
            <p className="truncate text-xs text-ink-500">{user?.email}</p>
          </div>
          <button onClick={() => void logout()} className="rounded-lg p-2 text-ink-500 hover:bg-slate-100 hover:text-ink-950" aria-label="Sign out"><LogOut size={18} /></button>
        </div>
      </aside>
    </>
  )
}
