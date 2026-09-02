export interface NetworkNode {
  ip: string
  device_type: string
  status: string
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