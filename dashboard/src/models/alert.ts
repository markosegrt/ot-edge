export interface Alert {
  id: number
  timestamp: string
  rule_id: string | null
  severity: string
  source: string
  destination: string
  protocol: string
  correlated: boolean
  occurrence_count: number
}