import { ShieldCheck, Sparkles } from 'lucide-react'
import type { ReactNode } from 'react'

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="grid min-h-screen bg-white lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden bg-ink-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -right-24 top-16 size-80 rounded-full bg-brand-500/20 blur-3xl" />
        <div className="absolute -bottom-20 left-12 size-64 rounded-full bg-sky-500/10 blur-3xl" />
        <div className="relative flex items-center gap-3">
          <span className="grid size-11 place-items-center rounded-xl bg-white text-ink-950"><Sparkles size={20} /></span>
          <span className="text-xl font-bold">ProjectAtlas</span>
        </div>
        <div className="relative max-w-xl">
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-brand-100">Project intelligence, grounded</p>
          <h1 className="mt-5 text-5xl font-bold leading-[1.08] tracking-tight">Turn scattered project knowledge into clear decisions.</h1>
          <p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">Bring documents, tasks and decisions together. Ask better questions and receive answers backed by your own sources.</p>
        </div>
        <div className="relative flex items-center gap-3 text-sm text-slate-300"><ShieldCheck className="text-brand-500" size={20} /> Your workspace data stays isolated and protected.</div>
      </section>
      <section className="flex min-h-screen items-center justify-center bg-canvas px-5 py-10 sm:px-10">
        <div className="w-full max-w-md">
          <div className="mb-10 flex items-center gap-3 lg:hidden"><span className="grid size-10 place-items-center rounded-xl bg-ink-950 text-white"><Sparkles size={18} /></span><span className="text-lg font-bold">ProjectAtlas</span></div>
          {children}
        </div>
      </section>
    </main>
  )
}
