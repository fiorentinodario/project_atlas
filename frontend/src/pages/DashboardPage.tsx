import { ArrowRight, Clock3, FolderPlus, Send, Sparkles } from 'lucide-react'
import { activities, projects, stats } from '../data/dashboard'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { ProgressBar } from '../components/ui/ProgressBar'
import { useAuth } from '../auth/useAuth'

export function DashboardPage() {
  const { user } = useAuth()
  const firstName = user?.display_name.split(' ')[0] ?? 'there'

  return (
    <div className="space-y-8">
      <section className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <p className="mb-2 text-sm font-semibold text-brand-600">Sunday, August 16</p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Good morning, {firstName}</h1>
          <p className="mt-2 text-ink-500">Here’s what’s happening across your projects.</p>
        </div>
        <Button><FolderPlus size={18} /> New project</Button>
      </section>

      <section aria-label="Project statistics" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(({ change, icon: Icon, label, tone, value }) => (
          <Card key={label} className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-ink-500">{label}</p>
                <p className="mt-2 text-3xl font-bold tracking-tight">{value}</p>
              </div>
              <span className={`grid size-11 place-items-center rounded-xl ${tone}`}><Icon size={20} aria-hidden="true" /></span>
            </div>
            <p className="mt-4 text-xs font-medium text-ink-500">{change}</p>
          </Card>
        ))}
      </section>

      <section className="relative overflow-hidden rounded-3xl bg-ink-950 px-5 py-6 text-white shadow-panel sm:px-7">
        <div className="pointer-events-none absolute -right-16 -top-24 size-64 rounded-full bg-brand-500/20 blur-3xl" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-center">
          <div className="flex flex-1 items-start gap-4">
            <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-white/10 text-brand-100"><Sparkles size={20} /></span>
            <div>
              <h2 className="font-semibold">Ask ProjectAtlas</h2>
              <p className="mt-1 text-sm text-slate-300">Search knowledge across every project workspace.</p>
            </div>
          </div>
          <form className="flex w-full gap-2 rounded-2xl bg-white p-2 lg:max-w-xl" onSubmit={(event) => event.preventDefault()}>
            <label htmlFor="ai-question" className="sr-only">Ask anything about your projects</label>
            <input id="ai-question" className="min-w-0 flex-1 rounded-xl px-3 text-sm text-ink-950 placeholder:text-slate-400" placeholder="Ask anything about your projects..." />
            <Button type="submit" className="size-10 px-0" aria-label="Send question"><Send size={17} /></Button>
          </form>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.45fr_0.85fr]">
        <section aria-labelledby="recent-projects-title">
          <div className="mb-4 flex items-center justify-between">
            <div><h2 id="recent-projects-title" className="text-xl font-bold">Recent projects</h2><p className="mt-1 text-sm text-ink-500">Your most recently active workspaces</p></div>
            <Button variant="ghost">View all <ArrowRight size={16} /></Button>
          </div>
          <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
            {projects.map((project) => (
              <Card key={project.name} className="group p-5 transition hover:-translate-y-0.5 hover:border-brand-500/40">
                <div className="flex items-start justify-between gap-3">
                  <span className="grid size-11 place-items-center rounded-xl bg-brand-50 font-bold text-brand-700">{project.name.slice(0, 2).toUpperCase()}</span>
                  <Badge tone="green">{project.tag}</Badge>
                </div>
                <h3 className="mt-5 font-bold">{project.name}</h3>
                <p className="mt-2 min-h-10 text-sm leading-5 text-ink-500">{project.description}</p>
                <div className="mt-5 flex items-center justify-between text-xs"><span className="font-semibold">{project.progress}% complete</span><span className="text-ink-500">{project.tasks} tasks</span></div>
                <div className="mt-2"><ProgressBar value={project.progress} /></div>
                <div className="mt-5 flex items-center gap-1.5 border-t border-slate-100 pt-4 text-xs text-ink-500"><Clock3 size={14} /> Updated {project.updated}</div>
              </Card>
            ))}
          </div>
        </section>

        <section aria-labelledby="activity-title">
          <div className="mb-4"><h2 id="activity-title" className="text-xl font-bold">Recent activity</h2><p className="mt-1 text-sm text-ink-500">Latest updates from your workspace</p></div>
          <Card className="divide-y divide-slate-100 px-5">
            {activities.map((activity) => (
              <div key={`${activity.text}-${activity.time}`} className="flex gap-3 py-4">
                <span className={`grid size-9 shrink-0 place-items-center rounded-full text-[11px] font-bold ${activity.color}`}>{activity.initials}</span>
                <div className="min-w-0"><p className="text-sm leading-5"><span className="font-semibold">{activity.initials === 'AI' ? 'Atlas AI' : 'You'}</span> {activity.text}</p><p className="mt-1 truncate text-xs text-ink-500">{activity.project} · {activity.time}</p></div>
              </div>
            ))}
          </Card>
        </section>
      </div>
    </div>
  )
}
