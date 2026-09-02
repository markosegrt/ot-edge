export interface Device {
  ip: string
  mac: string | null
  device_type: string
  status: string
  vendor: string | null
  first_seen: string
  last_seen: string
}