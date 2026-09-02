import { useEffect, useState } from "react"
import { getAlarms } from "../api_services/alarms"
import type { Alert } from "../models/alert"
import { SeverityBadge } from "../components/SeverityBadge"
import { Table, type Column } from "../components/Table"

const columns: Column<Alert>[] = [
  {
    header: "Time",
    cell: (a) => (
      <span className="text-slate-300">
        {new Date(a.timestamp).toLocaleTimeString("en-GB")}
      </span>
    ),
  },
  { header: "Rule", cell: (a) => a.rule_id ?? "-" },
  { header: "Severity", cell: (a) => <SeverityBadge severity={a.severity} /> },
  { header: "Source", cell: (a) => <span className="font-mono">{a.source}</span> },
  {
    header: "Destination",
    cell: (a) => <span className="font-mono">{a.destination}</span>,
  },
  {
    header: "Correlated",
    cell: (a) =>
      a.correlated ? (
        <span className="text-green-400">yes</span>
      ) : (
        <span className="text-slate-500">no</span>
      ),
  },
  { header: "Count", cell: (a) => a.occurrence_count },
]

export function AlarmsPage() {
  const [alarms, setAlarms] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getAlarms()
      .then(setAlarms)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-slate-400 text-base">Loading alarms...</p>
  if (error) return <p className="text-red-400 text-base">Error: {error}</p>

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Security Alarms</h2>
      <Table
        columns={columns}
        rows={alarms}
        rowKey={(a) => a.id}
        emptyText="No alarms recorded"
      />
    </div>
  )
}