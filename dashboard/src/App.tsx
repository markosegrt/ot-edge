import { useState } from "react"
import { NetworkPage } from "./pages/NetworkPage"
import { DevicesPage } from "./pages/DevicesPage"
import { AlarmsPage } from "./pages/AlarmsPage"
import { CorrelationPage } from "./pages/CorrelationPage"

type Tab = "network" | "devices" | "alarms" | "correlation"

const TABS: { id: Tab; label: string }[] = [
  { id: "network", label: "Network" },
  { id: "devices", label: "Devices" },
  { id: "alarms", label: "Alarms" },
  { id: "correlation", label: "Correlation" },
]

function App() {
  const [tab, setTab] = useState<Tab>("network")

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <header className="border-b border-slate-800 px-8 py-5">
        <h1 className="text-2xl font-bold tracking-tight">
          OT Edge <span className="text-blue-400">Dashboard</span>
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Passive OT network monitoring with process correlation
        </p>
      </header>

      <nav className="px-8 border-b border-slate-800">
        <div className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-5 py-3 text-base font-medium border-b-2 -mb-px transition-colors ${
                tab === t.id
                  ? "border-blue-500 text-white"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      <main className="p-8">
        {tab === "network" && <NetworkPage />}
        {tab === "devices" && <DevicesPage />}
        {tab === "alarms" && <AlarmsPage />}
        {tab === "correlation" && <CorrelationPage />}
      </main>
    </div>
  )
}

export default App