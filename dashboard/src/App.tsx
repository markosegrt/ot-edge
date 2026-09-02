import { useState } from "react"
import { AlarmsPage } from "./pages/AlarmsPage"
import { CorrelationPage } from "./pages/CorrelationPage"
import { DevicesPage } from "./pages/DevicesPage"

type Tab = "alarms" | "correlation" | "devices"

function App() {
  const [tab, setTab] = useState<Tab>("alarms")

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8">
      <h1 className="text-2xl font-bold mb-6">OT Edge Dashboard</h1>

      <div className="flex gap-2 mb-6 border-b border-slate-700">
        <TabButton active={tab === "alarms"} onClick={() => setTab("alarms")}>
          Alarmi
        </TabButton>
        <TabButton
          active={tab === "correlation"}
          onClick={() => setTab("correlation")}
        >
          Korelacija
        </TabButton>
        <TabButton active={tab === "devices"} onClick={() => setTab("devices")}>
          Uređaji
        </TabButton>
      </div>

      {tab === "alarms" && <AlarmsPage />}
      {tab === "correlation" && <CorrelationPage />}
      {tab === "devices" && <DevicesPage />}
    </div>
  )
}

interface TabButtonProps {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}

function TabButton({ active, onClick, children }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
        active
          ? "border-blue-500 text-white"
          : "border-transparent text-slate-400 hover:text-white"
      }`}
    >
      {children}
    </button>
  )
}

export default App