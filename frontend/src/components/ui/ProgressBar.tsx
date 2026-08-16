export function ProgressBar({ value }: { value: number }) {
  const safeValue = Math.min(100, Math.max(0, value))

  return (
    <div
      className="h-2 overflow-hidden rounded-full bg-slate-100"
      role="progressbar"
      aria-label="Project completion"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={safeValue}
    >
      <div className="h-full rounded-full bg-brand-500" style={{ width: `${safeValue}%` }} />
    </div>
  )
}
