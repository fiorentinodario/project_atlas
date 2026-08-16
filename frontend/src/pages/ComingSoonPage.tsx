import { Construction } from 'lucide-react'
import { Card } from '../components/ui/Card'

export function ComingSoonPage({ title }: { title: string }) {
  return (
    <Card className="grid min-h-[65vh] place-items-center p-8 text-center">
      <div>
        <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-brand-50 text-brand-700"><Construction size={24} /></span>
        <h1 className="mt-5 text-2xl font-bold">{title}</h1>
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-ink-500">This area will be introduced in its dedicated milestone. The route is ready and integrated into the responsive application shell.</p>
      </div>
    </Card>
  )
}
