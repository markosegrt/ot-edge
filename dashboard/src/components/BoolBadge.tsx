export function BoolBadge({ value, label }: { value: boolean; label?: string }) {
  const color = value ? "bg-green-600 text-white" : "bg-slate-600 text-slate-200"
  const text = label ?? (value ? "YES" : "NO")
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-sm font-semibold ${color}`}>
      {text}
    </span>
  )
}