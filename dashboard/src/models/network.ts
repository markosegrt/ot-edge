export interface NetworkNode {
  ip: string
  device_type: string
  status: string
  name: string | null
  suspicious: boolean
}

export interface NetworkLink {
  source: string
  target: string
  protocol: string
  packet_count: number
}

export interface NetworkData {
  nodes: NetworkNode[]
  links: NetworkLink[]
}