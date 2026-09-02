import { Handle, Position } from "@xyflow/react"
import { Cpu, Monitor, Server, HelpCircle } from "lucide-react"

interface DeviceNodeData {
  ip: string
  deviceType: string
  status: string
}

function iconFor(deviceType: string) {
  switch (deviceType) {
    case "PLC":
      return <Cpu size={28} className="text-blue-400" />
    case "HMI":
      return <Monitor size={28} className="text-green-400" />
    case "SCADA":
      return <Server size={28} className="text-purple-400" />
    default:
      return <HelpCircle size={28} className="text-yellow-400" />
  }
}

function statusColor(status: string) {
  switch (status) {
    case "NEW":
      return "bg-yellow-500 text-black"
    case "KNOWN":
      return "bg-green-600 text-white"
    case "UNAVAILABLE":
      return "bg-red-600 text-white"
    default:
      return "bg-slate-500 text-white"
  }
}

export function DeviceNode({ data }: { data: DeviceNodeData }) {
  return (
    <div className="bg-slate-800 border-2 border-slate-600 rounded-xl px-4 py-3 shadow-lg min-w-[160px]">
      {/* Handle-ovi su tacke za koje se kace linije. Nevidljivi ali potrebni. */}
      <Handle type="target" position={Position.Top} className="opacity-0" />
      <Handle type="source" position={Position.Bottom} className="opacity-0" />
      <Handle type="target" position={Position.Left} className="opacity-0" />
      <Handle type="source" position={Position.Right} className="opacity-0" />

      <div className="flex items-center gap-3">
        {iconFor(data.deviceType)}
        <div>
          <div className="font-semibold text-base">{data.deviceType}</div>
          <div className="font-mono text-sm text-slate-400">{data.ip}</div>
        </div>
      </div>
      <div className="mt-2">
        <span
          className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${statusColor(
            data.status
          )}`}
        >
          {data.status}
        </span>
      </div>
    </div>
  )
}