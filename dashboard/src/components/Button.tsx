import type { ReactNode } from "react"

type Variant = "primary" | "danger" | "subtle"

interface Props {
  children: ReactNode
  onClick?: () => void
  variant?: Variant
  type?: "button" | "submit"
  disabled?: boolean
}

const STYLES: Record<Variant, string> = {
  primary: "bg-blue-600 hover:bg-blue-500 text-white",
  danger: "bg-red-600 hover:bg-red-500 text-white",
  subtle: "bg-slate-700 hover:bg-slate-600 text-slate-100",
}

export function Button({
  children,
  onClick,
  variant = "primary",
  type = "button",
  disabled = false,
}: Props) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${STYLES[variant]}`}
    >
      {children}
    </button>
  )
}