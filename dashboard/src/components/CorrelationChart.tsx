import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts"
import type { TelemetryPoint } from "../models/correlation"

interface Props {
  telemetry: TelemetryPoint[]
  alertTimestamp: string
}

// Analogne vrednosti (leva osa, 0-100): nivo rezervoara ILI pritisak u cevi.
const ANALOG_TAGS: Record<string, { color: string; label: string }> = {
  "Rezervoar.Nivo": { color: "#22c55e", label: "Nivo (%)" },
  "Cev.Pritisak": { color: "#f97316", label: "Pritisak (bar)" },
}

// Prekidacke vrednosti (desna osa, ON/OFF): pumpe ILI ventil.
const STATE_TAGS: Record<string, { color: string; label: string }> = {
  "Pumpa1.Radi": { color: "#3b82f6", label: "Pumpa1" },
  "Pumpa2.Radi": { color: "#8b5cf6", label: "Pumpa2" },
  "Ventil.Otvoren": { color: "#eab308", label: "Ventil" },
}

export function CorrelationChart({ telemetry, alertTimestamp }: Props) {
  const byTime = new Map<number, Record<string, number>>()
  const presentTags = new Set<string>()

  for (const point of telemetry) {
    const t = new Date(point.timestamp).getTime()
    if (!byTime.has(t)) byTime.set(t, { t })
    byTime.get(t)![point.tag] = point.value
    presentTags.add(point.tag)
  }

  const data = Array.from(byTime.values()).sort((a, b) => a.t - b.t)
  const alertT = new Date(alertTimestamp).getTime()

  const times = data.map((d) => d.t as number)
  const minT = Math.min(alertT, ...(times.length ? times : [alertT]))
  const maxT = Math.max(alertT, ...(times.length ? times : [alertT]))

  const formatTime = (t: number) =>
    new Date(t).toLocaleTimeString("sr-RS", { hour12: false })

  // Crtamo SAMO tagove koji stvarno postoje u ovoj telemetriji.
  // Tako grafik radi i za PLC1 (nivo/pumpe) i za PLC2 (pritisak/ventil).
  const analogToDraw = Object.entries(ANALOG_TAGS).filter(([tag]) =>
    presentTags.has(tag)
  )
  const stateToDraw = Object.entries(STATE_TAGS).filter(([tag]) =>
    presentTags.has(tag)
  )

  if (data.length === 0) {
    return (
      <p className="text-slate-400 text-base py-8 text-center">
        No process telemetry in the correlation window for this alarm.
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={data} margin={{ top: 30, right: 40, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis
          dataKey="t"
          tickFormatter={formatTime}
          stroke="#94a3b8"
          type="number"
          domain={[minT, maxT]}
        />
        <YAxis yAxisId="analog" stroke="#94a3b8" domain={[0, 100]} />
        <YAxis
          yAxisId="state"
          orientation="right"
          stroke="#94a3b8"
          domain={[-0.1, 1.2]}
          ticks={[0, 1]}
          tickFormatter={(v) => (v === 1 ? "ON" : v === 0 ? "OFF" : "")}
        />
        <Tooltip
          labelFormatter={(t) => formatTime(t as number)}
          contentStyle={{ background: "#1e293b", border: "1px solid #334155" }}
        />
        <Legend />
        <ReferenceLine
          yAxisId="analog"
          x={alertT}
          stroke="#ef4444"
          strokeWidth={2}
          label={{ value: "Upis", fill: "#ef4444", position: "top" }}
        />
        {analogToDraw.map(([tag, cfg]) => (
          <Line
            key={tag}
            yAxisId="analog"
            type="monotone"
            dataKey={tag}
            name={cfg.label}
            stroke={cfg.color}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
        ))}
        {stateToDraw.map(([tag, cfg]) => (
          <Line
            key={tag}
            yAxisId="state"
            type="stepAfter"
            dataKey={tag}
            name={cfg.label}
            stroke={cfg.color}
            strokeWidth={2}
            dot={{ r: 3, fill: cfg.color }}
            connectNulls
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}