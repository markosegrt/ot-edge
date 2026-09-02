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

  if (error) return <p className="text-red-400">Greška: {error}</p>

  return (
    <div className="flex gap-6">
      {/* Leva strana: lista alarama */}
      <div className="w-64 shrink-0">
        <h3 className="text-sm font-semibold text-slate-400 mb-2">Alarmi</h3>
        <ul className="space-y-1">
          {alarms.map((a) => (
            <li key={a.id}>
              <button
                onClick={() => selectAlarm(a.id)}
                className={`w-full text-left px-3 py-2 rounded text-sm ${
                  selected?.alert_id === a.id
                    ? "bg-slate-700"
                    : "bg-slate-800 hover:bg-slate-700"
                }`}
              >
                <div className="flex justify-between items-center">
                  <span>{a.rule_id}</span>
                  <SeverityBadge severity={a.severity} />
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {a.source} → {a.destination}
                </div>
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Desna strana: graf */}
      <div className="flex-1">
        {selected === null ? (
          <p className="text-slate-400">
            Izaberite alarm levo da vidite procesni kontekst.
          </p>
        ) : (
          <div>
            <div className="mb-4">
              <div className="flex items-center gap-3">
                <SeverityBadge severity={selected.severity} />
                <span className="text-lg font-semibold">
                  {selected.rule_id}
                </span>
              </div>
              <p className="text-sm text-slate-400 mt-1">
                {selected.source} → {selected.destination} ·{" "}
                {new Date(selected.alert_timestamp).toLocaleTimeString("sr-RS", {
                  hour12: false,
                })}
              </p>
            </div>
            <CorrelationChart
              telemetry={selected.telemetry}
              alertTimestamp={selected.alert_timestamp}
            />
            <p className="text-xs text-slate-500 mt-2">
              Crvena linija označava trenutak neovlašćenog upisa. Ako se stanje
              pumpe menja u tom trenutku, korelacija podiže ozbiljnost.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}