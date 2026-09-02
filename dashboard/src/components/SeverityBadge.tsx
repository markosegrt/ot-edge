import { severityColor } from "../helpers/severity"

interface Props {
  severity: string
}

export function SeverityBadge({ severity }: Props) {
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${severityColor(
        severity
      )}`}
    >
      {severity}
    </span>
  )
}