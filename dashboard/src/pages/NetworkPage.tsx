import { useEffect, useState, useMemo } from "react"
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import { getNetwork } from "../api_services/network"
import type { NetworkData } from "../models/network"
import { DeviceNode } from "../components/DeviceNode"

const nodeTypes = { device: DeviceNode }

const EDGE_IP = "192.168.10.50"

export function NetworkPage() {
  const [data, setData] = useState<NetworkData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getNetwork().then(setData).catch((e) => setError(e.message))
    const interval = setInterval(() => {
      getNetwork().then(setData).catch((e) => setError(e.message))
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const { nodes, edges } = useMemo(() => {
    if (!data) return { nodes: [] as Node[], edges: [] as Edge[] }

    const visibleNodes = data.nodes.filter((n) => n.ip !== EDGE_IP)
    const visibleLinks = data.links.filter(
      (l) => l.source !== EDGE_IP && l.target !== EDGE_IP
    )

    const plcs = visibleNodes.filter((n) => n.device_type === "PLC")
    const others = visibleNodes.filter((n) => n.device_type !== "PLC")

    const centerX = 500
    const centerY = 320
    const radius = 340

    const resultNodes: Node[] = []

    plcs.forEach((plc, i) => {
      const offset = (i - (plcs.length - 1) / 2) * 160
      resultNodes.push({
        id: plc.ip,
        type: "device",
        position: { x: centerX, y: centerY + offset },
        data: { ip: plc.ip, deviceType: plc.device_type, status: plc.status },
      })
    })

    others.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / others.length - Math.PI / 2
      resultNodes.push({
        id: n.ip,
        type: "device",
        position: {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        },
        data: { ip: n.ip, deviceType: n.device_type, status: n.status },
      })
    })

    type LinkAgg = {
      source: string
      target: string
      protocol: string
      packets: number
    }
    const linkMap = new Map<string, LinkAgg>()
    for (const l of visibleLinks) {
      const pair = [l.source, l.target].sort()
      const key = pair[0] + "|" + pair[1] + "|" + l.protocol
      const existing = linkMap.get(key)
      if (existing) {
        existing.packets += l.packet_count
      } else {
        linkMap.set(key, {
          source: l.source,
          target: l.target,
          protocol: l.protocol,
          packets: l.packet_count,
        })
      }
    }

    const resultEdges: Edge[] = Array.from(linkMap.values()).map((l, i) => ({
      id: `e-${i}`,
      source: l.source,
      target: l.target,
      label: l.protocol,
      animated: true,
      style: { stroke: "#64748b", strokeWidth: 2 },
      labelStyle: { fill: "#cbd5e1", fontSize: 13, fontWeight: 600 },
      labelBgStyle: { fill: "#1e293b" },
    }))

    return { nodes: resultNodes, edges: resultEdges }
  }, [data])

  if (error) return <p className="text-red-400 text-base">Error: {error}</p>

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Device Network</h2>
      <div className="h-[600px] rounded-lg border border-slate-700 bg-slate-950">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#334155" gap={20} />
          <Controls />
        </ReactFlow>
      </div>
      <p className="text-sm text-slate-500 mt-3">
        Each node is a discovered device. Lines show which devices communicate
        and over which protocol. Unknown devices are highlighted in yellow.
      </p>
    </div>
  )
}