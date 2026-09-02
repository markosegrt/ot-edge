import { useEffect, useState } from "react"
import { getAlarms } from "../api_services/alarms"
import type { Alert } from "../models/alert"
import { SeverityBadge } from "../components/SeverityBadge"

export function AlarmsPage() {
  const [alarms, setAlarms] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getAlarms()
      .then((data) => setAlarms(data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-slate-400">Učitavanje alarma...</p>
  if (error) return <p className="text-red-400">Greška: {error}</p>

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Bezbednosni alarmi</h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-400 border-b border-slate-700">
            <th className="py-2 pr-4">Vreme</th>
            <th className="py-2 pr-4">Pravilo</th>
            <th className="py-2 pr-4">Ozbiljnost</th>
            <th className="py-2 pr-4">Izvor</th>
            <th className="py-2 pr-4">Odredište</th>
            <th className="py-2 pr-4">Povezano</th>
            <th className="py-2 pr-4">Ponavljanja</th>
          </tr>
        </thead>
        <tbody>
          {alarms.map((a) => (
            <tr key={a.id} className="border-b border-slate-800">
              <td className="py-2 pr-4 text-slate-300">
                {new Date(a.timestamp).toLocaleTimeString()}
              </td>
              <td className="py-2 pr-4">{a.rule_id}</td>
              <td className="py-2 pr-4">
                <SeverityBadge severity={a.severity} />
              </td>
              <td className="py-2 pr-4">{a.source}</td>
              <td className="py-2 pr-4">{a.destination}</td>
              <td className="py-2 pr-4">
                {a.correlated ? (
                  <span className="text-green-400">da</span>
                ) : (
                  <span className="text-slate-500">ne</span>
                )}
              </td>
              <td className="py-2 pr-4">{a.occurrence_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}