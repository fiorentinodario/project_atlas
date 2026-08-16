import { X } from 'lucide-react'
import { useEffect, type ReactNode } from 'react'

type ModalProps = {
  children: ReactNode
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
}

export function Modal({ children, description, isOpen, onClose, title }: ModalProps) {
  useEffect(() => {
    if (!isOpen) return
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', closeOnEscape)
    return () => document.removeEventListener('keydown', closeOnEscape)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-ink-950/40 p-4 backdrop-blur-sm" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section role="dialog" aria-modal="true" aria-labelledby="modal-title" aria-describedby={description ? 'modal-description' : undefined} className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div><h2 id="modal-title" className="text-xl font-bold">{title}</h2>{description && <p id="modal-description" className="mt-1 text-sm leading-6 text-ink-500">{description}</p>}</div>
          <button onClick={onClose} className="rounded-lg p-2 text-ink-500 hover:bg-slate-100" aria-label="Close dialog"><X size={19} /></button>
        </div>
        {children}
      </section>
    </div>
  )
}
