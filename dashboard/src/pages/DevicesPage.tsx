import { useEffect, useState } from "react"
import { getDevices } from "../api_services/devices"
import type { Device } from "../models/device"
import { Table, type Column } from "../components/Table"

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "NEW"
      ? "bg-yellow-500 text-black"
      : status === "KNOWN"
      ? "bg-green-600 text-white"
      : status === "UNAVAILABLE"
      ? "bg-red-600 text-white"
      : "bg-slate-500 text-white"
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-sm font-semibold ${color}`}>
      {status}
    </span>
  )
}

const columns: Column<Device>[] = [
  { header: "IP Address", cell: (d) => <span className="font-mono">{d.ip}</span> },
  { header: "Type", cell: (d) => d.device_type },
  { header: "Status", cell: (d) => <StatusBadge status={d.status} /> },
  {
    header: "First Seen",
    cell: (d) => (
      <span className="text-slate-400">
        {new Date(d.first_seen).toLocaleString("en-GB")}
      </span>
    ),
  },
  {
    header: "Last Seen",
    cell: (d) => (
      <span className="text-slate-400">
        {new Date(d.last_seen).toLocaleString("en-GB")}
      </span>
    ),
  },
]

export function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDevices()
      .then(setDevices)
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <p className="text-red-400 text-base">Error: {error}</p>

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Network Devices</h2>
      <Table
        columns={columns}
        rows={devices}
        rowKey={(d) => d.ip}
        emptyText="No devices discovered"
      />
    </div>
  )
}