    import { useEffect, useState } from "react"
import { getDevices } from "../api_services/devices"
import type { Device } from "../models/device"

export function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDevices()
      .then(setDevices)
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <p className="text-red-400">Greška: {error}</p>

  function statusBadge(status: string) {
    const color =
      status === "NEW"
        ? "bg-yellow-500 text-black"
        : status === "KNOWN"
        ? "bg-green-600 text-white"
        : status === "UNAVAILABLE"
        ? "bg-red-600 text-white"
        : "bg-slate-500 text-white"
    return (
      <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${color}`}>
        {status}
      </span>
    )
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Uređaji u mreži</h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-400 border-b border-slate-700">
            <th className="py-2 pr-4">IP adresa</th>
            <th className="py-2 pr-4">Tip</th>
            <th className="py-2 pr-4">Status</th>
            <th className="py-2 pr-4">Prvi put viđen</th>
            <th className="py-2 pr-4">Poslednji put viđen</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((d) => (
            <tr key={d.ip} className="border-b border-slate-800">
              <td className="py-2 pr-4 font-mono">{d.ip}</td>
              <td className="py-2 pr-4">{d.device_type}</td>
              <td className="py-2 pr-4">{statusBadge(d.status)}</td>
              <td className="py-2 pr-4 text-slate-400">
                {new Date(d.first_seen).toLocaleString("sr-RS")}
              </td>
              <td className="py-2 pr-4 text-slate-400">
                {new Date(d.last_seen).toLocaleString("sr-RS")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}