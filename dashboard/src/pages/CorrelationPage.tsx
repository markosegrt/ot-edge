import { useEffect, useState } from "react"
import { getAlarms } from "../api_services/alarms"
import { getCorrelationContext } from "../api_services/correlation"
import type { Alert } from "../models/alert"
import type { CorrelationContext } from "../models/correlation"
import { SeverityBadge } from "../components/SeverityBadge"
import { CorrelationChart } from "../components/CorrelationChart"

export function CorrelationPage() {
  const [alarms, setAlarms] = useState<Alert[]>([])
  const [selected, setSelected] = useState<CorrelationContext | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getAlarms()
      .then(setAlarms)
      .catch((e) => setError(e.message))
  }, [])

  function selectAlarm(id: number) {
    getCorrelationContext(id)
      .then(setSelected)
      .catch((e) => setError(e.message))
  }

  if (error) return <p className="text-red-400 text-base">Error: {error}</p>

  return (
    <div className="flex gap-6">
      <div className="w-72 shrink-0">
        <h3 className="text-base font-semibold text-slate-300 mb-3">Alarms</h3>
        <ul className="space-y-2">
          {alarms.map((a) => (
            <li key={a.id}>
              <button
                onClick={() => selectAlarm(a.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-base transition-colors ${
                  selected?.alert_id === a.id
                    ? "bg-slate-700"
                    : "bg-slate-800 hover:bg-slate-700"
                }`}
              >
                <div className="flex justify-between items-center">
                  <span className="font-medium">{a.rule_id}</span>
                  <SeverityBadge severity={a.severity} />
                </div>
                <div className="text-sm text-slate-500 mt-1 font-mono">
                  {a.source} → {a.destination}
                </div>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex-1">
        {selected === null ? (
          <p className="text-slate-400 text-base">
            Select an alarm on the left to view its process context.
          </p>
        ) : (
          <div>
            <div className="mb-4">
              <div className="flex items-center gap-3">
                <SeverityBadge severity={selected.severity} />
                <span className="text-xl font-semibold">{selected.rule_id}</span>
              </div>
              <p className="text-base text-slate-400 mt-1 font-mono">
                {selected.source} → {selected.destination} ·{" "}
                {new Date(selected.alert_timestamp).toLocaleTimeString("en-GB")}
              </p>
            </div>
            <CorrelationChart
              telemetry={selected.telemetry}
              alertTimestamp={selected.alert_timestamp}
            />
            <p className="text-sm text-slate-500 mt-3">
              The red line marks the moment of the unauthorized write. If a pump
              state changes at that moment, correlation raises the severity.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}