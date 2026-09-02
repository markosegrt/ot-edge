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

// Tagovi na LEVOJ osi (kontinualne vrednosti)
const LEVEL_TAGS: Record<string, string> = {
  "Rezervoar.Nivo": "#22c55e",
}

// Tagovi na DESNOJ osi (0/1 stanja pumpi)
const STATE_TAGS: Record<string, string> = {
  "Pumpa1.Radi": "#3b82f6",
  "Pumpa2.Radi": "#8b5cf6",
}

export function CorrelationChart({ telemetry, alertTimestamp }: Props) {
  const byTime = new Map<number, Record<string, number>>()

  for (const point of telemetry) {
    const t = new Date(point.timestamp).getTime()
    if (!byTime.has(t)) byTime.set(t, { t })
    byTime.get(t)![point.tag] = point.value
  }

  const data = Array.from(byTime.values()).sort((a, b) => a.t - b.t)
  const alertT = new Date(alertTimestamp).getTime()

  const formatTime = (t: number) =>
    new Date(t).toLocaleTimeString("sr-RS", { hour12: false })

  return (
    <ResponsiveContainer width="100%" height={360}>
      <LineChart data={data} margin={{ top: 10, right: 40, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis
          dataKey="t"
          tickFormatter={formatTime}
          stroke="#94a3b8"
          type="number"
          domain={["dataMin", "dataMax"]}
        />
        {/* Leva osa: nivo rezervoara (0-100) */}
        <YAxis yAxisId="level" stroke="#22c55e" domain={[0, 100]} />
        {/* Desna osa: stanje pumpi (0-1) */}
        <YAxis
          yAxisId="state"
          orientation="right"
          stroke="#94a3b8"
          domain={[0, 1.2]}
          ticks={[0, 1]}
          tickFormatter={(v) => (v === 1 ? "ON" : v === 0 ? "OFF" : "")}
        />
        <Tooltip
          labelFormatter={(t) => formatTime(t as number)}
          contentStyle={{ background: "#1e293b", border: "1px solid #334155" }}
        />
        <Legend />
        <ReferenceLine
          yAxisId="level"
          x={alertT}
          stroke="#ef4444"
          strokeWidth={2}
          label={{ value: "Upis", fill: "#ef4444", position: "top" }}
        />
        {Object.entries(LEVEL_TAGS).map(([tag, color]) => (
          <Line
            key={tag}
            yAxisId="level"
            type="stepAfter"
            dataKey={tag}
            stroke={color}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
        ))}
        {Object.entries(STATE_TAGS).map(([tag, color]) => (
          <Line
            key={tag}
            yAxisId="state"
            type="stepAfter"
            dataKey={tag}
            stroke={color}
            strokeWidth={2}
            dot={false}
            connectNulls
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}